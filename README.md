# ChucksGarage API

Flask API for managing customers, mechanics, service tickets, part inventory, and user authentication.

## What this repo includes

- JWT-based authentication
- Role-aware authorization (admin, mechanic, customer)
- CRUD endpoints for customers, mechanics, service tickets, and inventory parts
- Modeled junction-table support for ordered parts
- Postman collection: ChucksGarage.postman_collection.json

## Requirements

- Python 3.11+
- MySQL
- Flask + SQLAlchemy app already listed in requirements.txt

## Assignment-ready data model note

This app now includes a modeled junction table for service-ticket parts.

Instead of a simple many-to-many table that only stores foreign keys, we use a real `ServiceTicketPart` model so each ordered item can keep metadata such as:

- `quantity`
- `unit_cost`
- `part_id`
- `service_ticket_id`

This matches the lesson concept where a junction table may need extra information, such as order line items in a cafe or parts in a repair shop.

The relationship pattern is:

- one `Service_Ticket` can have many `ServiceTicketPart` records
- one `Part` can appear across many service ticket orders
- each row in `service_ticket_parts` stores the order details for a specific part on a specific ticket

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

## Part-order example endpoints

The parts-ordering feature is implemented as a modeled association table.

### Add a part to a service ticket

POST /service-tickets/<service_ticket_id>/parts

Example JSON body:

```json
{
  "part_id": 1,
  "quantity": 2,
  "unit_cost": 42.5
}
```

### Get all ordered parts for a service ticket

GET /service-tickets/<service_ticket_id>/parts

This returns the list of part line items, including the associated part metadata and the quantity/cost values.

### Find the most-used parts

GET /service-tickets/parts/popular

This endpoint uses a Python lambda to add quantities from every part-order line item, then sorts inventory from most used to least used. The response includes `total_used` beside each part's current `stock_quantity` for restocking decisions.

## Inventory endpoints

All inventory endpoints require a bearer token. Creating or deleting a part requires an admin role; admins and mechanics can update a part.

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/inventory` | Create a part with `name`, `sku`, and `stock_quantity`. |
| `GET` | `/inventory` | List parts. Supports `search`, `sort=name` or `sort=stock`, `offset`, and `limit`. |
| `GET` | `/inventory/<part_id>` | Get one part. |
| `PUT` | `/inventory/<part_id>` | Update a part. |
| `DELETE` | `/inventory/<part_id>` | Delete a part that has no service-ticket orders. |

Example create body:

```json
{
   "name": "Brake Pad Set",
   "sku": "BR-100",
   "stock_quantity": 20
}
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

### Seed demo data for repair tickets and part orders

```bash
python scripts/harden_existing_data.py
```

This script adds demo customers, mechanics, tickets, parts, and part-order records to help demonstrate the many-to-many-with-metadata relationship.

### Run tests

```bash
python -m pytest -q
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
- /inventory

Note: the service ticket path uses hyphens, not underscores.

## Test suite

Run tests with:

```bash
python -m pytest -q
```
