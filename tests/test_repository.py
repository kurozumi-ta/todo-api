import sqlite3
import pytest
from repository import TodoRepository


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    return TodoRepository(conn)


def test_create_returns_todo(repo):
    todo = repo.create("buy milk")
    assert todo.id == 1
    assert todo.title == "buy milk"
    assert todo.done is False


def test_list_all_empty(repo):
    assert repo.list_all() == []


def test_list_all_returns_created(repo):
    repo.create("a")
    repo.create("b")
    titles = [t.title for t in repo.list_all()]
    assert titles == ["a", "b"]


def test_complete_marks_done(repo):
    todo = repo.create("do laundry")
    updated = repo.complete(todo.id)
    assert updated is not None
    assert updated.done is True


def test_complete_nonexistent_returns_none(repo):
    assert repo.complete(999) is None


def test_delete_existing(repo):
    todo = repo.create("delete me")
    assert repo.delete(todo.id) is True
    assert repo.list_all() == []


def test_delete_nonexistent_returns_false(repo):
    assert repo.delete(999) is False
