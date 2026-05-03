from datetime import date

from pydantic import BaseModel, EmailStr, Field

from .models import ProjectRole, TaskStatus


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr

    model_config = {"from_attributes": True}


class AuthIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=80)


class SignupIn(AuthIn):
    name: str = Field(min_length=2, max_length=80)


class AuthOut(BaseModel):
    token: str
    user: UserOut


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=1000)


class ProjectOut(ProjectCreate):
    id: int
    role: ProjectRole


class MemberCreate(BaseModel):
    email: EmailStr
    role: ProjectRole = ProjectRole.member


class MemberOut(BaseModel):
    id: int
    role: ProjectRole
    user: UserOut

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=140)
    description: str = Field(default="", max_length=1500)
    status: TaskStatus = TaskStatus.todo
    due_date: date | None = None
    assignee_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=140)
    description: str | None = Field(default=None, max_length=1500)
    status: TaskStatus | None = None
    due_date: date | None = None
    assignee_id: int | None = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    status: TaskStatus
    due_date: date | None
    project_id: int
    assignee: UserOut | None

    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    total_tasks: int
    todo: int
    in_progress: int
    done: int
    overdue: int
    projects: int
