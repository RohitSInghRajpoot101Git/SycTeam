# SycTeam

SycTeam is a full-stack project and task management application with role-based collaboration, task tracking, and live deployment on Railway.

## Live Deployment

- App URL: https://sycteam-web-production.up.railway.app
- Health check: https://sycteam-web-production.up.railway.app/api/health

## Features

- Authentication with signup/login and bearer token sessions
- Role-based access with `Admin` and `Member` project memberships
- Project management: create and delete projects (admin only)
- Team management: add/update project members by email and role
- Task management: create tasks, assign members, update statuses, and due dates
- Dashboard metrics for projects, total tasks, done tasks, and overdue tasks
- Improved UI for project workspace, team panel, task form, and task cards

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Pydantic
- Frontend: React, Vite, lucide-react
- Database: PostgreSQL
- Deployment: Railway + Docker

## Local Setup

1. Ensure local PostgreSQL is running and a database exists, for example:

```text
postgresql://postgres:Rohit17240@localhost:5432/taskManager
```

2. Create backend environment file:

```bash
cd backend
cp .env.example .env
cd ..
```

3. Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

4. Run backend API:

```bash
python -m uvicorn backend.app.main:app --reload --port 8001
```

5. Run frontend in another terminal:

```bash
cd frontend
npm install
VITE_API_URL=http://127.0.0.1:8001/api npm run dev
```

Frontend runs at `http://localhost:5173`.

## Railway Configuration

The app is configured for Railway with:

- `Dockerfile` for deterministic Python + frontend build/runtime
- `nixpacks.toml` for build settings
- Environment variables on `sycteam-web` service:
  - `DATABASE_URL=${{Postgres.DATABASE_URL}}`
  - `SECRET_KEY=<long-random-secret>`
  - `DB_SCHEMA=team_task_manager_app`

## API Overview

- `POST /api/auth/signup` - create account
- `POST /api/auth/login` - login and receive bearer token
- `GET /api/projects` - list user projects
- `POST /api/projects` - create project (admin)
- `DELETE /api/projects/{project_id}` - delete project (admin)
- `GET /api/projects/{project_id}/members` - list project members
- `POST /api/projects/{project_id}/members` - add/update member (admin)
- `GET /api/tasks?project_id=1` - list tasks
- `POST /api/projects/{project_id}/tasks` - create task (admin)
- `PATCH /api/tasks/{task_id}` - update task; members can only update status
- `GET /api/dashboard` - project and task metrics
