# CodingLab

CodingLab is a Render-hosted Flask API with an embedded TypeScript React dashboard for demonstrating authenticated CRUD operations against PostgreSQL.

## Live application

- Dashboard: `https://chucksgarage.onrender.com/`
- Swagger API docs: `https://chucksgarage.onrender.com/api/docs`

The dashboard and API share one Render service. The React UI displays live records and the request/response output for each CRUD action.

## Features

- JWT login with customer, mechanic, and admin roles
- CRUD for customers, mechanics, inventory, and service tickets
- Service-ticket mechanic assignments and ordered parts
- React TypeScript dashboard with live data tables and API activity output
- Swagger documentation at `/api/docs`
- GitHub Actions test gate followed by Render deployment

## Project structure

```text
app/                 Flask application and compiled dashboard assets
client/              React TypeScript dashboard source
scripts/             Database initialization and admin provisioning commands
tests/               Flask API tests
flask_app.py         Render application entrypoint
wsgi.py              Gunicorn entrypoint
```

## Local setup

1. Create and activate a Python virtual environment.
1. Install Python dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

1. Copy `.env.example` to `.env` and set:

   ```env
   DATABASE_URL=postgresql://username:password@host:5432/chucks_garage
   JWT_SECRET_KEY=replace-with-a-long-random-value
   RATELIMIT_STORAGE_URI=memory://
   ```

1. Build the dashboard:

   ```bash
   cd client
   npm install
   npm run build
   ```

1. Initialize the database:

   ```bash
   cd ..
   python -m scripts.init_db
   ```

1. Start Flask:

   ```bash
   python flask_app.py
   ```

Open `http://127.0.0.1:5000/` for the dashboard and `http://127.0.0.1:5000/api/docs` for Swagger.

## Authentication

Register a customer at `POST /users/register`, then log in through the dashboard or `POST /users/login`. Login returns an `auth_token`, which the dashboard sends as a bearer token on protected requests.

Registration always creates a customer role. To create or promote an administrator in an initialized environment:

```bash
python -m scripts.create_admin admin@example.com admin-password
```

## Local PostgreSQL and Power BI practice

Install PostgreSQL locally, create a `codinglab` database, and use a local `.env` file:

```env
DATABASE_URL=postgresql://postgres:YOUR_LOCAL_PASSWORD@localhost:5432/codinglab
JWT_SECRET_KEY=your-local-secret
RATELIMIT_STORAGE_URI=memory://
```

Run `python -m scripts.init_db` to create the schema and seed the curriculum lessons. CodingLab can remain deployed on Render for sharing while your local PostgreSQL instance is used for larger analytics exercises.

Each table has an **Export CSV** button in the dashboard. Download Students, Teachers, Lessons, or 1:1 Sessions, then use Power BI Desktop:

```text
Get Data -> Text/CSV -> select the exported file
```

In Power Query, set data types, merge session data with the Student, Teacher, and Lesson exports, then build relationships using the exported ID fields.

## Render configuration

Environment variables:

```text
DATABASE_URL=<Render internal Postgres URL>
JWT_SECRET_KEY=<generated secret>
RATELIMIT_STORAGE_URI=memory://
```

Build command:

```bash
pip install -r requirements.txt && python -m scripts.init_db
```

Start command:

```bash
gunicorn wsgi:app --bind 0.0.0.0:$PORT
```

## Validation

```bash
python -m pytest -q
cd client && npm run lint && npm run build
```
