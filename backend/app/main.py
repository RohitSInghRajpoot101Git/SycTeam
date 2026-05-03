from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from .database import get_db, init_db
from .models import Membership, Project, ProjectRole, Task, TaskStatus, User
from .schemas import (
    AuthIn,
    AuthOut,
    DashboardOut,
    MemberCreate,
    MemberOut,
    ProjectCreate,
    ProjectOut,
    SignupIn,
    TaskCreate,
    TaskOut,
    TaskUpdate,
    UserOut,
)
from .security import create_token, hash_password, read_token, verify_password


init_db()

app = FastAPI(title="Team Task Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    payload = read_token(authorization.removeprefix("Bearer ").strip())
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.get(User, payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def project_role(db: Session, project_id: int, user_id: int) -> ProjectRole:
    membership = db.scalar(
        select(Membership).where(Membership.project_id == project_id, Membership.user_id == user_id)
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not on this project")
    return membership.role


def require_admin(db: Session, project_id: int, user_id: int) -> None:
    if project_role(db, project_id, user_id) != ProjectRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


def ensure_assignee_is_member(db: Session, project_id: int, assignee_id: int | None) -> None:
    if assignee_id is None:
        return
    exists = db.scalar(select(Membership.id).where(Membership.project_id == project_id, Membership.user_id == assignee_id))
    if not exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignee must be a project member")


def project_out(project: Project, role: ProjectRole) -> ProjectOut:
    return ProjectOut(id=project.id, name=project.name, description=project.description, role=role)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/auth/signup", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return AuthOut(token=create_token(user.id), user=user)


@app.post("/api/auth/login", response_model=AuthOut)
def login(payload: AuthIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return AuthOut(token=create_token(user.id), user=user)


@app.get("/api/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@app.get("/api/projects", response_model=list[ProjectOut])
def list_projects(user: User = Depends(current_user), db: Session = Depends(get_db)):
    memberships = db.scalars(
        select(Membership).options(joinedload(Membership.project)).where(Membership.user_id == user.id)
    ).all()
    return [project_out(m.project, m.role) for m in memberships]


@app.post("/api/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    project = Project(name=payload.name.strip(), description=payload.description.strip())
    db.add(project)
    db.flush()
    db.add(Membership(user_id=user.id, project_id=project.id, role=ProjectRole.admin))
    db.commit()
    db.refresh(project)
    return project_out(project, ProjectRole.admin)


@app.get("/api/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project_out(project, project_role(db, project_id, user.id))


@app.get("/api/projects/{project_id}/members", response_model=list[MemberOut])
def list_members(project_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    project_role(db, project_id, user.id)
    return db.scalars(
        select(Membership).options(joinedload(Membership.user)).where(Membership.project_id == project_id)
    ).all()


@app.post("/api/projects/{project_id}/members", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def add_member(project_id: int, payload: MemberCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_admin(db, project_id, user.id)
    target = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User must sign up before being added")
    membership = db.scalar(select(Membership).where(Membership.project_id == project_id, Membership.user_id == target.id))
    if membership:
        membership.role = payload.role
    else:
        membership = Membership(project_id=project_id, user_id=target.id, role=payload.role)
        db.add(membership)
    db.commit()
    return db.scalar(
        select(Membership).options(joinedload(Membership.user)).where(Membership.project_id == project_id, Membership.user_id == target.id)
    )


@app.get("/api/tasks", response_model=list[TaskOut])
def list_tasks(
    project_id: int | None = Query(default=None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    project_ids = select(Membership.project_id).where(Membership.user_id == user.id)
    query = select(Task).options(joinedload(Task.assignee)).where(Task.project_id.in_(project_ids))
    if project_id is not None:
        project_role(db, project_id, user.id)
        query = query.where(Task.project_id == project_id)
    return db.scalars(query.order_by(Task.created_at.desc())).all()


@app.post("/api/projects/{project_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(project_id: int, payload: TaskCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_admin(db, project_id, user.id)
    ensure_assignee_is_member(db, project_id, payload.assignee_id)
    task = Task(project_id=project_id, creator_id=user.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return db.scalar(select(Task).options(joinedload(Task.assignee)).where(Task.id == task.id))


@app.patch("/api/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    task = db.scalar(select(Task).options(joinedload(Task.assignee)).where(Task.id == task_id))
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    role = project_role(db, task.project_id, user.id)
    changes = payload.model_dump(exclude_unset=True)
    if role != ProjectRole.admin and set(changes) != {"status"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Members can only update task status")
    if "assignee_id" in changes:
        ensure_assignee_is_member(db, task.project_id, changes["assignee_id"])
    for field, value in changes.items():
        setattr(task, field, value)
    db.commit()
    return db.scalar(select(Task).options(joinedload(Task.assignee)).where(Task.id == task.id))


@app.get("/api/dashboard", response_model=DashboardOut)
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    project_ids = select(Membership.project_id).where(Membership.user_id == user.id)
    base = select(Task).where(Task.project_id.in_(project_ids))
    tasks = db.scalars(base).all()
    return DashboardOut(
        total_tasks=len(tasks),
        todo=sum(t.status == TaskStatus.todo for t in tasks),
        in_progress=sum(t.status == TaskStatus.in_progress for t in tasks),
        done=sum(t.status == TaskStatus.done for t in tasks),
        overdue=sum(bool(t.due_date and t.due_date < date.today() and t.status != TaskStatus.done) for t in tasks),
        projects=db.scalar(select(func.count()).select_from(Membership).where(Membership.user_id == user.id)) or 0,
    )


static_dir = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
