import streamlit as st
import pandas as pd
import os
import cv2
import numpy as np

from pages.helper import db_queries, emailer, match_algo
from pages.helper.ui_theme import inject_custom_theme, render_sidebar_profile, render_page_header
from pages.helper.utils import (
    image_obj_to_numpy,
    detect_all_faces,
    draw_face_boxes,
    extract_deep_face_embedding,
)

PAGE_SIZE = 10


def _reset_page(key: str):
    """Reset pagination when filters change."""
    st.session_state[key] = 0


# ── Case viewers ─────────────────────────────────────────────────────────────

def case_viewer(case, is_admin: bool = False, current_user: str = ""):
    case = list(case)
    case_id = str(case[0])
    name = case[1]
    age = case[2]
    status = case[3]
    last_seen_loc = case[4]
    submitted_by = case[5]
    matched_with_id = (case[6] or "").replace("{", "").replace("}", "").strip() if len(case) > 6 else ""
    case_number = case[7] if len(case) > 7 and case[7] else f"CASE-{str(case_id)[:8].upper()}"
    gender = case[8] if len(case) > 8 and case[8] else "Not Specified"
    height = case[9] if len(case) > 9 and case[9] else "N/A"
    last_seen_dt = case[10] if len(case) > 10 and case[10] else "N/A"
    city = case[11] if len(case) > 11 and case[11] else ""

    matched_with_details = None
    if matched_with_id:
        matched_with_details = db_queries.get_public_case_detail(matched_with_id)

    status_label = "✅ Found" if status == "F" else "🔴 Open (Not Found)"
    status_class = "status-badge-found" if status == "F" else "status-badge-missing"
    loc_display = f"{last_seen_loc}, {city}" if city else last_seen_loc

    # Case Card Container
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(15,23,42,0.04);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="case-id-badge">{case_number}</span>
                    <span class="{status_class}">{status_label}</span>
                </div>
                <span class="officer-badge">Registered By: {submitted_by}</span>
            </div>
            <h3 style="margin: 0 0 12px 0; color: #0F172A; font-size: 1.3rem; font-weight: 700;">{name}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    card_c1, card_c2, card_c3 = st.columns([1, 2.5, 2])

    with card_c1:
        img_path = f"./resources/{case_id}.jpg"
        if os.path.exists(img_path):
            st.image(img_path, width=130, use_container_width=False)
        else:
            st.caption("No registered photo")

    with card_c2:
        st.markdown(
            f"""
            <div style="font-size: 0.9rem; color: #334155; line-height: 1.6;">
                • <b>Age &amp; Gender:</b> {age} years &nbsp;|&nbsp; {gender}<br>
                • <b>Height:</b> {height}<br>
                • <b>Last Known Location:</b> {loc_display}<br>
                • <b>Last Seen Date &amp; Time:</b> {last_seen_dt}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with card_c3:
        if matched_with_details:
            st.markdown(
                f"""
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; padding: 10px 14px; border-radius: 8px;">
                    <div style="font-weight: 700; color: #166534; font-size: 0.88rem; margin-bottom: 4px;">
                        📍 Verified Citizen Sighting
                    </div>
                    <div style="font-size: 0.8rem; color: #14532D; line-height: 1.4;">
                        • <b>Location:</b> {matched_with_details[0][0]}<br>
                        • <b>Submitted By:</b> {matched_with_details[0][1]}<br>
                        • <b>Phone:</b> {matched_with_details[0][2]}<br>
                        • <b>Notes:</b> {matched_with_details[0][3] or 'None'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.caption("No verified citizen sightings linked yet.")

    # Admin or Case Owner can send notification email
    can_manage = is_admin or (current_user and current_user == submitted_by)
    act_col1, act_col2 = st.columns([1, 1])

    with act_col1:
        if can_manage and status == "F":
            if st.button("📧 Send Complainant Notification Email", key=f"email_{case_id}"):
                case_detail_rows = db_queries.get_registered_case_detail(case_id)
                if case_detail_rows:
                    sent = emailer.send_match_notification(case_id, case_detail_rows[0])
                    if sent:
                        complainant_email = case_detail_rows[0][2] if len(case_detail_rows[0]) > 2 else None
                        st.success(f"✅ Notification email sent to {complainant_email or 'complainant'}.")
                    else:
                        st.warning("⚠️ Email could not be sent. Check SMTP configuration.")

    with act_col2:
        if can_manage:
            with st.expander("✏️ Edit or Delete Record"):
                with st.form(key=f"edit_{case_id}"):
                    new_name = st.text_input("Name", value=name)
                    new_last_seen = st.text_input("Last Seen Area", value=last_seen_loc)
                    save_btn = st.form_submit_button("💾 Save Record Changes", type="primary")
                    if save_btn:
                        db_queries.update_registered_case(
                            case_id, {"name": new_name, "last_seen": new_last_seen}
                        )
                        st.success("Case updated successfully!")
                        st.rerun()

                confirm = st.checkbox(
                    "Confirm permanent removal from database",
                    key=f"del_confirm_{case_id}",
                )
                if st.button("🗑️ Delete Case File", key=f"del_{case_id}"):
                    if confirm:
                        db_queries.delete_registered_case(case_id)
                        st.success("Case record deleted!")
                        st.rerun()
                    else:
                        st.warning("Please tick the confirmation checkbox first.")

    st.write("---")


def public_case_viewer(case: list) -> None:
    case = list(case)
    case_id = str(case.pop(0))

    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 20px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(15,23,42,0.04);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span class="case-id-badge">SIGHTING-{case_id[:8].upper()}</span>
                <span class="officer-badge">Public Citizen Submission</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    data_col, image_col = st.columns([3, 1])

    with data_col:
        for label, value in zip(
            ["Status", "Location", "Mobile", "Birth Marks", "Submitted on", "Submitted by"],
            case,
        ):
            if label == "Status":
                value = "Found" if value == "F" else "Not Found"
            st.markdown(f"• **{label}:** {value}")

    with image_col:
        img_path = f"./resources/{case_id}.jpg"
        if os.path.exists(img_path):
            st.image(img_path, width=130, use_container_width=False)
        else:
            st.caption("No image preview")

    st.write("---")


def paginate(items: list, page_key: str):
    """Return the current page slice and render Prev / Next controls."""
    total = len(items)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = st.session_state.get(page_key, 0)
    page = max(0, min(page, total_pages - 1))
    st.session_state[page_key] = page

    paginated = items[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]

    def render_controls():
        col_prev, col_info, col_next = st.columns([1, 3, 1])
        if col_prev.button("◀ Previous Page", disabled=page == 0, key=f"{page_key}_prev"):
            st.session_state[page_key] = page - 1
            st.rerun()
        col_info.markdown(
            f"<div style='text-align:center; padding-top:6px; font-weight:600; color:#64748B;'>Page {page + 1} of {total_pages} &nbsp;·&nbsp; {total} record(s)</div>",
            unsafe_allow_html=True,
        )
        if col_next.button("Next Page ▶", disabled=page >= total_pages - 1, key=f"{page_key}_next"):
            st.session_state[page_key] = page + 1
            st.rerun()

    return paginated, render_controls


# ── Main page ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="All Cases", page_icon="🌐", layout="wide")

inject_custom_theme()
render_sidebar_profile()

render_page_header(
    "All Cases (System-Wide Directory)",
    "Browse, filter, and inspect missing person reports and citizen sightings registered across all departments",
    icon="🌐",
)

if True:

    # ── TOP SECTION: DIRECT PHOTO VERIFICATION ("UPLOAD AND CHECK") ──────────
    with st.container():
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, #F0F7FF 0%, #F5F3FF 50%, #ECFDF5 100%); border: 1.5px solid #BFDBFE; border-radius: 14px; padding: 18px 22px; margin-bottom: 20px; box-shadow: 0 4px 16px rgba(37,99,235,0.06);">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; background: linear-gradient(135deg, #2563EB, #1D4ED8); border-radius: 12px; color: white; font-size: 1.4rem; box-shadow: 0 2px 8px rgba(37,99,235,0.25);">
                            📷
                        </div>
                        <div>
                            <h3 style="margin: 0; color: #0F172A; font-size: 1.25rem; font-weight: 800; letter-spacing: -0.3px;">
                                Direct Photo Verification — Upload &amp; Check Database
                            </h3>
                            <p style="margin: 3px 0 0 0; color: #475569; font-size: 0.9rem;">
                                Upload any person's photo to instantly check if they exist in our missing persons database or citizen sightings.
                            </p>
                        </div>
                    </div>
                    <span style="background: #DBEAFE; color: #1E40AF; padding: 4px 12px; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; border: 1px solid #BFDBFE;">
                        ⚡ Instant AI Biometric Match
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_upload, col_action = st.columns([1.2, 1.8], gap="large")

        with col_upload:
            uploaded_verify_file = st.file_uploader(
                "Upload photo to verify against database:",
                type=["jpg", "jpeg", "png"],
                key="verify_photo_upload_input",
                help="Upload a portrait photo to check for biometric matches across all database records.",
            )

        with col_action:
            if uploaded_verify_file is not None:
                scope_choice = st.radio(
                    "Compare against database records:",
                    options=[
                        "All Sources (Missing Reports & Citizen Sightings)",
                        "Registered Missing Cases Only",
                        "Citizen Sightings Only",
                    ],
                    index=0,
                    horizontal=True,
                    key="verify_scope_radio",
                )
            else:
                st.markdown(
                    """
                    <div style="background: #FFFFFF; border: 1px dashed #CBD5E1; border-radius: 10px; padding: 22px; text-align: center; color: #64748B;">
                        <div style="font-size: 1.8rem; margin-bottom: 6px;">🖼️</div>
                        <div style="font-weight: 600; font-size: 0.95rem; color: #334155;">Upload a photo to begin instant verification</div>
                        <div style="font-size: 0.85rem; margin-top: 4px;">The AI model will detect the facial mesh and compare it across all database records.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        if uploaded_verify_file is not None:
            # Check if file changed to reset verification flag
            curr_filename = getattr(uploaded_verify_file, "name", "")
            if st.session_state.get("last_verified_photo_name") != curr_filename:
                st.session_state["last_verified_photo_name"] = curr_filename
                st.session_state["ran_photo_verification"] = False

            # Read and detect face
            image_numpy = image_obj_to_numpy(uploaded_verify_file)
            faces = detect_all_faces(image_numpy, max_faces=5)

            if not faces:
                st.error("❌ No human face detected in the uploaded photo. Please upload a clear photo with a visible face.")
            else:
                selected_face_idx = 0
                if len(faces) > 1:
                    st.info(f"Detected {len(faces)} faces in image. Please choose the face you want to verify:")
                    selected_face_idx = st.selectbox(
                        "Target Face to Check:",
                        options=list(range(len(faces))),
                        format_func=lambda i: f"Face #{i + 1}",
                        key="verify_face_selector",
                    )

                preview_img = draw_face_boxes(image_numpy, faces, selected_idx=selected_face_idx)

                # Show preview & verification button
                preview_c, btn_c = st.columns([1, 2], gap="medium")
                with preview_c:
                    st.image(preview_img, caption="Detected Face Preview", width=180)

                with btn_c:
                    st.markdown(
                        f"""
                        <div style="font-size: 0.9rem; color: #334155; margin-bottom: 12px; line-height: 1.5;">
                            • <b>Face Detected:</b> 468 landmark mesh extracted<br>
                            • <b>Feature Extractor:</b> OpenCV SFace 128-D Deep CNN<br>
                            • <b>Matching Engine:</b> scikit-learn k-NN (Cosine Metric, cutoff d &le; 0.55)
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    btn_verify = st.button(
                        "🔍 Check Database for This Person",
                        type="primary",
                        use_container_width=True,
                        key="btn_run_direct_verify",
                    )

                if btn_verify or st.session_state.get("ran_photo_verification"):
                    st.session_state["ran_photo_verification"] = True

                    target_scope = "all"
                    if "Missing Cases Only" in scope_choice:
                        target_scope = "registered_cases"
                    elif "Citizen Sightings Only" in scope_choice:
                        target_scope = "sightings"

                    with st.spinner("Analyzing biometric embedding and matching against database..."):
                        img_bgr = cv2.cvtColor(image_numpy, cv2.COLOR_RGB2BGR)
                        query_emb = extract_deep_face_embedding(img_bgr, faces[selected_face_idx]["landmarks"])
                        verify_res = match_algo.match_uploaded_face(
                            query_emb=query_emb,
                            distance_threshold=0.55,
                            compare_target=target_scope,
                        )

                    if not verify_res.get("status"):
                        st.error(f"❌ {verify_res.get('message', 'Matching error occurred.')}")
                    else:
                        matches = verify_res.get("matches", [])
                        total_checked = verify_res.get("total_checked", 0)
                        nearest_rejected = verify_res.get("nearest_rejected")

                        if matches:
                            st.markdown(
                                f"""
                                <div style="background: #F0FDF4; border: 1.5px solid #86EFAC; border-left: 6px solid #16A34A; border-radius: 12px; padding: 18px 22px; margin: 18px 0; box-shadow: 0 2px 10px rgba(22,163,74,0.08);">
                                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                                        <h4 style="margin: 0; color: #15803D; font-size: 1.25rem; font-weight: 800;">
                                            🎯 MATCH CONFIRMED: Found {len(matches)} Matching Person(s) in Database!
                                        </h4>
                                        <span style="background: #DCFCE7; color: #166534; font-weight: 700; font-size: 0.85rem; padding: 4px 12px; border-radius: 9999px;">
                                            Verified by AI Facial Recognition
                                        </span>
                                    </div>
                                    <p style="margin: 6px 0 0 0; color: #166534; font-size: 0.92rem;">
                                        The uploaded photo matches existing records in the database with high biometric similarity.
                                    </p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                            for idx, match in enumerate(matches):
                                m_id = match["id"]
                                m_name = match.get("name", "Unknown")
                                m_case_num = match.get("case_number", f"CASE-{m_id[:8].upper()}")
                                m_type = match.get("candidate_type", "Database Record")
                                m_conf = match.get("confidence", 0.0)
                                m_sim = match.get("similarity", 0.0)
                                m_loc = match.get("location", "Unknown Location")
                                m_status = match.get("status", "NF")
                                m_status_label = "✅ Found" if m_status == "F" else "🔴 Open (Not Found)"
                                m_status_cls = "status-badge-found" if m_status == "F" else "status-badge-missing"
                                m_sub_by = match.get("submitted_by", "N/A")
                                m_age = match.get("age", "N/A")
                                m_gender = match.get("gender", "N/A")
                                m_mobile = match.get("mobile", "N/A")

                                st.markdown(
                                    f"""
                                    <div style="background: #FFFFFF; border: 1.5px solid #22C55E; border-radius: 12px; padding: 18px 20px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(34,197,94,0.1);">
                                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                                            <div style="display: flex; align-items: center; gap: 10px;">
                                                <span class="case-id-badge">{m_case_num}</span>
                                                <span class="{m_status_cls}">{m_status_label}</span>
                                                <span style="background: #EFF6FF; color: #1D4ED8; font-size: 0.8rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">{m_type}</span>
                                            </div>
                                            <span style="background: #DCFCE7; color: #15803D; font-weight: 800; font-size: 0.95rem; padding: 4px 12px; border-radius: 8px; border: 1px solid #86EFAC;">
                                                Biometric Confidence: {m_conf}%
                                            </span>
                                        </div>
                                        <h3 style="margin: 0 0 10px 0; color: #0F172A; font-size: 1.3rem; font-weight: 800;">{m_name}</h3>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                                res_c1, res_c2, res_c3 = st.columns([1, 2.5, 2])
                                with res_c1:
                                    img_file = f"./resources/{m_id}.jpg"
                                    if os.path.exists(img_file):
                                        st.image(img_file, caption=f"DB Photo: {m_name}", width=130)
                                    else:
                                        st.caption("No image on file")

                                with res_c2:
                                    st.markdown(
                                        f"""
                                        <div style="font-size: 0.9rem; color: #334155; line-height: 1.6;">
                                            • <b>Age &amp; Gender:</b> {m_age} years &nbsp;|&nbsp; {m_gender}<br>
                                            • <b>Last Known Location:</b> {m_loc}<br>
                                            • <b>Registered By:</b> {m_sub_by}<br>
                                            • <b>Contact:</b> {m_mobile}
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                with res_c3:
                                    st.markdown(
                                        f"""
                                        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px 14px; border-radius: 8px;">
                                            <div style="font-weight: 700; color: #0F172A; font-size: 0.88rem; margin-bottom: 6px;">
                                                📊 AI Biometric Verification Metrics
                                            </div>
                                            <div style="font-size: 0.82rem; color: #475569; line-height: 1.5;">
                                                • <b>Cosine Similarity:</b> <code>{m_sim}</code><br>
                                                • <b>Cosine Distance:</b> <code>{match.get('distance', 'N/A')}</code><br>
                                                • <b>Threshold Cutoff:</b> <code>d &le; 0.55</code><br>
                                                • <b>Verification:</b> <span style="color:#15803D; font-weight:700;">PASSED</span>
                                            </div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )
                                st.write("---")

                        else:
                            rej_dist = nearest_rejected["distance"] if nearest_rejected else "N/A"
                            rej_sim = nearest_rejected.get("similarity", "N/A") if nearest_rejected else "N/A"
                            rej_title = nearest_rejected.get("title", "None") if nearest_rejected else "None"

                            st.markdown(
                                f"""
                                <div style="background-color: #FFF1F2; border: 1.5px solid #FECDD3; border-left: 6px solid #E11D48; padding: 18px 22px; border-radius: 12px; margin: 18px 0; box-shadow: 0 2px 10px rgba(225,29,72,0.06);">
                                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                                        <h4 style="color: #9F1239; margin: 0; font-size: 1.2rem; font-weight: 800;">
                                            ℹ️ NO MATCH FOUND IN DATABASE
                                        </h4>
                                        <span style="background: #FFE4E6; color: #9F1239; font-weight: 700; font-size: 0.85rem; padding: 4px 12px; border-radius: 9999px;">
                                            Different Individual
                                        </span>
                                    </div>
                                    <p style="margin: 8px 0; color: #4C0519; font-size: 0.95rem;">
                                        This individual does <b>not match</b> any registered missing person case or citizen sighting in the database.
                                    </p>
                                    <div style="background: white; border: 1px solid #FFE4E6; border-radius: 8px; padding: 12px 16px; margin-top: 10px; font-size: 0.9rem; color: #334155; line-height: 1.6;">
                                        • <b>Total Candidates Evaluated:</b> {total_checked} record(s)<br>
                                        • <b>Closest Database Candidate:</b> {rej_title}<br>
                                        • <b>Measured Cosine Similarity:</b> <code>{rej_sim}</code> (Distance: <code>{rej_dist}</code>)<br>
                                        • <b>Required Match Threshold:</b> Similarity <code>&ge; 0.45</code> (Distance <code>&le; 0.55</code>)<br>
                                        • <b>Conclusion:</b> Similarity score is below threshold. Verified as a different individual.
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

        st.markdown("<hr style='margin: 24px 0 20px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

    is_logged_in = st.session_state.get("login_status", False)
    if not is_logged_in:
        st.info("🔒 **Officer / Admin Directory Access:** You are currently in public direct verification mode. To browse the complete department case directory, edit cases, or send email alerts, please sign in from the **Home** page.")
        st.stop()

    user = st.session_state.get("user", "")
    is_admin = st.session_state.get("role", "").lower() == "admin"

    # Filter Bar Card
    with st.container():
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 20px 8px 20px; margin-bottom: 16px;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                    🔍 System-Wide Case Directory Filters
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        filter_col, search_col, date_col = st.columns([2, 3, 2])

        status = filter_col.selectbox(
            "Filter by Category",
            options=["All", "Not Found", "Found", "Public Cases"],
            on_change=_reset_page,
            args=("page_all_cases",),
        )

        search_name = search_col.text_input(
            "Search by Name or Keyword",
            placeholder="Search across all records...",
            on_change=_reset_page,
            args=("page_all_cases",),
        )

        date_filter = date_col.date_input("Filter by Date (On or after)", value=None)

    st.write("")

    # ── Public Cases view ────────────────────────────────────────────────────
    if status == "Public Cases":
        cases_data = list(db_queries.fetch_public_cases(False, status))

        if search_name:
            cases_data = [
                c for c in cases_data if search_name.lower() in str(c).lower()
            ]

        if date_filter:
            cases_data = [
                c for c in cases_data if c[5] and str(c[5])[:10] >= str(date_filter)
            ]

        if cases_data:
            exp_c1, exp_c2 = st.columns([3, 1])
            with exp_c1:
                st.caption(f"Showing **{len(cases_data)}** public citizen sighting(s)")
            with exp_c2:
                df = pd.DataFrame(
                    cases_data,
                    columns=[
                        "ID",
                        "Status",
                        "Location",
                        "Mobile",
                        "Birth Marks",
                        "Submitted On",
                        "Submitted By",
                    ],
                )
                df["Status"] = (
                    df["Status"].map({"F": "Found", "NF": "Not Found"}).fillna(df["Status"])
                )
                st.download_button(
                    "📥 Export Public Cases (CSV)",
                    data=df.to_csv(index=False),
                    file_name="public_cases.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        if not cases_data:
            st.info("No public sightings found matching your filter criteria.")
        else:
            paginated, render_controls = paginate(cases_data, "page_pub_all")
            for case in paginated:
                public_case_viewer(case)
            render_controls()

    # ── Registered Cases view (Department-Wide) ───────────────────────────────
    else:
        cases_data = list(db_queries.fetch_registered_cases(user, status, view_all=True))

        if search_name:
            cases_data = [
                c for c in cases_data
                if search_name.lower() in str(c[1]).lower() or (len(c) > 7 and c[7] and search_name.lower() in str(c[7]).lower())
            ]

        if date_filter:
            from sqlmodel import Session, select
            from pages.helper.db_queries import engine
            from pages.helper.data_models import RegisteredCases
            import datetime

            date_dt = datetime.datetime.combine(date_filter, datetime.time.min)
            with Session(engine) as session:
                q = (
                    select(
                        RegisteredCases.id,
                        RegisteredCases.name,
                        RegisteredCases.age,
                        RegisteredCases.status,
                        RegisteredCases.last_seen,
                        RegisteredCases.submitted_by,
                        RegisteredCases.matched_with,
                        RegisteredCases.case_number,
                        RegisteredCases.gender,
                        RegisteredCases.height,
                        RegisteredCases.last_seen_datetime,
                        RegisteredCases.city,
                    )
                    .where(RegisteredCases.submitted_on >= date_dt)
                )
                if status != "All":
                    status_filter = "F" if status == "Found" else "NF"
                    q = q.where(RegisteredCases.status == status_filter)
                cases_data = list(session.exec(q).all())

            if search_name:
                cases_data = [
                    c for c in cases_data
                    if search_name.lower() in str(c[1]).lower() or (len(c) > 7 and c[7] and search_name.lower() in str(c[7]).lower())
                ]

        if cases_data:
            exp_c1, exp_c2 = st.columns([3, 1])
            with exp_c1:
                st.caption(f"Showing **{len(cases_data)}** department case file(s)")
            with exp_c2:
                df_rows = []
                for c in cases_data:
                    df_rows.append({
                        "Case ID": c[7] if len(c) > 7 and c[7] else str(c[0]),
                        "Name": c[1],
                        "Age": c[2],
                        "Gender": c[8] if len(c) > 8 and c[8] else "N/A",
                        "Height": c[9] if len(c) > 9 and c[9] else "N/A",
                        "Status": "Found" if c[3] == "F" else "Not Found",
                        "Last Seen City": c[11] if len(c) > 11 and c[11] else "",
                        "Last Seen Location": c[4],
                        "Last Seen Date & Time": c[10] if len(c) > 10 and c[10] else "N/A",
                        "Registered By": c[5],
                        "Matched Sighting ID": c[6] if len(c) > 6 else "",
                    })
                df = pd.DataFrame(df_rows)
                st.download_button(
                    "📥 Export All Cases (CSV)",
                    data=df.to_csv(index=False),
                    file_name="all_registered_cases.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        if not cases_data:
            st.info("No registered cases found in the system archives.")
        else:
            paginated, render_controls = paginate(cases_data, "page_all_cases")
            for case in paginated:
                case_viewer(case, is_admin=is_admin, current_user=user)
            render_controls()
