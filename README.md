# ChucksGarage API

Flask API for managing customers, mechanics, service tickets, and user authentication.

## What this repo includes

- JWT-based authentication
- Role-aware authorization (admin, mechanic, customer)
- CRUD endpoints for customers, mechanics, and service tickets
- Postman collection: ChucksGarage.postman_collection.json

## Requirements

- Python 3.11+
- MySQL

## Setup

1. Create and activate a virtual environment.
1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

1. Copy `.env.example` to `.env` and set values:

   - DATABASE_URL
   - JWT_SECRET_KEY
   - RATELIMIT_STORAGE_URI

Example .env values:

```env
DATABASE_URL=mysql+mysqlconnector://username:password@localhost/chucks_garage
JWT_SECRET_KEY=replace-with-a-long-random-value
RATELIMIT_STORAGE_URI=memory://
```

1. Start the API:

   ```bash
   python app.py
   ```

Default local URL:

```text
http://127.0.0.1:5000
```

## Authentication flow

### Register customer user

POST /users/register

Body example:

```json
{
  "email": "driver@example.com",
  "password": "strong-password",
  "name": "Driver One",
  "date_of_birth": "1990-01-01"
}
```

Note: registration always creates a customer role.

### Login

POST /users/login

Body example:

```json
{
  "email": "driver@example.com",
  "password": "strong-password"
}
```

Response includes auth_token.

### Use token

Send this header on protected routes:

```text
Authorization: Bearer <auth_token>
```

## Admin access for full CRUD

Many mutation routes require admin role. If you do not already have an admin user in your database, create one:

```bash
python -c "from app import create_app; from app.extensions import db; from app.models import User; from werkzeug.security import generate_password_hash; app=create_app('config.DevelopmentConfig'); ctx=app.app_context(); ctx.push(); email='admin@example.com'; pwd='admin-password'; existing=db.session.execute(db.select(User).where(User.email==email)).scalar_one_or_none(); print('Admin already exists') if existing else (db.session.add(User(email=email, password_hash=generate_password_hash(pwd), role='admin')), db.session.commit(), print('Admin created')); ctx.pop()"
```

Then login in Postman with:

```json
{
  "email": "admin@example.com",
  "password": "admin-password"
}
```

## How to use in Postman

1. Start the API with:

   ```bash
   python app.py
   ```

1. Import these files into Postman:

   - `ChucksGarage.postman_collection.json`
   - `ChucksGarage.postman_environment.json`

1. In Postman, select environment `ChucksGarage Local`.

1. Run request `Reg/Log -> AdminLog`.

1. Confirm login returns JSON with `auth_token`.

1. Run any request under `customers`, `mechanics`, or `SerTick`.

Protected requests automatically use the collection bearer token variable `{{token}}`, which is set by the login request test script.

If login does not set token automatically, add this in the login request Tests tab:

```javascript
pm.collectionVariables.set("token", pm.response.json().auth_token);
```

## Common workflows

### Start the app

```bash
python app.py
```

The app runs at `http://127.0.0.1:5000`.

### Log in as admin

Use the `Reg/Log -> AdminLog` request in Postman, or send this payload to `POST /users/login`:

```json
{
   "email": "admin@example.com",
   "password": "admin-password"
}
```

### Run tests

```bash
python -m unittest discover -s tests
```

### Connect SQL Workbench

Use the same MySQL settings from `.env`:

```text
host: localhost
port: 3306
database: chucks_garage
user: root
password: your local MySQL password
```

If SQL Workbench can connect and the app starts, the backend stack is healthy.

## Route prefixes

Use these prefixes exactly:

- /users
- /customers
- /mechanics
- /service-tickets

Note: the service ticket path uses hyphens, not underscores.

## Test suite

Run tests with:

```bash
python -m unittest discover -s tests
```
