import os
import json
import traceback
import warnings
from collections import defaultdict

import cv2
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors, KNeighborsClassifier

warnings.filterwarnings(action="ignore")

from pages.helper import db_queries
from pages.helper.utils import extract_deep_face_embedding

_embedding_cache = {}


def get_case_deep_embedding(case_id: str, raw_mesh_json: str) -> np.ndarray:
    """
    Extract or retrieve cached 128-D SFace Deep Convolutional Embedding for a case/sighting.
    Uses the saved photo at ./resources/{case_id}.jpg and MediaPipe landmarks for alignment.
    """
    if case_id in _embedding_cache:
        return _embedding_cache[case_id]

    img_path = f"./resources/{case_id}.jpg"
    if os.path.exists(img_path):
        img = cv2.imread(img_path)
        if img is not None:
            try:
                raw_landmarks = json.loads(raw_mesh_json)
                feat = extract_deep_face_embedding(img, raw_landmarks)
                _embedding_cache[case_id] = feat
                return feat
            except Exception:
                pass

    # Fallback to normalized landmarks if image cannot be read
    raw_landmarks = json.loads(raw_mesh_json)
    arr = np.array(raw_landmarks, dtype=float).reshape(-1, 3)
    arr = arr - arr[4]
    d = np.linalg.norm(arr[33] - arr[263])
    if d > 1e-6:
        arr = arr / d
    fallback = arr.flatten()[:128]
    if len(fallback) < 128:
        fallback = np.pad(fallback, (0, 128 - len(fallback)))
    fallback = fallback / (np.linalg.norm(fallback) + 1e-8)
    _embedding_cache[case_id] = fallback
    return fallback


def match(sim_threshold: float = 0.45):
    """
    System-wide KNN matching using 128-D Deep Feature Embeddings.
    """
    matched_images = defaultdict(list)
    try:
        from sqlmodel import Session, select
        from pages.helper.db_queries import engine
        from pages.helper.data_models import RegisteredCases, PublicSubmissions

        with Session(engine) as session:
            regs = session.exec(select(RegisteredCases)).all()
            pubs = session.exec(select(PublicSubmissions)).all()

            if not regs or not pubs:
                return {"status": False, "message": "No registered cases or public submissions found."}

            reg_embeddings = [get_case_deep_embedding(r.id, r.face_mesh) for r in regs]
            pub_embeddings = [get_case_deep_embedding(p.id, p.face_mesh) for p in pubs]

            X = np.array(reg_embeddings)
            knn = NearestNeighbors(n_neighbors=1, metric="cosine", algorithm="brute")
            knn.fit(X)

            for p_idx, p_emb in enumerate(pub_embeddings):
                distances, indices = knn.kneighbors([p_emb])
                cos_dist = float(distances[0][0])
                cos_sim = 1.0 - cos_dist
                pred_idx = indices[0][0]

                if cos_sim >= sim_threshold:
                    reg_id = regs[pred_idx].id
                    pub_id = pubs[p_idx].id
                    matched_images[reg_id].append((pub_id, cos_dist))

        return {"status": True, "result": matched_images}
    except Exception as e:
        traceback.print_exc()
        return {"status": False, "message": str(e)}


