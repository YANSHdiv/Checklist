import uuid
from datetime import datetime
from typing import List, Optional, Any
import strawberry
from strawberry.types import Info
from app.models import FIXED_STEPS, Release
from app.services import (
    get_all_releases,
    get_release_by_id,
    create_release,
    update_release,
    toggle_step,
    delete_release,
)
from app.database import get_db_context


@strawberry.type
class StepType:
    id: int
    title: str


@strawberry.type
class ReleaseType:
    id: uuid.UUID
    name: str
    due_date: datetime
    additional_info: Optional[str]
    completed_steps: List[int]
    status: str
    created_at: datetime
    updated_at: datetime


@strawberry.input
class CreateReleaseInput:
    name: str
    due_date: datetime
    additional_info: Optional[str] = None


@strawberry.input
class UpdateReleaseInput:
    id: uuid.UUID
    name: Optional[str] = None
    due_date: Optional[datetime] = None
    additional_info: Optional[str] = None


def to_release_type(r: Release) -> ReleaseType:
    return ReleaseType(
        id=r.id,
        name=r.name,
        due_date=r.due_date,
        additional_info=r.additional_info,
        completed_steps=r.completed_steps or [],
        status=r.status,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@strawberry.type
class Query:
    @strawberry.field
    def releases(self, info: Info, limit: Optional[int] = 100) -> List[ReleaseType]:
        db = info.context.get("db") if info.context else None
        if db:
            releases = get_all_releases(db, limit=limit)
            return [to_release_type(r) for r in releases]
        with get_db_context() as session:
            releases = get_all_releases(session, limit=limit)
            return [to_release_type(r) for r in releases]

    @strawberry.field
    def release(self, id: uuid.UUID, info: Info) -> Optional[ReleaseType]:
        db = info.context.get("db") if info.context else None
        if db:
            r = get_release_by_id(db, id)
            return to_release_type(r) if r else None
        with get_db_context() as session:
            r = get_release_by_id(session, id)
            return to_release_type(r) if r else None

    @strawberry.field
    def steps(self) -> List[StepType]:
        return [StepType(id=s["id"], title=s["title"]) for s in FIXED_STEPS]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_release(self, input: CreateReleaseInput, info: Info) -> ReleaseType:
        db = info.context.get("db") if info.context else None
        if db:
            r = create_release(
                db=db,
                name=input.name,
                due_date=input.due_date,
                additional_info=input.additional_info,
            )
            return to_release_type(r)
        with get_db_context() as session:
            r = create_release(
                db=session,
                name=input.name,
                due_date=input.due_date,
                additional_info=input.additional_info,
            )
            return to_release_type(r)

    @strawberry.mutation
    def update_release(self, input: UpdateReleaseInput, info: Info) -> Optional[ReleaseType]:
        db = info.context.get("db") if info.context else None
        if db:
            r = update_release(
                db=db,
                release_id=input.id,
                name=input.name,
                due_date=input.due_date,
                additional_info=input.additional_info,
            )
            return to_release_type(r) if r else None
        with get_db_context() as session:
            r = update_release(
                db=session,
                release_id=input.id,
                name=input.name,
                due_date=input.due_date,
                additional_info=input.additional_info,
            )
            return to_release_type(r) if r else None

    @strawberry.mutation
    def toggle_step(self, release_id: uuid.UUID, step_id: int, info: Info) -> Optional[ReleaseType]:
        db = info.context.get("db") if info.context else None
        if db:
            r = toggle_step(db=db, release_id=release_id, step_id=step_id)
            return to_release_type(r) if r else None
        with get_db_context() as session:
            r = toggle_step(db=session, release_id=release_id, step_id=step_id)
            return to_release_type(r) if r else None

    @strawberry.mutation
    def delete_release(self, id: uuid.UUID, info: Info) -> bool:
        db = info.context.get("db") if info.context else None
        if db:
            return delete_release(db=db, release_id=id)
        with get_db_context() as session:
            return delete_release(db=session, release_id=id)


schema = strawberry.Schema(query=Query, mutation=Mutation)
