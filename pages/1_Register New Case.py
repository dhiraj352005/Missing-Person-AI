import os
import uuid
import json
import random
import string
from datetime import datetime, date, time

import streamlit as st

from pages.helper.data_models import RegisteredCases
from pages.helper import db_queries
from pages.helper.utils import image_obj_to_numpy, detect_all_faces, draw_face_boxes
from pages.helper.ui_theme import inject_custom_theme, render_sidebar_profile, render_page_header

st.set_page_config(page_title="Register New Case", page_icon="📝", layout="wide")

# Apply modern Light Theme & Sidebar
inject_custom_theme()
render_sidebar_profile()

if "login_status" not in st.session_state or not st.session_state["login_status"]:
    st.warning("🔒 Please sign in from the Home page to register case reports.")
else:
    user = st.session_state["user"]

    render_page_header(
        "Register New Missing Person Case",
        "Upload a verified photograph and register missing person biometric landmarks and complainant records",
        icon="📝",
    )

    image_col, form_col = st.columns([1, 1.35], gap="large")
    save_flag = 0
    registered_case_number = None

    # ── PHOTO UPLOAD & AI FACE VALIDATION ─────────────────────────────────────
    with image_col:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(15,23,42,0.04);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <h3 style="margin: 0; font-size: 1.15rem; color: #0F172A; font-weight: 700;">📸 1. Missing Person Photo</h3>
                    <span style="background: #EFF6FF; color: #1D4ED8; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 700;">REQUIRED</span>
                </div>
                <p style="font-size: 0.85rem; color: #64748B; margin: 0 0 12px 0;">
                    High-accuracy MediaPipe 468-point 3D landmark detection and SFace 128-D CNN embedding are extracted automatically.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        image_obj = st.file_uploader(
            "Select Photo (JPG, JPEG, PNG) *",
            type=["jpg", "jpeg", "png"],
            key="new_case_photo_uploader",
        )

        faces = []
        selected_face_idx = None
        unique_id = None
        image_numpy = None

        if image_obj:
            file_key = f"{image_obj.name}_{image_obj.size}"

            if st.session_state.get("nc_file_key") != file_key:
                unique_id = str(uuid.uuid4())
                uploaded_file_path = f"./resources/{unique_id}.jpg"

                with open(uploaded_file_path, "wb") as f:
                    f.write(image_obj.read())
                image_obj.seek(0)

                with st.spinner("🔍 Running MediaPipe AI Face Landmark Validation..."):
                    image_numpy = image_obj_to_numpy(image_obj)
                    detected_faces = detect_all_faces(image_numpy, max_faces=5)

                if not detected_faces:
                    if os.path.exists(uploaded_file_path):
                        os.remove(uploaded_file_path)
                    st.session_state["nc_file_key"] = file_key
                    st.session_state["nc_faces"] = []
                    st.session_state["nc_image_numpy"] = None
                    st.session_state["nc_unique_id"] = None
                    st.session_state["nc_uploaded_path"] = None
                else:
                    st.session_state["nc_file_key"] = file_key
                    st.session_state["nc_faces"] = detected_faces
                    st.session_state["nc_image_numpy"] = image_numpy
                    st.session_state["nc_unique_id"] = unique_id
                    st.session_state["nc_uploaded_path"] = uploaded_file_path

            faces = st.session_state.get("nc_faces", [])
            image_numpy = st.session_state.get("nc_image_numpy")
            unique_id = st.session_state.get("nc_unique_id")

            if not faces:
                st.error(
                    "❌ **Face Validation Failed**: No human face detected in this image.\n\n"
                    "• Ensure the face is clearly visible, upright, and front-facing.\n"
                    "• Avoid heavy motion blur, dark shadows, or extreme angles."
                )
            elif len(faces) == 1:
                annotated = draw_face_boxes(image_numpy, faces, selected_idx=0)
                st.image(annotated, use_container_width=True)
                st.markdown(
                    """
                    <div style="background-color: #DCFCE7; color: #166534; border: 1px solid #BBF7D0; border-radius: 8px; padding: 10px 14px; font-weight: 600; font-size: 0.9rem; margin-top: 8px;">
                        ✅ <b>AI Landmark Mesh Ready:</b> 1 human face detected and validated.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                selected_face_idx = 0
            else:
                st.warning(f"⚠️ **{len(faces)} faces detected.** Please select which person to register:")
                options = [f"Face {i + 1}" for i in range(len(faces))]
                choice = st.radio("Select target person:", options, horizontal=True, key="nc_face_choice_radio")
                selected_face_idx = options.index(choice)
                annotated = draw_face_boxes(image_numpy, faces, selected_idx=selected_face_idx)
                st.image(annotated, use_container_width=True)
                st.info(f"Using **Face {selected_face_idx + 1}** for facial landmark registration.")
        else:
            st.info("👈 Please upload a clear photo of the missing person to activate registration.")

    # ── REGISTRATION FORM ─────────────────────────────────────────────────────
    with form_col:
        with st.form(key="register_missing_person_form"):
            st.markdown(
                """
                <div style="border-bottom: 2px solid #E2E8F0; padding-bottom: 8px; margin-bottom: 16px;">
                    <h3 style="margin: 0; font-size: 1.2rem; color: #0F172A; font-weight: 700;">
                        👤 Missing Person Profile
                    </h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

            c_name, c_age = st.columns([2, 1])
            with c_name:
                name = st.text_input("Full Name *", placeholder="e.g. Ramesh Kumar").strip()
            with c_age:
                age = st.number_input("Age (Years) *", min_value=1, max_value=120, value=25, step=1)

            c_gender, c_height = st.columns(2)
            with c_gender:
                gender = st.selectbox("Gender *", options=["Male", "Female", "Other"])
            with c_height:
                height = st.text_input("Height (optional)", placeholder="e.g. 5 ft 8 in / 172 cm").strip()

            birthmarks = st.text_input("Birthmarks / Scars / Identifying Features (optional)", placeholder="e.g. Mole on right cheek, scar on forehead").strip()

            c_city, c_location = st.columns(2)
            with c_city:
                city = st.text_input("Last Seen City *", placeholder="e.g. Pune").strip()
            with c_location:
                last_seen_loc = st.text_input("Last Seen Area / Landmark *", placeholder="e.g. Akurdi Railway Station").strip()

            c_date, c_time = st.columns(2)
            with c_date:
                ls_date = st.date_input("Last Seen Date *", value=date.today())
            with c_time:
                ls_time = st.time_input("Last Seen Time *", value=time(12, 0))

            last_seen_datetime_str = f"{ls_date.strftime('%Y-%m-%d')} at {ls_time.strftime('%I:%M %p')}"

            description = st.text_area(
                "Physical Description & Remarks (optional)",
                placeholder="Clothing worn when last seen, languages spoken, mental/physical condition, etc.",
            ).strip()

            st.markdown(
                """
                <div style="border-bottom: 2px solid #E2E8F0; padding-bottom: 8px; margin-top: 24px; margin-bottom: 16px;">
                    <h3 style="margin: 0; font-size: 1.2rem; color: #0F172A; font-weight: 700;">
                        📞 Complainant &amp; Contact Details
                    </h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

            c_cname, c_cphone = st.columns(2)
            with c_cname:
                complainant_name = st.text_input("Complainant Name *", placeholder="e.g. Suresh Kumar (Father)").strip()
            with c_cphone:
                complainant_phone = st.text_input("Phone Number * (10 digits)", placeholder="e.g. 9876543210").strip()

            complainant_email = st.text_input("Complainant Email (optional - for automated match alerts)", placeholder="e.g. complainant@example.com").strip()

            st.write("")
            submit_btn = st.form_submit_button("🚀 Submit & Save Case Record", type="primary", use_container_width=True)

            if submit_btn:
                errors = []

                if not image_obj:
                    errors.append("❌ Photo is required: Please upload a photo of the missing person.")
                elif not faces or selected_face_idx is None:
                    errors.append("❌ Face validation failed: At least one clear face must be detected in the photo.")

                if not name:
                    errors.append("❌ Full Name is required.")
                if not city:
                    errors.append("❌ Last Seen City is required.")
                if not last_seen_loc:
                    errors.append("❌ Last Seen Location / Landmark is required.")
                if not complainant_name:
                    errors.append("❌ Complainant Name is required.")
                if not complainant_phone:
                    errors.append("❌ Complainant Phone Number is required.")
                elif not complainant_phone.isdigit() or len(complainant_phone) != 10:
                    errors.append("❌ Complainant Phone Number must be exactly 10 digits.")

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    rand_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    registered_case_number = f"MP-{datetime.now().year}-{rand_id}"

                    selected_landmarks = faces[selected_face_idx]["landmarks"]

                    new_case = RegisteredCases(
                        id=unique_id,
                        case_number=registered_case_number,
                        submitted_by=user,
                        name=name,
                        father_name="",
                        age=str(age),
                        gender=gender,
                        height=height if height else None,
                        complainant_name=complainant_name,
                        complainant_mobile=complainant_phone,
                        complainant_email=complainant_email if complainant_email else None,
                        adhaar_card="",
                        last_seen=last_seen_loc,
                        last_seen_datetime=last_seen_datetime_str,
                        address=f"{last_seen_loc}, {city}",
                        city=city,
                        description=description if description else None,
                        face_mesh=json.dumps(selected_landmarks),
                        status="NF",
                        birth_marks=birthmarks if birthmarks else None,
                        matched_with="",
                    )

                    db_queries.register_new_case(new_case)
                    save_flag = 1

    # ── SUCCESS CONFIRMATION MODAL / BANNER ───────────────────────────────────
    if save_flag == 1 and registered_case_number:
        st.balloons()
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 2px solid #22C55E; border-radius: 12px; padding: 24px; margin-top: 24px; box-shadow: 0 4px 12px rgba(34, 197, 94, 0.1);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                    <h3 style="color: #166534; margin: 0; font-size: 1.4rem;">
                        🎉 Case File Successfully Registered
                    </h3>
                    <span style="background: #DCFCE7; color: #166534; border: 1px solid #BBF7D0; padding: 4px 14px; border-radius: 20px; font-weight: 700; font-size: 0.9rem;">
                        {registered_case_number}
                    </span>
                </div>
                <div style="font-size: 0.95rem; color: #334155; line-height: 1.6;">
                    • <b>Missing Person:</b> {name} (Age: {age}, {gender})<br>
                    • <b>Last Known Location:</b> {last_seen_loc}, {city} on {last_seen_datetime_str}<br>
                    • <b>Complainant:</b> {complainant_name} ({complainant_phone})<br>
                    • <b>Security &amp; Sync:</b> Record stored in local SQLite and synchronized to <b>MongoDB Atlas Cloud</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for k in ["nc_file_key", "nc_faces", "nc_image_numpy", "nc_unique_id", "nc_uploaded_path"]:
            st.session_state.pop(k, None)
