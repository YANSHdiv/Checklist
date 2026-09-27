import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, DateTime, JSON, Uuid, Index, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

FIXED_STEPS = [
    {"id": 1, "title": "Code freeze"},
    {"id": 2, "title": "Run automated tests"},
    {"id": 3, "title": "Review changelog"},
    {"id": 4, "title": "Update documentation"},
    {"id": 5, "title": "Run security checks"},
    {"id": 6, "title": "Build production bundle"},
    {"id": 7, "title": "Deploy to staging"},
    {"id": 8, "title": "Run smoke tests"},
    {"id": 9, "title": "Deploy to production"},
    {"id": 10, "title": "Verify production"},
]

TOTAL_STEPS = len(FIXED_STEPS)


def compute_status(completed_steps: List[int]) -> str:
    """Compute release status from completed steps list.
    Fast-path without set allocation when empty or full.
    0 -> planned
    1-9 -> ongoing
    10 -> done
    """
    if not completed_steps:
        return "planned"
    length = len(completed_steps)
    if length == 0:
        return "planned"
    # Fast path: if steps are already uniquely maintained
    if length == TOTAL_STEPS:
        # Check if all unique 1..10
        if len(set(completed_steps)) == TOTAL_STEPS:
            return "done"
    elif length > TOTAL_STEPS:
        if len(set(completed_steps)) >= TOTAL_STEPS:
            return "done"
    count = len(set(completed_steps))
    if count == 0:
        return "planned"
    elif count >= TOTAL_STEPS:
        return "done"
    return "ongoing"


class Base(DeclarativeBase):
    pass


class Release(Base):
    __tablename__ = "releases"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    additional_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_steps: Mapped[List[int]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_releases_created_at_desc", created_at.desc()),
    )

    @property
    def status(self) -> str:
        return compute_status(self.completed_steps or [])
