# PFO2_SistemaGestionareasAPIBaseDatos

Sistema de Gestión de Tareas (API Flask + SQLite)

 Descripción

Este proyecto implementa una API REST básica en Python utilizando Flask.

Permite:
* Registrar usuarios
* Iniciar sesión
* Acceder a una vista protegida

Los datos se almacenan en SQLite y las contraseñas se guardan de forma segura mediante hashing.

---

Tecnologías

* Python 3
* Flask
* SQLite
* Werkzeug (hash de contraseñas)

---

Ejecución

Instalar dependencias:

```bash
pip install flask
```

Ejecutar servidor:

```bash
python servidor.py
```

Servidor disponible en:
http://127.0.0.1:5000

Ejecutar cliente:

```bash
python cliente.py
```

---

Endpoints

### POST /registro

Registra un usuario

```json
{
  "usuario": "ana",
  "contraseña": "1234"
}
```

---

### POST /login

Inicia sesión

---

### GET /tareas

Muestra una vista HTML (requiere login)

---
Base de datos

Se crea automáticamente el archivo:

```
db.sqlite3
```

Tabla:

```sql
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE,
    password TEXT
);
```

---

Seguridad

Las contraseñas se almacenan utilizando hashing (`werkzeug.security`).

---

Respuestas Conceptuales

### ¿Por qué hashear contraseñas?

Porque evita que las contraseñas se almacenen en texto plano, protegiendo los datos ante posibles accesos no autorizados.

---

### Ventajas de SQLite

* No requiere instalación de servidor
* Fácil de usar
* Persistencia en un solo archivo
* Ideal para proyectos pequeños

---

Autor

Jose Luis Colombo

---
