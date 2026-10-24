import os
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError, VerificationError
from sqlmodel import Session, select

from pages.helper.data_models import Users
from pages.helper.db_queries import engine
from pages.helper.mongo_db import get_db

# Configure Argon2id hasher
# Memory cost: 65,536 KB (64 MB), Time cost: 2 iterations, Parallelism: 4 threads, Hash length: 32 bytes
ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    type=Type.ID,
)

# JWT configuration (Secret >= 32 bytes for HS256)
JWT_SECRET = os.environ.get(
    "JWT_SECRET",
    "missing_person_ai_super_secure_jwt_secret_key_2026_32bytes_long",
)
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using the Argon2id algorithm."""
    return ph.hash(plain_password)


def verify_password(stored_hash: str, plain_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash (with legacy bcrypt fallback)."""
    if not stored_hash or not plain_password:
        return False
    # Try Argon2id
    try:
        if ph.verify(stored_hash, plain_password):
            return True
    except (VerifyMismatchError, VerificationError):
        pass
    except Exception:
        pass

    # Fallback to bcrypt for legacy hashes ($2b$, $2a$)
    try:
        import bcrypt

        if stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"):
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), stored_hash.encode("utf-8")
            )
    except Exception:
        pass

    return False


def generate_jwt_token(user_doc: dict) -> str:
    """Generate a signed JWT token containing user identity and role."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_doc["username"],
        "name": user_doc.get("name", user_doc["username"]),
        "email": user_doc.get("email", ""),
        "role": user_doc.get("role", "Officer"),
        "city": user_doc.get("city", ""),
        "area": user_doc.get("area", ""),
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_jwt_token(token: str) -> dict | None:
    """Verify and decode a JWT token."""
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError:
        print("[auth] JWT token has expired.")
        return None
    except jwt.InvalidTokenError as e:
        print(f"[auth] Invalid JWT token: {e}")
        return None


def get_user_by_username(username: str) -> dict | None:
    """Fetch user document from local SQLite or MongoDB Atlas."""
    username_clean = username.strip().lower()
    if not username_clean:
        return None

    # 1. Check local SQLite database (always fast & available)
    try:
        with Session(engine) as session:
            user_obj = session.exec(
                select(Users).where(Users.username == username_clean)
            ).first()
            if user_obj:
                return {
                    "username": user_obj.username,
                    "name": user_obj.name,
                    "email": user_obj.email or "",
                    "password_hash": user_obj.password_hash,
                    "algorithm": user_obj.algorithm,
                    "city": user_obj.city or "",
                    "area": user_obj.area or "",
                    "role": user_obj.role,
                }
    except Exception as e:
        print(f"[auth] SQLite fetch user error: {e}")

    # 2. Check MongoDB Atlas Cloud (fallback)
    try:
        db = get_db()
        mongo_user = db.users.find_one({"username": username_clean})
        if mongo_user:
            # Cache to local SQLite for offline access
            try:
                with Session(engine) as session:
                    cached_user = Users(
                        id=str(mongo_user.get("_id", uuid4())),
                        username=mongo_user["username"],
                        name=mongo_user.get("name", mongo_user["username"]),
                        email=mongo_user.get("email"),
                        password_hash=mongo_user.get("password_hash", ""),
                        algorithm=mongo_user.get("algorithm", "Argon2id"),
                        city=mongo_user.get("city", "Pune"),
                        area=mongo_user.get("area", ""),
                        role=mongo_user.get("role", "Officer"),
                    )
                    session.add(cached_user)
                    session.commit()
            except Exception:
                pass
            return mongo_user
    except Exception as e:
        print(f"[auth] MongoDB lookup notice: {e}")

    return None


def register_user(
    username: str,
    name: str,
    email: str,
    password: str,
    city: str,
    area: str,
    role: str = "Officer",
) -> tuple[bool, str, dict | None]:
    """
    Register a new user in SQLite and sync to MongoDB Atlas with Argon2id password hashing.
    """
    username_clean = username.strip().lower()
    if not username_clean:
        return False, "Username is required.", None
    if not password:
        return False, "Password is required.", None
    if len(password) < 4:
        return False, "Password must be at least 4 characters.", None

    # Check if username already exists locally
    try:
        with Session(engine) as session:
            existing = session.exec(
                select(Users).where(Users.username == username_clean)
            ).first()
            if existing:
                return False, f"Username '{username_clean}' already exists.", None
    except Exception as e:
        print(f"[auth] SQLite check error: {e}")

    # Compute Argon2id hash
    hashed_pw = hash_password(password)
    user_id = str(uuid4())

    user_dict = {
        "id": user_id,
        "username": username_clean,
        "name": name.strip() or username_clean,
        "email": email.strip() or None,
        "password_hash": hashed_pw,
        "algorithm": "Argon2id",
        "city": city.strip() or "Pune",
        "area": area.strip() or "",
        "role": role,
    }

    # Save to local SQLite
    try:
        with Session(engine) as session:
            new_user = Users(
                id=user_id,
                username=username_clean,
                name=user_dict["name"],
                email=user_dict["email"],
                password_hash=hashed_pw,
                algorithm="Argon2id",
                city=user_dict["city"],
                area=user_dict["area"],
                role=role,
            )
            session.add(new_user)
            session.commit()
    except Exception as e:
        return False, f"Failed to save user in database: {e}", None

    # Sync to MongoDB Atlas in background daemon thread (non-blocking)
    import threading

    def _sync_to_mongo():
        try:
            db = get_db()
            doc = {
                "_id": user_id,
                "username": username_clean,
                "name": user_dict["name"],
                "email": user_dict["email"],
                "password_hash": hashed_pw,
                "algorithm": "Argon2id",
                "city": user_dict["city"],
                "area": user_dict["area"],
                "role": role,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            db.users.replace_one({"username": username_clean}, doc, upsert=True)
        except Exception as e:
            print(f"[auth] MongoDB cloud sync notice: {e}")

    threading.Thread(target=_sync_to_mongo, daemon=True).start()

    return True, "User registered successfully!", user_dict


def authenticate_user(
    username: str, password: str
) -> tuple[bool, str, dict | None, str | None]:
    """
    Authenticate a user using Argon2id, returning a signed JWT token on success.
    """
    username_clean = username.strip().lower()
    user_doc = get_user_by_username(username_clean)
    if not user_doc:
        return False, "User not found.", None, None

    stored_hash = user_doc.get("password_hash")
    if not stored_hash:
        return False, "Account has no password set.", None, None

    # Verify with Argon2id
    if not verify_password(stored_hash, password):
        return False, "Invalid username or password.", None, None

    # Generate JWT token
    token = generate_jwt_token(user_doc)
    return True, "Authentication successful.", user_doc, token


def ensure_default_users():
    """
    Seed initial user 'dhiraj' (Admin) and 'gagan' into local SQLite and MongoDB Atlas.
    """
    import threading

    default_accounts = [
        {
            "username": "dhiraj",
            "name": "Dhiraj Raut",
            "email": "dhiraj352005@gmail.com",
            "password": "dhiraj123",
            "city": "Pune",
            "area": "Pimpri",
            "role": "Admin",
        },
        {
            "username": "gagan",
            "name": "Gagandeep Singh",
            "email": "gaganmanku96@gmail.com",
            "password": "abc",
            "city": "Noida",
            "area": "Sector 128",
            "role": "Admin",
        },
    ]

    for acc in default_accounts:
        try:
            with Session(engine) as session:
                existing = session.exec(
                    select(Users).where(Users.username == acc["username"])
                ).first()
                if not existing:
                    hashed = hash_password(acc["password"])
                    user_row = Users(
                        id=str(uuid4()),
                        username=acc["username"],
                        name=acc["name"],
                        email=acc["email"],
                        password_hash=hashed,
                        algorithm="Argon2id",
                        city=acc["city"],
                        area=acc["area"],
                        role=acc["role"],
                    )
                    session.add(user_row)
                    session.commit()
                    print(f"[auth] Seeded default user '{acc['username']}' into SQLite.")
        except Exception as e:
            print(f"[auth] Error seeding '{acc['username']}' into SQLite: {e}")

    # Mirror into MongoDB Atlas in background daemon thread
    def _seed_mongo():
        for acc in default_accounts:
            try:
                db = get_db()
                if db.users.count_documents({"username": acc["username"]}) == 0:
                    hashed = hash_password(acc["password"])
                    db.users.insert_one(
                        {
                            "username": acc["username"],
                            "name": acc["name"],
                            "email": acc["email"],
                            "password_hash": hashed,
                            "algorithm": "Argon2id",
                            "city": acc["city"],
                            "area": acc["area"],
                            "role": acc["role"],
                            "created_at": datetime.now(timezone.utc),
                            "updated_at": datetime.now(timezone.utc),
                        }
                    )
            except Exception:
                pass

    threading.Thread(target=_seed_mongo, daemon=True).start()
