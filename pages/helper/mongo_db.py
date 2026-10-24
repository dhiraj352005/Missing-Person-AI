import os
import json
from datetime import datetime
import pymongo

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://dhiraj352005_db_user:AQuWQJHD8RT80zlf@cluster0.qdwzjlz.mongodb.net/?retryWrites=true&w=majority",
)
DB_NAME = "missing_persons_db"

_client = None


def get_mongo_client():
    global _client
    if _client is None:
        _client = pymongo.MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=1500,
            connectTimeoutMS=1500,
        )
    return _client


def get_db():
    return get_mongo_client()[DB_NAME]


def save_registered_case_to_mongo(case):
    """Save or update a registered missing person case in MongoDB Atlas."""
    try:
        db = get_db()
        face_landmarks = []
        if isinstance(case.face_mesh, str):
            try:
                face_landmarks = json.loads(case.face_mesh)
            except Exception:
                face_landmarks = case.face_mesh
        else:
            face_landmarks = case.face_mesh

        doc = {
            "_id": str(case.id),
            "case_number": getattr(case, "case_number", None),
            "submitted_by": case.submitted_by,
            "name": case.name,
            "father_name": getattr(case, "father_name", None),
            "age": str(case.age) if getattr(case, "age", None) else None,
            "gender": getattr(case, "gender", None),
            "height": getattr(case, "height", None),
            "complainant_name": getattr(case, "complainant_name", None),
            "complainant_mobile": getattr(case, "complainant_mobile", None),
            "complainant_email": getattr(case, "complainant_email", None),
            "adhaar_card": getattr(case, "adhaar_card", None),
            "last_seen": getattr(case, "last_seen", None),
            "last_seen_datetime": getattr(case, "last_seen_datetime", None),
            "address": getattr(case, "address", None),
            "city": getattr(case, "city", None),
            "description": getattr(case, "description", None),
            "status": getattr(case, "status", "NF"),
            "birth_marks": getattr(case, "birth_marks", None),
            "matched_with": getattr(case, "matched_with", None),
            "face_mesh_landmark_count": len(face_landmarks) if isinstance(face_landmarks, list) else 0,
            "face_mesh": face_landmarks,
            "submitted_on": getattr(case, "submitted_on", datetime.utcnow()),
            "updated_at": datetime.utcnow(),
        }
        db.registered_cases.replace_one({"_id": str(case.id)}, doc, upsert=True)
        print(f"[MongoDB] Successfully saved registered case: {case.name} ({case.id})")
        return True
    except Exception as e:
        print(f"[MongoDB] Error saving registered case: {e}")
        return False


def save_public_case_to_mongo(sub):
    """Save or update a public sighting submission in MongoDB Atlas."""
    try:
        db = get_db()
        face_landmarks = []
        if isinstance(sub.face_mesh, str):
            try:
                face_landmarks = json.loads(sub.face_mesh)
            except Exception:
                face_landmarks = sub.face_mesh
        else:
            face_landmarks = sub.face_mesh

        doc = {
            "_id": str(sub.id),
            "submitted_by": getattr(sub, "submitted_by", None),
            "location": getattr(sub, "location", None),
            "mobile": getattr(sub, "mobile", None),
            "email": getattr(sub, "email", None),
            "status": getattr(sub, "status", "NF"),
            "birth_marks": getattr(sub, "birth_marks", None),
            "face_mesh_landmark_count": len(face_landmarks) if isinstance(face_landmarks, list) else 0,
            "face_mesh": face_landmarks,
            "submitted_on": getattr(sub, "submitted_on", datetime.utcnow()),
            "updated_at": datetime.utcnow(),
        }
        db.public_submissions.replace_one({"_id": str(sub.id)}, doc, upsert=True)
        print(f"[MongoDB] Successfully saved public submission ({sub.id})")
        return True
    except Exception as e:
        print(f"[MongoDB] Error saving public submission: {e}")
        return False


def update_found_status_in_mongo(register_case_id: str, public_case_id: str):
    """Update status to Found ('F') and link matching IDs in MongoDB Atlas."""
    try:
        db = get_db()
        db.registered_cases.update_one(
            {"_id": str(register_case_id)},
            {"$set": {"status": "F", "matched_with": str(public_case_id), "updated_at": datetime.utcnow()}},
        )
        db.public_submissions.update_one(
            {"_id": str(public_case_id)},
            {"$set": {"status": "F", "updated_at": datetime.utcnow()}},
        )
        print(f"[MongoDB] Updated found status for case {register_case_id} matched with {public_case_id}")
        return True
    except Exception as e:
        print(f"[MongoDB] Error updating found status: {e}")
        return False


def update_registered_case_in_mongo(case_id: str, fields: dict):
    """Update specific fields in MongoDB Atlas."""
    try:
        db = get_db()
        fields_copy = dict(fields)
        fields_copy["updated_at"] = datetime.utcnow()
        db.registered_cases.update_one({"_id": str(case_id)}, {"$set": fields_copy})
        return True
    except Exception as e:
        print(f"[MongoDB] Error updating case {case_id}: {e}")
        return False


def delete_registered_case_in_mongo(case_id: str):
    """Delete a registered case from MongoDB Atlas."""
    try:
        db = get_db()
        db.registered_cases.delete_one({"_id": str(case_id)})
        print(f"[MongoDB] Deleted case {case_id}")
        return True
    except Exception as e:
        print(f"[MongoDB] Error deleting case {case_id}: {e}")
        return False
