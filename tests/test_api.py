from __future__ import annotations

import json
import sqlite3
import threading
import urllib.request
import urllib.error
import pytest
from server import make_server


@pytest.fixture(scope="module")
def base_url():
    server = make_server(host="127.0.0.1", port=18000, db_path=":memory:")
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield "http://127.0.0.1:18000"
    server.shutdown()


def _request(method: str, url: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, json.loads(raw) if raw else {}


# POST /todos
def test_create_todo(base_url):
    status, body = _request("POST", f"{base_url}/todos", {"title": "buy eggs"})
    assert status == 201
    assert body["title"] == "buy eggs"
    assert body["done"] is False


def test_create_todo_missing_title(base_url):
    status, body = _request("POST", f"{base_url}/todos", {})
    assert status == 400
    assert "error" in body


def test_create_todo_oversized_body(base_url):
    data = ("x" * (65 * 1024)).encode()
    req = urllib.request.Request(
        f"{base_url}/todos",
        data=data,
        headers={"Content-Type": "application/json", "Content-Length": str(len(data))},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            status, body = resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        status, body = e.code, json.loads(e.read())
    assert status == 400
    assert "error" in body


def test_create_todo_invalid_json(base_url):
    data = b"not-json"
    req = urllib.request.Request(
        f"{base_url}/todos",
        data=data,
        headers={"Content-Type": "application/json", "Content-Length": str(len(data))},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            status, body = resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        status, body = e.code, json.loads(e.read())
    assert status == 400
    assert "error" in body


# GET /todos
def test_list_todos_with_query_string(base_url):
    status, body = _request("GET", f"{base_url}/todos?done=true")
    assert status == 200
    assert isinstance(body, list)


def test_list_todos(base_url):
    _request("POST", f"{base_url}/todos", {"title": "list item"})
    status, body = _request("GET", f"{base_url}/todos")
    assert status == 200
    assert isinstance(body, list)
    assert any(t["title"] == "list item" for t in body)


# PATCH /todos/:id
def test_complete_todo(base_url):
    _, created = _request("POST", f"{base_url}/todos", {"title": "finish report"})
    todo_id = created["id"]
    status, body = _request("PATCH", f"{base_url}/todos/{todo_id}")
    assert status == 200
    assert body["done"] is True


def test_complete_nonexistent(base_url):
    status, body = _request("PATCH", f"{base_url}/todos/99999")
    assert status == 404


# DELETE /todos/:id
def test_delete_todo(base_url):
    _, created = _request("POST", f"{base_url}/todos", {"title": "to be deleted"})
    todo_id = created["id"]
    status, _ = _request("DELETE", f"{base_url}/todos/{todo_id}")
    assert status == 204


def test_delete_nonexistent(base_url):
    status, body = _request("DELETE", f"{base_url}/todos/99999")
    assert status == 404
