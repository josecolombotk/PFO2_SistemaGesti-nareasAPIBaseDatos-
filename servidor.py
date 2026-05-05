import os
import secrets
import sqlite3
import html

from flask import Flask, Response, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash


def create_app() -> Flask:
    app = Flask(__name__)

    os.makedirs(app.instance_path, exist_ok=True)
    app.config["DATABASE"] = os.path.join(app.instance_path, "gestion_tareas.sqlite3")
    app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    def get_db() -> sqlite3.Connection:
        db: sqlite3.Connection | None = getattr(g, "db", None)
        if db is None:
            db = sqlite3.connect(app.config["DATABASE"])
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys = ON")
            g.db = db
        return db

    def init_db() -> None:
        db = get_db()
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                titulo TEXT NOT NULL,
                creada_en TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
            )
            """
        )
        db.commit()

    @app.teardown_appcontext
    def close_db(_exc: Exception | None) -> None:
        db: sqlite3.Connection | None = getattr(g, "db", None)
        if db is not None:
            db.close()

    def current_user() -> dict | None:
        user_id = session.get("user_id")
        usuario = session.get("usuario")
        if not user_id or not usuario:
            return None
        return {"id": user_id, "usuario": usuario}

    def require_login() -> tuple[dict | None, Response | None]:
        user = current_user()
        if user is None:
            return None, Response(
                "<h1>No autorizado</h1><p>Inicia sesión para ver tus tareas.</p>",
                status=401,
                mimetype="text/html",
            )
        return user, None

    def require_login_json() -> tuple[dict | None, tuple[Response, int] | None]:
        user = current_user()
        if user is None:
            return None, (jsonify({"error": "No autorizado. Inicia sesión."}), 401)
        return user, None

    @app.post("/registro")
    def registro():
        data = request.get_json(silent=True) or {}
        usuario = data.get("usuario")
        password = data.get("contraseña") or data.get("contrasena")

        if not isinstance(usuario, str) or not usuario.strip():
            return jsonify({"error": "El campo 'usuario' es obligatorio."}), 400
        if not isinstance(password, str) or not password:
            return (
                jsonify({"error": "El campo 'contraseña' es obligatorio."}),
                400,
            )

        password_hash = generate_password_hash(password)
        db = get_db()
        try:
            db.execute(
                "INSERT INTO usuarios (usuario, password_hash) VALUES (?, ?)",
                (usuario.strip(), password_hash),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return jsonify({"error": "El usuario ya existe."}), 409

        return jsonify({"mensaje": "Usuario registrado correctamente."}), 201

    @app.post("/login")
    def login():
        data = request.get_json(silent=True) or {}
        usuario = data.get("usuario")
        password = data.get("contraseña") or data.get("contrasena")

        if not isinstance(usuario, str) or not isinstance(password, str):
            return jsonify({"error": "Datos inválidos."}), 400

        db = get_db()
        row = db.execute(
            "SELECT id, usuario, password_hash FROM usuarios WHERE usuario = ?",
            (usuario.strip(),),
        ).fetchone()

        if row is None or not check_password_hash(row["password_hash"], password):
            return jsonify({"error": "Credenciales incorrectas."}), 401

        session.clear()
        session["user_id"] = row["id"]
        session["usuario"] = row["usuario"]

        return jsonify({"mensaje": "Login correcto."}), 200

    @app.get("/tareas")
    def tareas():
        user, error_response = require_login()
        if error_response is not None:
            return error_response

        db = get_db()
        rows = db.execute(
            "SELECT id, titulo, creada_en FROM tareas WHERE usuario_id = ? ORDER BY id DESC",
            (user["id"],),
        ).fetchall()

        items = []
        for row in rows:
            tarea_id = row["id"]
            titulo = html.escape(row["titulo"])
            creada_en = html.escape(row["creada_en"])
            items.append(f"<li>[{tarea_id}] {titulo} <small>({creada_en})</small></li>")

        tareas_html = "<p>No hay tareas registradas.</p>"
        if items:
            tareas_html = "<ul>" + "".join(items) + "</ul>"

        page = f"""
        <!doctype html>
        <html lang="es">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Tareas</title>
          </head>
          <body>
            <h1>Bienvenido, {html.escape(user["usuario"])}</h1>
            <h2>Tareas registradas</h2>
            {tareas_html}
          </body>
        </html>
        """.strip()
        return Response(page, mimetype="text/html")

    @app.post("/api/tareas")
    def crear_tarea():
        user, error = require_login_json()
        if error is not None:
            return error

        data = request.get_json(silent=True) or {}
        titulo = data.get("titulo")
        if not isinstance(titulo, str) or not titulo.strip():
            return jsonify({"error": "El campo 'titulo' es obligatorio."}), 400

        db = get_db()
        cursor = db.execute(
            "INSERT INTO tareas (usuario_id, titulo) VALUES (?, ?)",
            (user["id"], titulo.strip()),
        )
        db.commit()

        tarea_id = cursor.lastrowid
        row = db.execute(
            "SELECT id, titulo, creada_en FROM tareas WHERE id = ? AND usuario_id = ?",
            (tarea_id, user["id"]),
        ).fetchone()

        return (
            jsonify(
                {
                    "mensaje": "Tarea creada.",
                    "tarea": {
                        "id": row["id"],
                        "titulo": row["titulo"],
                        "creada_en": row["creada_en"],
                    },
                }
            ),
            201,
        )

    @app.get("/api/tareas")
    def listar_tareas():
        user, error = require_login_json()
        if error is not None:
            return error

        db = get_db()
        rows = db.execute(
            "SELECT id, titulo, creada_en FROM tareas WHERE usuario_id = ? ORDER BY id DESC",
            (user["id"],),
        ).fetchall()

        tareas = [
            {"id": row["id"], "titulo": row["titulo"], "creada_en": row["creada_en"]}
            for row in rows
        ]
        return jsonify({"tareas": tareas}), 200

    @app.delete("/api/tareas/<int:tarea_id>")
    def eliminar_tarea(tarea_id: int):
        user, error = require_login_json()
        if error is not None:
            return error

        db = get_db()
        cursor = db.execute(
            "DELETE FROM tareas WHERE id = ? AND usuario_id = ?",
            (tarea_id, user["id"]),
        )
        db.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Tarea no encontrada."}), 404

        return jsonify({"mensaje": "Tarea eliminada."}), 200

    with app.app_context():
        init_db()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
