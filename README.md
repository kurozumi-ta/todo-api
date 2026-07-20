# Todo API

Python 標準ライブラリと SQLite だけで動く、シンプルな ToDo 管理 REST API。

## 要件

- Python 3.9 以上
- 外部ライブラリ不要（テスト実行には pytest が必要）

## 起動方法

```bash
python3 server.py
# Listening on http://127.0.0.1:8000
```

データは `todo.db`（SQLite）に自動作成されます。起動時にテーブルが存在しない場合は自動マイグレーションします。

---

## エンドポイント一覧

| メソッド | パス | 説明 | 成功レスポンス |
|--------|------|------|--------------|
| `POST` | `/todos` | ToDo を作成 | `201 Created` |
| `GET` | `/todos` | ToDo 一覧を取得 | `200 OK` |
| `PATCH` | `/todos/:id` | ToDo を完了にする | `200 OK` |
| `DELETE` | `/todos/:id` | ToDo を削除する | `204 No Content` |

### ToDo オブジェクト

```json
{
  "id": 1,
  "title": "牛乳を買う",
  "done": false,
  "created_at": "2026-07-20 10:00:00"
}
```

---

## curl リクエスト例

### ToDo を作成する

```bash
curl -X POST http://127.0.0.1:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "牛乳を買う"}'
```

```json
{"id": 1, "title": "牛乳を買う", "done": false, "created_at": "2026-07-20 10:00:00"}
```

### ToDo 一覧を取得する

```bash
curl http://127.0.0.1:8000/todos
```

```json
[
  {"id": 1, "title": "牛乳を買う", "done": false, "created_at": "2026-07-20 10:00:00"},
  {"id": 2, "title": "洗濯をする", "done": true,  "created_at": "2026-07-20 10:05:00"}
]
```

### ToDo を完了にする

```bash
curl -X PATCH http://127.0.0.1:8000/todos/1
```

```json
{"id": 1, "title": "牛乳を買う", "done": true, "created_at": "2026-07-20 10:00:00"}
```

### ToDo を削除する

```bash
curl -X DELETE http://127.0.0.1:8000/todos/1
# → 204 No Content（レスポンスボディなし）
```

---

## エラーレスポンス

すべてのエラーは JSON で返ります。

| ステータス | 発生条件 |
|----------|---------|
| `400 Bad Request` | `title` が空、リクエストボディが不正な JSON、ボディが 64 KB 超 |
| `404 Not Found` | 存在しない ID へのアクセス、または未定義のパス |

```json
{"error": "title is required"}
```

---

## テストの実行

pytest をインストールしてテストを実行します。

```bash
pip3 install pytest
python3 -m pytest tests/ -v
```

テストは SQLite の `:memory:` データベースを使用するため、`todo.db` に影響しません。

```
tests/test_api.py::test_create_todo                    PASSED
tests/test_api.py::test_create_todo_missing_title      PASSED
tests/test_api.py::test_create_todo_oversized_body     PASSED
tests/test_api.py::test_create_todo_invalid_json       PASSED
tests/test_api.py::test_list_todos_with_query_string   PASSED
tests/test_api.py::test_list_todos                     PASSED
tests/test_api.py::test_complete_todo                  PASSED
tests/test_api.py::test_complete_nonexistent           PASSED
tests/test_api.py::test_delete_todo                    PASSED
tests/test_api.py::test_delete_nonexistent             PASSED
tests/test_repository.py::test_create_returns_todo     PASSED
tests/test_repository.py::test_list_all_empty          PASSED
tests/test_repository.py::test_list_all_returns_created PASSED
tests/test_repository.py::test_complete_marks_done     PASSED
tests/test_repository.py::test_complete_nonexistent_returns_none PASSED
tests/test_repository.py::test_delete_existing         PASSED
tests/test_repository.py::test_delete_nonexistent_returns_false PASSED
```

### テスト構成

| ファイル | 対象 | 件数 |
|---------|------|-----|
| `tests/test_repository.py` | `TodoRepository`（DB 操作の単体テスト） | 7 |
| `tests/test_api.py` | HTTP エンドポイント（統合テスト） | 10 |

---

## ファイル構成

```
todo-api/
├── server.py          # HTTP サーバー・ルーティング
├── repository.py      # SQLite アクセス層
├── todo.db            # データファイル（自動生成・git 管理外）
└── tests/
    ├── test_api.py
    └── test_repository.py
```
