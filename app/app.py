import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import boto3
import pymysql


PORT = int(os.getenv("PORT", "8080"))
LOG_FILE = os.getenv("LOG_FILE", "/var/log/aws-ha-app.log")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
DB_SECRET_ID = os.getenv("DB_SECRET_ID", "aws-ha-app/database")
DB_INSTANCE_IDENTIFIER = os.getenv("DB_INSTANCE_IDENTIFIER", "aws-ha-app-mysql")
INDIA_TZ = timezone(timedelta(hours=5, minutes=30))

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

_db_config = None


def aws_client(service):
    return boto3.client(service, region_name=AWS_REGION)


def get_db_config():
    global _db_config
    if _db_config:
        return _db_config

    secret = aws_client("secretsmanager").get_secret_value(SecretId=DB_SECRET_ID)
    credentials = json.loads(secret["SecretString"])

    instance = aws_client("rds").describe_db_instances(
        DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER
    )["DBInstances"][0]

    _db_config = {
        "host": instance["Endpoint"]["Address"],
        "port": instance["Endpoint"]["Port"],
        "user": credentials["username"],
        "password": credentials["password"],
        "database": credentials["db_name"],
        "cursorclass": pymysql.cursors.DictCursor,
        "connect_timeout": 5,
        "autocommit": True,
    }
    return _db_config


def db_connection():
    conn = pymysql.connect(**get_db_config())
    with conn.cursor() as cursor:
        cursor.execute("SET time_zone = '+05:30'")
    return conn


def india_now():
    return datetime.now(INDIA_TZ).replace(tzinfo=None)


def serialize_todo(todo):
    if not todo:
        return todo

    serialized = dict(todo)
    for field in ("created_at", "updated_at"):
        value = serialized.get(field)
        if isinstance(value, datetime):
            serialized[field] = value.replace(tzinfo=INDIA_TZ).isoformat()
    return serialized


def serialize_todos(todos):
    return [serialize_todo(todo) for todo in todos]


def column_exists(cursor, column_name):
    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'todos'
          AND column_name = %s
        """,
        (column_name,),
    )
    return cursor.fetchone()["count"] > 0


def init_database():
    last_error = None
    for _ in range(30):
        try:
            with db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS todos (
                            id BIGINT AUTO_INCREMENT PRIMARY KEY,
                            title VARCHAR(255) NOT NULL,
                            notes TEXT NULL,
                            completed BOOLEAN NOT NULL DEFAULT FALSE,
                            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP
                        )
                        """
                    )
                    if not column_exists(cursor, "created_at"):
                        cursor.execute(
                            """
                            ALTER TABLE todos
                            ADD COLUMN created_at TIMESTAMP NOT NULL
                                DEFAULT CURRENT_TIMESTAMP
                            """
                        )
                    if not column_exists(cursor, "updated_at"):
                        cursor.execute(
                            """
                            ALTER TABLE todos
                            ADD COLUMN updated_at TIMESTAMP NOT NULL
                                DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                            """
                        )
            logging.info("Database initialized")
            return
        except Exception as exc:  # noqa: BLE001 - startup retry should log any failure
            last_error = exc
            logging.warning("Waiting for database: %s", exc)
            time.sleep(5)
    raise RuntimeError(f"Could not initialize database: {last_error}")


def json_response(handler, status, payload):
    body = json.dumps(payload, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def text_response(handler, status, body, content_type="text/plain; charset=utf-8"):
    encoded = body.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(encoded)))
    handler.end_headers()
    handler.wfile.write(encoded)


def read_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