def match_uploaded_face(
    query_emb: np.ndarray,
    distance_threshold: float = 0.55,
    compare_target: str = "all",
    exclude_id: str = None,
) -> dict:
    """
    Match an arbitrary 128-D query face embedding against all registered missing persons
    and citizen sightings in the database using OpenCV SFace CNN + scikit-learn KNN (Cosine metric).
    """
    from sqlmodel import Session, select
    from pages.helper.db_queries import engine
    from pages.helper.data_models import RegisteredCases, PublicSubmissions

    try:
        with Session(engine) as session:
            candidate_records = []

            # 1. Citizen Public Sightings
            if compare_target in ("sightings", "all"):
                public_sightings = session.exec(select(PublicSubmissions)).all()
                for pub in public_sightings:
                    if exclude_id and pub.id == exclude_id:
                        continue
                    candidate_records.append({
                        "id": pub.id,
                        "face_mesh": pub.face_mesh,
                        "type": "Public Sighting",
                        "title": f"Citizen Sighting ({pub.submitted_by or 'Anonymous'})",
                        "name": pub.submitted_by or "Citizen Sighting",
                        "case_number": f"SIGHTING-{pub.id[:8].upper()}",
                        "submitted_by": pub.submitted_by or "Anonymous Citizen",
                        "location": pub.location or "Unknown Location",
                        "mobile": pub.mobile or "N/A",
                        "email": pub.email or "N/A",
                        "birth_marks": pub.birth_marks or "None reported",
                        "submitted_on": str(pub.submitted_on)[:19] if pub.submitted_on else "N/A",
                        "status": pub.status,
                        "age": "N/A",
                        "gender": "N/A",
                        "height": "N/A",
                        "city": "",
                    })

            # 2. Registered Department Missing Cases
            if compare_target in ("registered_cases", "all"):
                query = select(RegisteredCases)
                if exclude_id:
                    query = query.where(RegisteredCases.id != exclude_id)
                other_cases = session.exec(query).all()
                for c in other_cases:
                    c_num = c.case_number or f"CASE-{c.id[:8].upper()}"
                    c_loc = f"{c.last_seen}, {c.city}" if c.city else (c.last_seen or "Unknown Location")
                    candidate_records.append({
                        "id": c.id,
                        "face_mesh": c.face_mesh,
                        "type": "Registered Case",
                        "title": f"Missing Report: {c.name} ({c_num})",
                        "name": c.name,
                        "case_number": c_num,
                        "submitted_by": f"Officer {c.submitted_by} / Complainant {c.complainant_name or 'N/A'}",
                        "location": c_loc,
                        "mobile": c.complainant_mobile or "N/A",
                        "email": c.complainant_email or "N/A",
                        "birth_marks": c.birth_marks or "None reported",
                        "submitted_on": str(c.submitted_on)[:19] if c.submitted_on else "N/A",
                        "status": c.status,
                        "age": c.age or "N/A",
                        "gender": c.gender or "Not Specified",
                        "height": c.height or "N/A",
                        "city": c.city or "",
                        "complainant_name": c.complainant_name or "N/A",
                    })

            if not candidate_records:
                return {
                    "status": True,
                    "matches": [],
                    "all_evaluated": [],
                    "nearest_rejected": None,
                    "total_checked": 0,
                    "threshold_used": distance_threshold,
                    "message": "No candidates found in the database to compare against.",
                }

            sighting_vectors = []
            valid_candidates = []
            for cand in candidate_records:
                try:
                    c_emb = get_case_deep_embedding(cand["id"], cand["face_mesh"])
                    sighting_vectors.append(c_emb)
                    valid_candidates.append(cand)
                except Exception:
                    continue

            if not sighting_vectors:
                return {
                    "status": True,
                    "matches": [],
                    "all_evaluated": [],
                    "nearest_rejected": None,
                    "total_checked": 0,
                    "threshold_used": distance_threshold,
                    "message": "No valid facial embeddings could be extracted from database candidates.",
                }

            # Fit scikit-learn NearestNeighbors with Cosine Metric on 128-D Deep Vectors
            X = np.array(sighting_vectors)
            k_neighbors = min(len(sighting_vectors), 10)
            knn = NearestNeighbors(n_neighbors=k_neighbors, metric="cosine", algorithm="brute")
            knn.fit(X)

            distances, indices = knn.kneighbors([query_emb])
            distances = distances[0]
            indices = indices[0]

            matches = []
            all_evaluated = []
            nearest_rejected = None

            for dist, idx in zip(distances, indices):
                cand = valid_candidates[idx]
                cos_dist = float(dist)
                cos_sim = float(1.0 - cos_dist)

                # Match criteria: Cosine distance <= threshold (similarity >= 1 - threshold)
                is_match = cos_dist <= distance_threshold

                # Calibrated Confidence:
                # Similarity >= 0.45: 75% to 100%
                # Similarity < 0.45: < 45% (rejected)
                if is_match:
                    confidence = round(
                        min(100.0, max(75.0, 75.0 + ((cos_sim - 0.45) / 0.55) * 25.0)), 1
                    )
                else:
                    confidence = round(max(0.0, cos_sim * 60.0), 1)

                candidate_info = {
                    "id": cand["id"],
                    "sighting_id": cand["id"],
                    "candidate_type": cand["type"],
                    "title": cand["title"],
                    "name": cand["name"],
                    "case_number": cand["case_number"],
                    "distance": round(cos_dist, 4),
                    "similarity": round(cos_sim, 4),
                    "confidence": confidence,
                    "location": cand["location"],
                    "submitted_by": cand["submitted_by"],
                    "mobile": cand["mobile"],
                    "email": cand["email"],
                    "birth_marks": cand["birth_marks"],
                    "submitted_on": cand["submitted_on"],
                    "status": cand["status"],
                    "age": cand.get("age", "N/A"),
                    "gender": cand.get("gender", "N/A"),
                    "height": cand.get("height", "N/A"),
                    "city": cand.get("city", ""),
                    "is_match": is_match,
                }

                all_evaluated.append(candidate_info)

                if is_match:
                    matches.append(candidate_info)
                elif nearest_rejected is None:
                    nearest_rejected = candidate_info

            return {
                "status": True,
                "matches": matches,
                "all_evaluated": all_evaluated,
                "nearest_rejected": nearest_rejected,
                "total_checked": len(valid_candidates),
                "threshold_used": distance_threshold,
                "model_name": "OpenCV SFace Deep CNN (128-D) + scikit-learn KNN (Cosine Metric)",
            }
    except Exception as e:
        traceback.print_exc()
        return {"status": False, "message": str(e)}


def match_single_case(
    target_case_id: str,
    distance_threshold: float = 0.55,
    compare_target: str = "all",
):
    """
    Wrapper for single case comparison against the database.
    """
    from sqlmodel import Session, select
    from pages.helper.db_queries import engine
    from pages.helper.data_models import RegisteredCases

    try:
        with Session(engine) as session:
            target = session.exec(
                select(RegisteredCases).where(RegisteredCases.id == target_case_id)
            ).first()

            if not target:
                return {"status": False, "message": "Target case not found in database."}

            try:
                target_emb = get_case_deep_embedding(target.id, target.face_mesh)
            except Exception as e:
                return {"status": False, "message": f"Corrupt facial data for case: {e}"}

        res = match_uploaded_face(
            query_emb=target_emb,
            distance_threshold=distance_threshold,
            compare_target=compare_target,
            exclude_id=target_case_id,
        )
        res["target_case"] = target
        return res
    except Exception as e:
        traceback.print_exc()
        return {"status": False, "message": str(e)}


if __name__ == "__main__":
    result = match()
    print(result)
