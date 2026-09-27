import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Release, TOTAL_STEPS


def get_all_releases(db: Session, limit: Optional[int] = 100) -> List[Release]:
    stmt = select(Release).order_by(Release.created_at.desc())
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt).all())


def get_release_by_id(db: Session, release_id: uuid.UUID) -> Optional[Release]:
    return db.get(Release, release_id)


def create_release(
    db: Session,
    name: str,
    due_date: datetime,
    additional_info: Optional[str] = None,
) -> Release:
    if not name or not name.strip():
        raise ValueError("Release name is required and cannot be empty.")

    release = Release(
        name=name.strip(),
        due_date=due_date,
        additional_info=additional_info.strip() if additional_info else None,
        completed_steps=[],
    )
    db.add(release)
    db.commit()
    db.refresh(release)
    return release


def update_release(
    db: Session,
    release_id: uuid.UUID,
    name: Optional[str] = None,
    due_date: Optional[datetime] = None,
    additional_info: Optional[str] = None,
) -> Optional[Release]:
    release = db.get(Release, release_id)
    if not release:
        return None

    if name is not None:
        if not name.strip():
            raise ValueError("Release name cannot be empty.")
        release.name = name.strip()

    if due_date is not None:
        release.due_date = due_date

    if additional_info is not None:
        release.additional_info = additional_info.strip() if additional_info else None

    try:
        db.commit()
        db.refresh(release)
    except Exception:
        db.rollback()
        return None
    return release


def toggle_step(db: Session, release_id: uuid.UUID, step_id: int) -> Optional[Release]:
    if step_id < 1 or step_id > TOTAL_STEPS:
        raise ValueError(f"stepId must be between 1 and {TOTAL_STEPS}")

    release = db.get(Release, release_id)
    if not release:
        return None

    current_steps = list(release.completed_steps or [])
    if step_id in current_steps:
        current_steps.remove(step_id)
    else:
        current_steps.append(step_id)

    # Keep steps unique and sorted
    release.completed_steps = sorted(list(set(current_steps)))
    try:
        db.commit()
        db.refresh(release)
    except Exception:
        db.rollback()
        return None
    return release


def delete_release(db: Session, release_id: uuid.UUID) -> bool:
    release = db.get(Release, release_id)
    if not release:
        return False
    try:
        db.delete(release)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