def list_todos():
    with db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, notes, completed, created_at, updated_at
                FROM todos
                ORDER BY completed ASC, created_at DESC
                """
            )
            return serialize_todos(cursor.fetchall())


def create_todo(payload):
    title = str(payload.get("title", "")).strip()
    notes = str(payload.get("notes", "")).strip()
    if not title:
        raise ValueError("Title is required")

    with db_connection() as conn:
        with conn.cursor() as cursor:
            now = india_now()
            cursor.execute(
                """
                INSERT INTO todos (title, notes, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
                """,
                (title, notes or None, now, now),
            )
            todo_id = cursor.lastrowid
            cursor.execute(
                """
                SELECT id, title, notes, completed, created_at, updated_at
                FROM todos
                WHERE id = %s
                """,
                (todo_id,),
            )
            return serialize_todo(cursor.fetchone())


def update_todo(todo_id, payload):
    fields = []
    values = []

    if "title" in payload:
        title = str(payload["title"]).strip()
        if not title:
            raise ValueError("Title cannot be empty")
        fields.append("title = %s")
        values.append(title)

    if "notes" in payload:
        notes = str(payload["notes"]).strip()
        fields.append("notes = %s")
        values.append(notes or None)

    if "completed" in payload:
        fields.append("completed = %s")
        values.append(bool(payload["completed"]))

    if not fields:
        raise ValueError("No supported fields supplied")

    fields.append("updated_at = %s")
    values.append(india_now())
    values.append(todo_id)
    with db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"UPDATE todos SET {', '.join(fields)} WHERE id = %s",
                values,
            )
            cursor.execute(
                """
                SELECT id, title, notes, completed, created_at, updated_at
                FROM todos
                WHERE id = %s
                """,
                (todo_id,),
            )
            return serialize_todo(cursor.fetchone())


def delete_todo(todo_id):
    with db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM todos WHERE id = %s", (todo_id,))
            return cursor.rowcount > 0


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AWS HA Todo</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #172033;
      --muted: #687085;
      --line: #d9dee8;
      --panel: #ffffff;
      --wash: #f4f7fb;
      --brand: #0f766e;
      --brand-dark: #115e59;
      --accent: #f59e0b;
      --danger: #b91c1c;
      --done: #64748b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        linear-gradient(135deg, rgba(15, 118, 110, 0.10), transparent 34%),
        linear-gradient(225deg, rgba(245, 158, 11, 0.14), transparent 32%),
        var(--wash);
      min-height: 100vh;
    }
    .shell {
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0;
    }
    header {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 20px;
      margin-bottom: 24px;
    }
    h1 {
      margin: 0;
      font-size: clamp(2rem, 4vw, 4.2rem);
      line-height: 0.95;
      letter-spacing: 0;
    }
    .subhead {
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 1rem;
      max-width: 620px;
    }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
      background: #e9f8f5;
      border: 1px solid #bfe8df;
      color: var(--brand-dark);
      padding: 10px 12px;
      border-radius: 8px;
      font-weight: 700;
      font-size: 0.9rem;
    }
    .dot {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: var(--brand);
    }
    main {
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr);
      gap: 20px;
      align-items: start;
    }
    .panel, .todo {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 18px 45px rgba(23, 32, 51, 0.08);
    }
    .panel {
      padding: 20px;
      position: sticky;
      top: 20px;
    }
    h2 {
      margin: 0 0 16px;
      font-size: 1.1rem;
    }
    label {
      display: block;
      font-weight: 700;
      font-size: 0.86rem;
      margin: 14px 0 6px;
    }
    input, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      font: inherit;
      background: #fbfcfe;
      color: var(--ink);
    }
    textarea {
      min-height: 110px;
      resize: vertical;
    }
    button {
      border: 0;
      border-radius: 8px;
      background: var(--brand);
      color: white;
      font: inherit;
      font-weight: 800;
      padding: 12px 14px;
      cursor: pointer;
    }
    button:hover { background: var(--brand-dark); }
    .submit {
      width: 100%;
      margin-top: 16px;
    }
    .toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
      gap: 12px;
    }
    .counts {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .pill {
      background: white;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 10px;
      color: var(--muted);
      font-weight: 700;
      font-size: 0.86rem;
    }
    .list {
      display: grid;
      gap: 12px;
    }
    .todo {
      padding: 16px;
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 14px;
      align-items: start;
    }
    .todo input[type="checkbox"] {
      width: 22px;
      height: 22px;
      margin-top: 3px;
      accent-color: var(--brand);
    }
    .todo h3 {
      margin: 0;
      font-size: 1rem;
    }
    .todo p {
      margin: 7px 0 0;
      color: var(--muted);
      line-height: 1.45;
      white-space: pre-wrap;
    }
    .todo small {
      display: block;
      margin-top: 10px;
      color: var(--done);
    }
    .todo.done h3,
    .todo.done p {
      color: var(--done);
      text-decoration: line-through;
    }
    .delete {
      background: #fff1f2;
      color: var(--danger);
      border: 1px solid #fecdd3;
      padding: 8px 10px;
    }
    .delete:hover {
      background: #ffe4e6;
    }
    .empty {
      border: 1px dashed #b6bfce;
      border-radius: 8px;
      padding: 32px;
      text-align: center;
      color: var(--muted);
      background: rgba(255, 255, 255, 0.62);
    }
    .error {
      display: none;
      margin: 0 0 14px;
      color: var(--danger);
      font-weight: 700;
    }
    @media (max-width: 820px) {
      header, main { display: block; }
      .status { margin-top: 16px; }
      .panel { position: static; margin-bottom: 18px; }
      .toolbar { align-items: flex-start; flex-direction: column; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div>
        <h1>AWS HA Todo</h1>
        <p class="subhead">A resilient todo list served from private EC2 instances and stored in Multi-AZ MySQL RDS.</p>
      </div>
      <div class="status"><span class="dot"></span><span id="systemStatus">Checking RDS</span></div>
    </header>
    <main>
      <section class="panel">
        <h2>Add a task</h2>
        <p class="error" id="formError"></p>
        <form id="todoForm">
          <label for="title">Task</label>
          <input id="title" name="title" maxlength="255" autocomplete="off" placeholder="Ship the next demo" required />
          <label for="notes">Notes</label>
          <textarea id="notes" name="notes" placeholder="Add context, links, or acceptance criteria"></textarea>
          <button class="submit" type="submit">Save task</button>
        </form>
      </section>
      <section>
        <div class="toolbar">
          <h2>Today&apos;s queue</h2>
          <div class="counts">
            <span class="pill" id="totalCount">0 total</span>
            <span class="pill" id="openCount">0 open</span>
            <span class="pill" id="doneCount">0 done</span>
          </div>
        </div>
        <div class="list" id="todoList"></div>
      </section>
    </main>
  </div>
  <script>
    const list = document.querySelector("#todoList");
    const form = document.querySelector("#todoForm");
    const errorBox = document.querySelector("#formError");
    const systemStatus = document.querySelector("#systemStatus");

    async function request(path, options = {}) {
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.error || "Request failed");
      }
      return data;
    }

    function formatDate(value) {
      if (!value) return "";
      return new Date(value).toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    }

    function render(todos) {
      const total = todos.length;
      const done = todos.filter(todo => todo.completed).length;
      document.querySelector("#totalCount").textContent = `${total} total`;
      document.querySelector("#openCount").textContent = `${total - done} open`;
      document.querySelector("#doneCount").textContent = `${done} done`;

      if (todos.length === 0) {
        list.innerHTML = `<div class="empty">No tasks yet. Add the first one and watch it persist in RDS.</div>`;
        return;
      }

      list.innerHTML = todos.map(todo => `
        <article class="todo ${todo.completed ? "done" : ""}">
          <input type="checkbox" data-action="toggle" data-id="${todo.id}" ${todo.completed ? "checked" : ""} aria-label="Toggle ${todo.title}">
          <div>
            <h3>${escapeHtml(todo.title)}</h3>
            ${todo.notes ? `<p>${escapeHtml(todo.notes)}</p>` : ""}
            <small>Added ${formatDate(todo.created_at)}</small>
          </div>
          <button class="delete" data-action="delete" data-id="${todo.id}" aria-label="Delete ${todo.title}">Delete</button>
        </article>
      `).join("");
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    async function loadTodos() {
      const data = await request("/api/todos");
      render(data.todos);
    }

    async function checkSystem() {
      try {
        await request("/api/health");
        systemStatus.textContent = "RDS connected";
      } catch {
        systemStatus.textContent = "RDS unavailable";
      }
    }

    form.addEventListener("submit", async event => {
      event.preventDefault();
      errorBox.style.display = "none";
      const formData = new FormData(form);
      try {
        await request("/api/todos", {
          method: "POST",
          body: JSON.stringify({
            title: formData.get("title"),
            notes: formData.get("notes")
          })
        });
        form.reset();
        await loadTodos();
      } catch (error) {
        errorBox.textContent = error.message;
        errorBox.style.display = "block";
      }
    });

    list.addEventListener("click", async event => {
      const target = event.target;
      const action = target.dataset.action;
      const id = target.dataset.id;
      if (!action || !id) return;

      if (action === "toggle") {
        await request(`/api/todos/${id}`, {
          method: "PATCH",
          body: JSON.stringify({ completed: target.checked })
        });
      }

      if (action === "delete") {
        await request(`/api/todos/${id}`, { method: "DELETE" });
      }

      await loadTodos();
    });

    checkSystem();
    loadTodos().catch(error => {
      list.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
    });
  </script>
</body>
</html>
"""


class TodoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                return text_response(self, 200, INDEX_HTML, "text/html; charset=utf-8")
            if parsed.path == "/health":
                return text_response(self, 200, "OK\n")
            if parsed.path == "/api/health":
                with db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1 AS ok")
                        cursor.fetchone()
                return json_response(self, 200, {"status": "ok", "database": "connected"})
            if parsed.path == "/api/todos":
                return json_response(self, 200, {"todos": list_todos()})
            return json_response(self, 404, {"error": "Not found"})
        except Exception as exc:  # noqa: BLE001 - API should return controlled failures
            logging.exception("GET failed")
            return json_response(self, 500, {"error": str(exc)})

    def do_POST(self):
        try:
            if self.path == "/api/todos":
                return json_response(self, 201, {"todo": create_todo(read_json(self))})
            return json_response(self, 404, {"error": "Not found"})
        except ValueError as exc:
            return json_response(self, 400, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            logging.exception("POST failed")
            return json_response(self, 500, {"error": str(exc)})

    def do_PATCH(self):
        try:
            parts = self.path.strip("/").split("/")
            if len(parts) == 3 and parts[:2] == ["api", "todos"]:
                todo = update_todo(int(parts[2]), read_json(self))
                if not todo:
                    return json_response(self, 404, {"error": "Todo not found"})
                return json_response(self, 200, {"todo": todo})
            return json_response(self, 404, {"error": "Not found"})
        except ValueError as exc:
            return json_response(self, 400, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            logging.exception("PATCH failed")
            return json_response(self, 500, {"error": str(exc)})

    def do_DELETE(self):
        try:
            parts = self.path.strip("/").split("/")
            if len(parts) == 3 and parts[:2] == ["api", "todos"]:
                deleted = delete_todo(int(parts[2]))
                return json_response(self, 200, {"deleted": deleted})
            return json_response(self, 404, {"error": "Not found"})
        except Exception as exc:  # noqa: BLE001
            logging.exception("DELETE failed")
            return json_response(self, 500, {"error": str(exc)})

    def log_message(self, fmt, *args):
        logging.info("%s - %s", self.address_string(), fmt % args)


if __name__ == "__main__":
    init_database()
    logging.info("Starting todo application on port %s at %s", PORT, datetime.now(INDIA_TZ))
    server = ThreadingHTTPServer(("0.0.0.0", PORT), TodoHandler)
    server.serve_forever()
