import os
import urllib.request

import cv2
import PIL
import PIL.ImageDraw
import PIL.ImageFont
import numpy as np
import streamlit as st
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

_MODEL_PATH = "face_landmarker.task"
_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)

_SFACE_MODEL_PATH = "face_recognition_sface_2021dec.onnx"
_SFACE_MODEL_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_recognition_sface/face_recognition_sface_2021dec.onnx"
)
_sface_recognizer = None


def _ensure_sface_model():
    if not os.path.exists(_SFACE_MODEL_PATH):
        urllib.request.urlretrieve(_SFACE_MODEL_URL, _SFACE_MODEL_PATH)


def get_sface_recognizer():
    global _sface_recognizer
    if _sface_recognizer is None:
        _ensure_sface_model()
        _sface_recognizer = cv2.FaceRecognizerSF.create(_SFACE_MODEL_PATH, "")
    return _sface_recognizer


def extract_deep_face_embedding(image: np.ndarray, raw_landmarks: list) -> np.ndarray:
    """
    Extract a normalized 128-dimensional deep feature embedding using OpenCV SFace CNN.
    Aligns the face using MediaPipe 5 primary keypoints and passes the 112x112 crop through SFace.
    """
    recognizer = get_sface_recognizer()
    img = image.copy()
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

    h, w = img.shape[:2]
    pts = np.array(raw_landmarks, dtype=float).reshape(-1, 3)
    xs = pts[:, 0] * w
    ys = pts[:, 1] * h

    xmin, xmax = float(np.clip(xs.min(), 0, w)), float(np.clip(xs.max(), 0, w))
    ymin, ymax = float(np.clip(ys.min(), 0, h)), float(np.clip(ys.max(), 0, h))
    bw = max(10.0, xmax - xmin)
    bh = max(10.0, ymax - ymin)

    # 5 Keypoints: Right eye (33), Left eye (263), Nose tip (1), Right mouth (61), Left mouth (291)
    re_x, re_y = float(xs[33]), float(ys[33])
    le_x, le_y = float(xs[263]), float(ys[263])
    nt_x, nt_y = float(xs[1]), float(ys[1])
    rm_x, rm_y = float(xs[61]), float(ys[61])
    lm_x, lm_y = float(xs[291]), float(ys[291])

    face_arr = np.array(
        [xmin, ymin, bw, bh, re_x, re_y, le_x, le_y, nt_x, nt_y, rm_x, rm_y, lm_x, lm_y, 0.99],
        dtype=np.float32,
    )
    aligned = recognizer.alignCrop(img, face_arr)
    feat = recognizer.feature(aligned).flatten()
    norm = np.linalg.norm(feat)
    if norm > 1e-6:
        feat = feat / norm
    return feat


def _ensure_model():
    if not os.path.exists(_MODEL_PATH):
        with st.spinner("Downloading face landmarker model (one-time, ~30 MB)..."):
            urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)


def _ensure_model_silent():
    if not os.path.exists(_MODEL_PATH):
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)


def _build_detector(num_faces: int = 5):
    base_options = mp_python.BaseOptions(model_asset_path=_MODEL_PATH)
    options = mp_vision.FaceLandmarkerOptions(
        base_options=base_options,
        num_faces=num_faces,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
    )
    return mp_vision.FaceLandmarker.create_from_options(options)


def _normalize_image(image: np.ndarray) -> np.ndarray:
    if image.dtype != np.uint8:
        image = image.astype(np.uint8)
    if image.ndim == 2:
        image = np.stack([image] * 3, axis=-1)
    elif image.shape[2] == 4:
        image = image[:, :, :3]
    return image


def image_obj_to_numpy(image_obj) -> np.ndarray:
    """Convert a Streamlit-uploaded image object to an RGB numpy array."""
    image = PIL.Image.open(image_obj).convert("RGB")
    return np.array(image)


def detect_all_faces(image: np.ndarray, max_faces: int = 5):
    """
    Detect up to max_faces in an image.

    Returns a list of dicts, one per detected face:
        {
            "landmarks": [x1,y1,z1, x2,y2,z2, ...],   # flattened, normalised
            "bbox": (x_min, y_min, x_max, y_max),      # pixel coords
        }
    Returns an empty list if no faces are found.
    """
    _ensure_model()
    image = _normalize_image(image)
    h, w = image.shape[:2]

    try:
        detector = _build_detector(num_faces=max_faces)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
        result = detector.detect(mp_image)
        detector.close()
    except Exception as e:
        st.error(f"❌ Face detection failed: {e}")
        return []

    faces = []
    for lm_list in result.face_landmarks:
        xs = [lm.x * w for lm in lm_list]
        ys = [lm.y * h for lm in lm_list]
        padding = 0.08 * max(w, h)
        bbox = (
            max(0, int(min(xs) - padding)),
            max(0, int(min(ys) - padding)),
            min(w, int(max(xs) + padding)),
            min(h, int(max(ys) + padding)),
        )
        landmarks_flat = [coord for lm in lm_list for coord in (lm.x, lm.y, lm.z)]
        faces.append({"landmarks": landmarks_flat, "bbox": bbox})
    return faces


