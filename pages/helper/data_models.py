from uuid import uuid4
from datetime import datetime

from sqlmodel import Field, create_engine, SQLModel


class PublicSubmissions(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    # Changed: UUID -> str, uuid4 -> lambda: str(uuid4())
    id: str = Field(
        primary_key=True, default_factory=lambda: str(uuid4()), nullable=False
    )
    submitted_by: str = Field(max_length=128, nullable=True)
    face_mesh: str = Field(nullable=False)  # JSON string of face mesh landmarks
    location: str = Field(max_length=128, nullable=True)
    mobile: str = Field(max_length=10, nullable=False)
    email: str = Field(max_length=64, nullable=True)
    status: str = Field(max_length=16, nullable=False)
    birth_marks: str = Field(max_length=512, nullable=True)
    # Changed: datetime.utcnow() -> datetime.utcnow (remove parentheses)
    submitted_on: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class RegisteredCases(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: str = Field(
        primary_key=True, default_factory=lambda: str(uuid4()), nullable=False
    )
    case_number: str = Field(max_length=32, nullable=True, default=None)
    submitted_by: str = Field(max_length=64, nullable=False)
    name: str = Field(max_length=128, nullable=False)
    father_name: str = Field(max_length=128, nullable=True, default="")
    age: str = Field(max_length=8, nullable=True)
    gender: str = Field(max_length=16, nullable=True, default=None)
    height: str = Field(max_length=32, nullable=True, default=None)
    complainant_name: str = Field(max_length=128, nullable=False)
    complainant_mobile: str = Field(max_length=15, nullable=False)
    complainant_email: str = Field(max_length=128, nullable=True, default=None)
    adhaar_card: str = Field(max_length=16, nullable=True, default="")
    last_seen: str = Field(max_length=128, nullable=False)
    last_seen_datetime: str = Field(max_length=64, nullable=True, default=None)
    address: str = Field(max_length=512, nullable=True, default="")
    city: str = Field(max_length=64, nullable=True, default=None)
    description: str = Field(max_length=1024, nullable=True, default=None)
    face_mesh: str = Field(nullable=False)  # JSON string of face mesh landmarks
    submitted_on: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    status: str = Field(max_length=16, nullable=False, default="NF")
    birth_marks: str = Field(max_length=512, nullable=True, default="")
    matched_with: str = Field(nullable=True, default="")


class Users(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: str = Field(
        primary_key=True, default_factory=lambda: str(uuid4()), nullable=False
    )
    username: str = Field(max_length=64, nullable=False, unique=True, index=True)
    name: str = Field(max_length=128, nullable=False)
    email: str = Field(max_length=128, nullable=True)
    password_hash: str = Field(max_length=256, nullable=False)
    algorithm: str = Field(max_length=32, default="Argon2id")
    city: str = Field(max_length=64, default="Pune")
    area: str = Field(max_length=64, default="")
    role: str = Field(max_length=32, default="Officer")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


if __name__ == "__main__":
    sqlite_url = "sqlite:///example.db"
    engine = create_engine(sqlite_url)

    RegisteredCases.__table__.create(engine)
    PublicSubmissions.__table__.create(engine)
    Users.__table__.create(engine)
