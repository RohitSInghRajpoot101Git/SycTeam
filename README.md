# Team Task Manager

A full-stack project and task management app built for the assignment:

- FastAPI REST API
- React frontend
- PostgreSQL database
- Signup/login authentication
- Project membership with `Admin` and `Member` roles
- Task creation, assignment, status tracking, and overdue dashboard
- Railway-ready deployment config

## Features

Admins can create projects, add team members by email, assign roles, and create tasks. Members can view projects they belong to and update task status. The dashboard shows total projects, total tasks, completed tasks, and overdue tasks.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Pydantic
- Frontend: React, Vite, lucide-react
- Database: PostgreSQL
- Deployment: Railway with Nixpacks

## Local Setup

Make sure your local PostgreSQL server is running and that this database exists:

```text
postgresql://postgres:Rohit17240@localhost:5432/taskManager
```

Create the backend environment file:

```bash
cd backend
cp .env.example .env
cd ..
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Run the API from the repository root:

```bash
uvicorn backend.app.main:app --reload
```

Run the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`; API runs at `http://localhost:8000`.

## Railway Deployment

1. Push this repository to GitHub.
2. Create a new Railway project from the GitHub repo.
3. Add a Railway PostgreSQL database.
4. Set these environment variables on the web service:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=use-a-long-random-secret
```

5. Railway will use `nixpacks.toml` to install Python and Node dependencies, build React, and start FastAPI.

## API Overview

- `POST /api/auth/signup` - create account
- `POST /api/auth/login` - login and receive bearer token
- `GET /api/projects` - list user projects
- `POST /api/projects` - create project as Admin
- `GET /api/projects/{project_id}/members` - list project members
- `POST /api/projects/{project_id}/members` - add/update member, Admin only
- `GET /api/tasks?project_id=1` - list tasks
- `POST /api/projects/{project_id}/tasks` - create task, Admin only
- `PATCH /api/tasks/{task_id}` - update task; Members can update status only
- `GET /api/dashboard` - task and project metrics

## Submission Checklist

- Live URL: add Railway URL here after deployment
- GitHub repo: add repository URL here
- README: included
- Demo video: record signup, project creation, adding a member, creating a task, status update, and dashboard