# Distinct colours for up to 5 faces (unselected state)
_FACE_COLORS = [
    (255, 200, 0),  # yellow
    (0, 180, 255),  # cyan
    (255, 100, 0),  # orange
    (180, 0, 255),  # purple
    (255, 0, 150),  # pink
]
_SELECTED_COLOR = (50, 220, 80)  # green
_UNSELECTED_DIM = (160, 160, 160)  # grey when another face is selected


def draw_face_boxes(
    image_numpy: np.ndarray, faces: list, selected_idx: int = None
) -> PIL.Image.Image:
    """
    Draw labelled bounding boxes around detected faces.

    - Single face: one green box labelled "Face detected"
    - Multiple faces, nothing selected: each box gets a distinct colour + number
    - Multiple faces, one selected: selected = bright green, others = grey + number
    """
    img = PIL.Image.fromarray(_normalize_image(image_numpy))
    draw = PIL.ImageDraw.Draw(img)
    n = len(faces)

    for i, face in enumerate(faces):
        x0, y0, x1, y1 = face["bbox"]
        box_w = max(1, (x1 - x0) // 200 + 2)  # line width scales with box size

        if n == 1:
            color = _SELECTED_COLOR
            label = "Face detected"
        elif selected_idx is None:
            color = _FACE_COLORS[i % len(_FACE_COLORS)]
            label = f"Face {i + 1}"
        elif i == selected_idx:
            color = _SELECTED_COLOR
            label = f"Face {i + 1} (selected)"
        else:
            color = _UNSELECTED_DIM
            label = f"Face {i + 1}"

        # Draw rounded-corner-ish box with a slightly thicker outline
        for offset in range(box_w):
            draw.rectangle(
                [x0 - offset, y0 - offset, x1 + offset, y1 + offset],
                outline=color,
            )

        # Label background + text
        font_size = max(12, (y1 - y0) // 8)
        text_x, text_y = x0, max(0, y0 - font_size - 4)
        draw.rectangle(
            [
                text_x,
                text_y,
                text_x + len(label) * font_size // 2 + 8,
                text_y + font_size + 4,
            ],
            fill=color,
        )
        draw.text((text_x + 4, text_y + 2), label, fill=(0, 0, 0))

    return img


# ── Single-face helper (kept for mobile_app compatibility) ────────────────────


def extract_face_mesh_landmarks(image: np.ndarray):
    """
    Extract face mesh landmarks for exactly one face.
    Shows a Streamlit error if none found. Returns None on failure.
    """
    faces = detect_all_faces(image, max_faces=1)
    if not faces:
        st.error(
            "❌ No face detected in this image.\n\n"
            "**Tips for a better result:**\n"
            "- Ensure the face is clearly visible and not obscured\n"
            "- Use good lighting — avoid dark or back-lit photos\n"
            "- Use a front-facing photo where possible"
        )
        return None
    return faces[0]["landmarks"]


# ── Frame-level helper (video) ────────────────────────────────────────────────


def extract_face_mesh_from_frame(frame_rgb: np.ndarray):
    """Silent version for batch/video use. Returns landmarks or None."""
    _ensure_model_silent()
    frame_rgb = _normalize_image(frame_rgb)
    try:
        detector = _build_detector(num_faces=1)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result = detector.detect(mp_image)
        detector.close()
        if result.face_landmarks:
            lm_list = result.face_landmarks[0]
            return [coord for lm in lm_list for coord in (lm.x, lm.y, lm.z)]
        return None
    except Exception:
        return None


def _cosine_distance(a: list, b: list) -> float:
    a, b = np.array(a), np.array(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 1.0
    return 1.0 - float(np.dot(a, b) / denom)


def extract_unique_faces_from_video(
    video_path: str,
    frame_interval: int = 15,
    similarity_threshold: float = 0.05,
):
    """
    Extract unique face landmarks from a video file.
    Returns list of (landmarks, frame_rgb) tuples — one per unique face.
    """
    _ensure_model_silent()
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    unique_faces = []
    frame_idx = 0
    while True:
        ret, frame_bgr = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            landmarks = extract_face_mesh_from_frame(frame_rgb)
            if landmarks is not None:
                is_duplicate = any(
                    _cosine_distance(landmarks, ex_lm) < similarity_threshold
                    for ex_lm, _ in unique_faces
                )
                if not is_duplicate:
                    unique_faces.append((landmarks, frame_rgb))
        frame_idx += 1

    cap.release()
    return unique_faces


def create_base_map(
    location=[22.9734, 78.6569],
    zoom_start=5,
    mapbox_token: str = None,
    style: str = "streets",
):
    """
    Creates a Folium base map centered over India.
    Default style is vibrant colorful Mapbox Streets (streets-v12).
    Also supports Outdoors (rich terrain), Satellite, Dark, and Light.
    """
    import folium

    DEFAULT_MAPBOX_TOKEN = ""

    env_token = os.environ.get("MAPBOX_TOKEN")
    if not env_token and os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("MAPBOX_TOKEN="):
                        env_token = line.strip().split("=", 1)[1].strip("'\" ")
                        break
        except Exception:
            pass

    token = (
        mapbox_token
        or (st.session_state.get("mapbox_token") if "mapbox_token" in st.session_state else None)
        or env_token
        or DEFAULT_MAPBOX_TOKEN
    )
    if token and hasattr(token, "strip"):
        token = token.strip()

    if token:
        style_map = {
            "streets": "streets-v12",
            "outdoors": "outdoors-v12",
            "satellite": "satellite-streets-v12",
            "dark": "dark-v11",
            "light": "light-v11",
        }
        style_key = style.lower()
        if "outdoor" in style_key:
            style_id = "outdoors-v12"
        elif "satellit" in style_key:
            style_id = "satellite-streets-v12"
        elif "dark" in style_key:
            style_id = "dark-v11"
        elif "light" in style_key:
            style_id = "light-v11"
        else:
            style_id = "streets-v12"

        tiles_url = f"https://api.mapbox.com/styles/v1/mapbox/{style_id}/tiles/{{z}}/{{x}}/{{y}}?access_token={token}"
        m = folium.Map(location=location, zoom_start=zoom_start, tiles=None, control_scale=True)
        folium.TileLayer(
            tiles=tiles_url,
            attr="&copy; <a href='https://www.mapbox.com/about/maps/'>Mapbox</a> &copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a>",
            name=f"Mapbox ({style_id})",
            max_zoom=19,
        ).add_to(m)
    else:
        m = folium.Map(
            location=location,
            zoom_start=zoom_start,
            tiles="OpenStreetMap",
            control_scale=True,
        )
    return m


def add_city_case_markers(m, counts: dict, city_coords: dict):
    """
    Renders high-visibility, modern glowing biometric markers for each city.
    """
    import folium

    for city, data in counts.items():
        found = data.get("found", 0)
        not_found = data.get("not_found", 0)
        total = found + not_found
        if total <= 0:
            continue

        coords = city_coords.get(city)
        if coords is None:
            for key, val in city_coords.items():
                if key.lower() == city.lower():
                    coords = val
                    break
        if coords is None:
            continue

        has_unresolved = not_found > 0
        primary_color = "#e53935" if has_unresolved else "#2e7d32"
        fill_color = "#ff5252" if has_unresolved else "#4caf50"
        status_text = "🔴 Active Missing Cases" if has_unresolved else "🟢 All Cases Resolved"
        pct_resolved = round((found / total) * 100) if total > 0 else 0

        # Dynamic radius based on total cases
        glow_radius = max(16, min(48, 14 + total * 6))
        core_radius = max(8, min(24, 7 + total * 3))

        tooltip_html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; min-width: 170px; padding: 4px;">
            <div style="font-size: 1.05rem; font-weight: bold; color: #111; margin-bottom: 4px; border-bottom: 2px solid {primary_color}; padding-bottom: 2px;">
                📍 {city}
            </div>
            <div style="font-size: 0.85rem; font-weight: 600; color: {primary_color}; margin-bottom: 6px;">
                {status_text}
            </div>
            <div style="font-size: 0.82rem; color: #333; line-height: 1.4;">
                • <b>Total Cases:</b> {total}<br>
                • <span style="color: #c62828;"><b>Unresolved (Missing):</b> {not_found}</span><br>
                • <span style="color: #2e7d32;"><b>Resolved (Found):</b> {found}</span>
            </div>
            <div style="margin-top: 6px; background-color: #e0e0e0; border-radius: 4px; height: 6px; overflow: hidden;">
                <div style="background-color: #2e7d32; width: {pct_resolved}%; height: 100%;"></div>
            </div>
            <div style="font-size: 0.72rem; color: #666; text-align: right; margin-top: 2px;">
                {pct_resolved}% Resolved
            </div>
        </div>
        """

        # 1. Outer translucent pulsating aura
        folium.CircleMarker(
            location=coords,
            radius=glow_radius,
            color=primary_color,
            weight=1.5,
            fill=True,
            fill_color=fill_color,
            fill_opacity=0.22,
        ).add_to(m)

        # 2. Inner crisp core marker with rich tooltip and popup
        folium.CircleMarker(
            location=coords,
            radius=core_radius,
            color="#ffffff",
            weight=2.5,
            fill=True,
            fill_color=primary_color,
            fill_opacity=0.9,
            tooltip=folium.Tooltip(tooltip_html, sticky=True),
            popup=folium.Popup(tooltip_html, max_width=250),
        ).add_to(m)
