# OODEL — Our Bakery Management Solution
# Project Overview
  OODEL (Our Bakery Management Solution) is a bakery management web application developed for Susie's Customs Cakes. The system is designed to support bakery operations by organizing customer information, managing orders, handling customer requests, and streamlining day-to-day business workflows.

  This repository contains the source code for the project. The main branch represents the stable version of the application, while active development and feature integration take place in separate branches.

# Features
  The application is intended to support the following areas:

* Order Management: Manage and track customer orders.
* Customer Requests: Organize custom cake requests and customer requirements.
* Customer Database: Maintain customer information.
* Bakery Operations: Support day-to-day bakery management workflows.

# Repository Branches
- main : Contains the stable, tested version of the website.
- dev-branch : Integration branch where features are combined and tested before being merged into main.
- feature/* : individual work branches and where individual features are implemented, designed, and merge 
  with dev branch, which eventually merges with main branch.

# Team Members of the project
* Keyan Moiny
* Armando Cuandros
* Mher Bezik
* Harut Dolmadjian
* Vandan Patel

# Project Status
Status: In Development 


## Application Structure

- `index.html` - customer ordering and order-tracking interface.
- `baker.html` - authenticated bakery queue and production interface.
- `frontend/` - static production build plus the preserved React/Vite starter for a future migration.
- `backend/` - Django REST API, staff authentication, admin site, and order database models.
- `render.yaml` - Render Blueprint for the frontend, API, and PostgreSQL database.

The production frontend build copies the three root HTML pages into `frontend/dist` and injects the API URL. The browser never sends or stores card information. Until a payment processor is integrated, checkout supports cash on pickup only.

## Local Development

Prerequisites: Git, Node.js 24, and Python 3.14.

### Backend

Copy `backend/.env.example` to `backend/.env` and replace every placeholder. Then run:

```bash
cd backend
python -m venv .venv
```

Activate the environment with `.venv\Scripts\activate` on Windows or `source .venv/bin/activate` on macOS/Linux, then run:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py ensure_baker
python manage.py runserver
```

The API runs at `http://127.0.0.1:8000`. Its health check is `/api/health/` and the Django admin is `/admin/`.

### Frontend

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

The local frontend runs at `http://localhost:5173`. `npm run build` builds the production static prototype. Use `npm run dev:react` or `npm run build:react` only when working on the preserved React starter.

### Checks

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test

cd ../frontend
npm run build
npm run lint
```

## Deploying to Render

1. Push this branch to GitHub after reviewing it.
2. In Render, select **New > Blueprint** and choose this repository and branch.
3. Render reads `render.yaml` and proposes three resources: `oodel-web`, `oodel-api`, and `oodel-db`.
4. Enter a strong `BAKER_PASSWORD` when Render prompts for the secret value.
5. Apply the Blueprint and wait for all three resources to become healthy.
6. Open the `oodel-web` URL. Use the configured `BAKER_USERNAME` and `BAKER_PASSWORD` on `baker.html#/login`.

The free Render PostgreSQL plan expires after 30 days and has no backups. Upgrade or migrate the database before the expiration date if any real customer data is stored.

## Secrets and Environment Variables

- Never commit passwords, database URLs, API keys, or real `.env` files.
- Only placeholders belong in `.env.example`.
- Frontend variables beginning with `VITE_` are public and must never contain secrets.
- If a secret is committed, rotate it immediately; deleting the commit alone does not revoke it.
