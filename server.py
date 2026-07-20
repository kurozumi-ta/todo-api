import json
import re
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer

from repository import TodoRepository

_DB_PATH = "todo.db"
_MAX_BODY = 64 * 1024  # 64 KB — reject oversized payloads before reading
_ROUTE_TODOS = re.compile(r"^/todos/?$")
_ROUTE_TODO = re.compile(r"^/todos/(\d+)/?$")


def _json(handler: BaseHTTPRequestHandler, status: int, body: object):
    data = json.dumps(body, ensure_ascii=False).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _read_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", 0))  # ValueError if malformed
    if length > _MAX_BODY:
        raise ValueError(f"request body exceeds {_MAX_BODY} bytes")
    return json.loads(handler.rfile.read(length)) if length else {}  # ValueError on bad JSON


class TodoHandler(BaseHTTPRequestHandler):
    repo: TodoRepository

    @property
    def _path(self) -> str:
        return self.path.split("?", 1)[0]

    def log_message(self, format, *args):
        pass  # suppress access log noise in tests

    # GET /todos
    def do_GET(self):
        if _ROUTE_TODOS.match(self._path):
            todos = self.repo.list_all()
            _json(self, 200, [{"id": t.id, "title": t.title, "done": t.done, "created_at": t.created_at} for t in todos])
        else:
            _json(self, 404, {"error": "not found"})

    # POST /todos
    def do_POST(self):
        if _ROUTE_TODOS.match(self._path):
            try:
                body = _read_json(self)
            except ValueError as e:
                _json(self, 400, {"error": str(e)})
                return
            title = body.get("title", "").strip()
            if not title:
                _json(self, 400, {"error": "title is required"})
                return
            todo = self.repo.create(title)
            _json(self, 201, {"id": todo.id, "title": todo.title, "done": todo.done, "created_at": todo.created_at})
        else:
            _json(self, 404, {"error": "not found"})

    # PATCH /todos/:id  →  complete
    def do_PATCH(self):
        m = _ROUTE_TODO.match(self._path)
        if m:
            todo = self.repo.complete(int(m.group(1)))
            if todo is None:
                _json(self, 404, {"error": "todo not found"})
            else:
                _json(self, 200, {"id": todo.id, "title": todo.title, "done": todo.done, "created_at": todo.created_at})
        else:
            _json(self, 404, {"error": "not found"})

    # DELETE /todos/:id
    def do_DELETE(self):
        m = _ROUTE_TODO.match(self._path)
        if m:
            deleted = self.repo.delete(int(m.group(1)))
            if not deleted:
                _json(self, 404, {"error": "todo not found"})
            else:
                self.send_response(204)
                self.end_headers()
        else:
            _json(self, 404, {"error": "not found"})


def make_server(host: str = "127.0.0.1", port: int = 8000, db_path: str = _DB_PATH) -> HTTPServer:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    repo = TodoRepository(conn)

    class _Handler(TodoHandler):
        pass

    _Handler.repo = repo
    return HTTPServer((host, port), _Handler)


if __name__ == "__main__":
    server = make_server()
    print("Listening on http://127.0.0.1:8000")
    server.serve_forever()
