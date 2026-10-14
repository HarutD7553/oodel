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
- dev :  Integration branch where features are combined and tested before being merged into main.
- feature/* : individual work branches and where individual features are implemented, designed, and merge 
  with dev branch, which eventually merges with main branch.

# Team Members of the project
* Keyan Moiny
* Armando Cuandros
* Mher Bizek
* Harutiyan Dolmandjian
* Vandan Patel

# Project Status
Status: In Development 


## Armando's Frontend and Backend Creations Steps and Secrets

A short description of what this project does (for example: a hunting-focused mapping web app built for CIT 480).

## Project Structure

- `frontend/` - the React app (what users see in the browser)
- `backend/` - the Django app (the server and database logic)

## Prerequisites

Install these before you start:

- Git
- Node.js (LTS version)
- Python 3

## Getting Started

### 1. Clone the repo

```bash
git clone <repo-link>
cd <repo-folder-name>
```

### 2. Set up your environment files

Copy each `.env.example` file to `.env` and fill in your own values:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Then open each new `.env` file and replace the placeholder values with your own. Ask the team for any values you don't have.

### 3. Run the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 manage.py runserver
```

The backend runs at http://127.0.0.1:8000

Each time you open a new terminal to work on the backend, run `source venv/bin/activate` from inside `backend/` first.

### 4. Run the frontend

Open a second terminal tab, then:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at http://localhost:5173

## Secrets and Environment Variables

- Copy `.env.example` to `.env` and fill in your own values.
- **Never commit real secrets.** This includes passwords, API keys, and tokens. The `.env` files are listed in `.gitignore` and must stay out of GitHub.
- Only put fake or blank placeholder values in `.env.example`.
- Variables in the frontend (anything starting with `VITE_`) are visible to anyone using the app, so never put secrets there.
- Share real secrets through a private channel or a password manager, not in public chats or in the repo.
- **If a secret is committed by accident, tell the team and change it right away.** Deleting the commit is not enough, because the secret may already have been copied.