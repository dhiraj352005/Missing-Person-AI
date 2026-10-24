import streamlit as st
import os
import importlib

from pages.helper import db_queries, match_algo, emailer
from pages.helper.ui_theme import inject_custom_theme, render_sidebar_profile, render_page_header

importlib.reload(match_algo)

st.set_page_config(page_title="Match Cases & Sightings", page_icon="🎯", layout="wide")

inject_custom_theme()
render_sidebar_profile()

if "login_status" not in st.session_state or not st.session_state["login_status"]:
    st.warning("🔒 Please sign in from the Home page to perform biometric facial matching.")
else:
    user = st.session_state["user"]
    is_admin = st.session_state.get("role", "").lower() == "admin"

    render_page_header(
        "Biometric Case Matching & Sighting Verification",
        "Deep SFace CNN (128-D Feature Embedding) + scikit-learn k-NN (Cosine Metric) for automated identity verification",
        icon="🎯",
    )

    # ── STEP 1: Select Case Scope ─────────────────────────────────────────────
    with st.container():
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px 20px; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(15,23,42,0.04);">
                <div style="font-size: 0.85rem; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                    Step 1: Select Missing Person Investigation
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        scope_col, sel_col = st.columns([1, 2], gap="medium")

        with scope_col:
            scope = st.radio(
                "Filter Case Scope:",
                options=["My Registered Cases", "All Department Cases"],
                horizontal=False,
                key="match_scope_radio",
            )

        view_all = (scope == "All Department Cases")
        available_cases = list(db_queries.fetch_registered_cases(user, status="All", view_all=view_all))

        with sel_col:
            if not available_cases:
                st.info("No cases available in this view. Click 'Register New Case' in the sidebar to add one!")
                selected_case_id = None
            else:
                case_options = {}
                for c in available_cases:
                    status_label = "✅ Found" if c[3] == "F" else "🔴 Open"
                    case_no = c[7] if len(c) > 7 and c[7] else f"CASE-{c[0][:8].upper()}"
                    gender_str = f", {c[8]}" if len(c) > 8 and c[8] else ""
                    display_label = f"[{case_no}] {c[1]} (Age: {c[2]}{gender_str}, {c[4]}) — {status_label}"
                    case_options[display_label] = c

                selected_label = st.selectbox(
                    "Select Target Person to Evaluate:",
                    options=list(case_options.keys()),
                    key="case_picker",
                )
                selected_case = case_options[selected_label]
                selected_case_id = selected_case[0]

    # ── STEP 2: Display Selected Missing Person Details ───────────────────────
    if selected_case_id and available_cases:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px 20px; margin-top: 16px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(15,23,42,0.04);">
                <div style="font-size: 0.85rem; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">
                    Step 2: Missing Person Target Profile
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        prof_col1, prof_col2 = st.columns([1, 3], gap="medium")

        with prof_col1:
            img_path = f"./resources/{selected_case_id}.jpg"
            if os.path.exists(img_path):
                st.image(img_path, width=150, caption="Registered Biometric Photo")
            else:
                st.caption("No registered image")

        with prof_col2:
            case_no = selected_case[7] if len(selected_case) > 7 and selected_case[7] else f"CASE-{selected_case[0][:8].upper()}"
            gender_val = selected_case[8] if len(selected_case) > 8 and selected_case[8] else "N/A"
            height_val = selected_case[9] if len(selected_case) > 9 and selected_case[9] else "N/A"
            ls_datetime = selected_case[10] if len(selected_case) > 10 and selected_case[10] else "N/A"
            city_val = selected_case[11] if len(selected_case) > 11 and selected_case[11] else ""
            loc_val = f"{selected_case[4]}, {city_val}" if city_val else selected_case[4]
            status_str = "✅ Found" if selected_case[3] == "F" else "🔴 Open (Missing)"
            status_cls = "status-badge-found" if selected_case[3] == "F" else "status-badge-missing"

            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span class="case-id-badge">{case_no}</span>
                    <span class="{status_cls}">{status_str}</span>
                </div>
                <h3 style="margin: 0 0 10px 0; color: #0F172A; font-weight: 800; font-size: 1.4rem;">{selected_case[1]}</h3>
                """,
                unsafe_allow_html=True,
            )
            info_c1, info_c2 = st.columns(2)
            with info_c1:
                st.markdown(f"• **Age & Gender:** {selected_case[2]} years &nbsp;|&nbsp; {gender_val}")
                st.markdown(f"• **Height:** {height_val}")
                st.markdown(f"• **Last Seen Location:** {loc_val}")
            with info_c2:
                st.markdown(f"• **Last Seen Date & Time:** {ls_datetime}")
                st.markdown(f"• **Registered By Officer:** `{selected_case[5]}`")

        # ── STEP 3: ML Model Diagnostics & Threshold ─────────────────────────
        with st.expander("⚙️ ML Model Architecture & Cosine Biometric Threshold"):
            st.markdown(
                r"""
                **Hybrid Deep CNN + KNN Architecture:**
                1. **Face Alignment:** MediaPipe extracts 5 canonical facial anchors to warp the face into a standardized $112 \times 112$ canonical frame.
                2. **Deep Feature Extraction:** OpenCV **SFace Deep CNN** transforms the aligned face into an $L_2$-normalized **128-dimensional identity embedding vector**.
                3. **$k$-Nearest Neighbors ($k=1$, Cosine Metric):** Scikit-learn's `NearestNeighbors(metric="cosine")` measures the angular Cosine Distance:
                   $$d_{\text{cos}}(u, v) = 1 - \frac{u \cdot v}{\|u\|_2 \|v\|_2}$$
                4. **Decision Boundary:**
                   * $d_{\text{cos}} \le 0.55$ (Cosine Similarity $\ge 0.45$) $\implies$ **True Match** (75%–100% confidence).
                   * $d_{\text{cos}} > 0.55$ (Cosine Similarity $< 0.45$) $\implies$ **Rejected** (Different individuals, typically $d_{\text{cos}} \ge 0.75$).
                """
            )
            col_thresh, col_desc = st.columns([1, 2])
            with col_thresh:
                user_threshold = st.slider(
                    "Cosine Distance Cutoff (d):",
                    min_value=0.30,
                    max_value=0.75,
                    value=0.55,
                    step=0.05,
                    help="Default 0.55 (corresponds to Cosine Similarity >= 0.45). Same person typically achieves similarity 0.70 - 1.00.",
                )
            with col_desc:
                min_sim = round(1.0 - user_threshold, 2)
                st.caption(
                    f"Selected Cutoff: **d ≤ {user_threshold}** (Requires Cosine Similarity **≥ {min_sim}**). "
                    "This threshold eliminates false positives while identifying individuals despite hairstyle, facial hair, or lighting variations."
                )

        # ── STEP 4: Search Target Database Scope ─────────────────────────────
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px 20px; margin-top: 16px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(15,23,42,0.04);">
                <div style="font-size: 0.85rem; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                    Step 3: Database Search Scope
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        pool_col1, pool_col2 = st.columns([1.2, 1], gap="medium")
        with pool_col1:
            search_pool = st.radio(
                "Compare Target Person Against:",
                options=[
                    "All Sources (Citizen Sightings & Other Missing Cases)",
                    "Citizen Public Sightings Only",
                    "Other Registered Missing Cases Only",
                ],
                index=0,
                key="search_pool_radio",
            )
        with pool_col2:
            st.caption(
                "💡 **Pro-tip:** 'All Sources' checks both citizen sightings uploaded from the mobile citizen app "
                "AND cross-checks other police department cases (detects aliases, duplicate filings, or photos taken at different times)."
            )

        if "All Sources" in search_pool:
            target_scope_mode = "all"
        elif "Citizen" in search_pool:
            target_scope_mode = "sightings"
        else:
            target_scope_mode = "registered_cases"

        # ── STEP 5: Action Button — Run KNN Classifier ────────────────────────
        st.write("")
        btn_match = st.button(
            f"🔍 Run SFace CNN + KNN Model: Check if {selected_case[1]} has a Match",
            type="primary",
            use_container_width=True,
        )

        if btn_match or st.session_state.get(f"ran_match_{selected_case_id}"):
            st.session_state[f"ran_match_{selected_case_id}"] = True

            with st.spinner(f"Running OpenCV SFace Deep CNN & scikit-learn KNN on {selected_case[1]}'s biometric vector..."):
                match_res = match_algo.match_single_case(
                    selected_case_id,
                    distance_threshold=user_threshold,
                    compare_target=target_scope_mode,
                )

            if not match_res["status"]:
                st.error(f"❌ {match_res['message']}")
            else:
                matches = match_res.get("matches", [])
                total_checked = match_res.get("total_checked", 0)
                nearest_rejected = match_res.get("nearest_rejected")

                if not matches:
                    st.warning(f"ℹ️ **No Match Found for {selected_case[1]}**")

                    rej_dist = nearest_rejected["distance"] if nearest_rejected else "N/A"
                    rej_sim = nearest_rejected.get("similarity", "N/A") if nearest_rejected else "N/A"
                    rej_sub = nearest_rejected["submitted_by"] if nearest_rejected else "None"
                    rej_title = nearest_rejected.get("title", rej_sub) if nearest_rejected else "None"
                    rej_loc = nearest_rejected["location"] if nearest_rejected else ""

                    st.markdown(
                        f"""
                        <div style="background-color: #FFF1F2; border: 1px solid #FECDD3; border-left: 5px solid #E11D48; padding: 18px 20px; border-radius: 10px; margin: 16px 0;">
                            <h4 style="color: #9F1239; margin-top: 0; font-size: 1.15rem;">🔬 KNN Classifier Result: Negative (Different Individuals)</h4>
                            <p style="margin: 4px 0; color: #4C0519; font-size: 0.95rem;">
                                The model compared <b>{selected_case[1]}</b>'s 128-D Deep CNN embedding against <b>{total_checked}</b> candidate record(s) in the selected pool.
                            </p>
                            <div style="background: white; border: 1px solid #FFE4E6; border-radius: 8px; padding: 12px; margin-top: 10px; font-size: 0.9rem; color: #334155; line-height: 1.6;">
                                • <b>Nearest Candidate Analyzed:</b> {rej_title} ({rej_loc})<br>
                                • <b>Measured Cosine Similarity:</b> <code>{rej_sim}</code> (Cosine Distance: <code>{rej_dist}</code>)<br>
                                • <b>Biometric Cutoff Required:</b> Cosine Similarity <code>&ge; {round(1.0 - user_threshold, 2)}</code> (Distance <code>&le; {user_threshold}</code>)<br>
                                • <b>Conclusion:</b> Similarity <code>{rej_sim}</code> is well below threshold. The KNN classifier correctly rejected this candidate as a <b>different individual</b>.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                else:
                    st.success(f"🎉 **Biometric Match Confirmed!** The Deep CNN + KNN model detected **{len(matches)}** verified match(es) for **{selected_case[1]}**!")

                    for idx, sighting in enumerate(matches):
                        cand_type = sighting.get("candidate_type", "Public Sighting")
                        badge_color = "#1D4ED8" if cand_type == "Registered Case" else "#15803D"
                        badge_bg = "#EFF6FF" if cand_type == "Registered Case" else "#F0FDF4"
                        badge_border = "#BFDBFE" if cand_type == "Registered Case" else "#BBF7D0"
                        s_title = sighting.get("title", f"Verified Sighting #{idx + 1}")

                        st.markdown(
                            f"""
                            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid {badge_color}; padding: 18px 20px; border-radius: 12px; margin-bottom: 16px; box-shadow: 0 2px 6px rgba(15,23,42,0.04);">
                                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                                    <h3 style="color: #0F172A; margin: 0; font-size: 1.25rem;">📍 {s_title}</h3>
                                    <span style="background-color: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border}; padding: 3px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: 700;">
                                        {cand_type}
                                    </span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        col_s_img, col_s_info = st.columns([1, 3], gap="medium")

                        with col_s_img:
                            s_img_path = f"./resources/{sighting['sighting_id']}.jpg"
                            if os.path.exists(s_img_path):
                                st.image(s_img_path, width=150, caption="Matched Photo")
                            else:
                                st.caption("No image preview")

                        with col_s_info:
                            conf = sighting["confidence"]
                            sim_pct = round(sighting["similarity"] * 100, 1)
                            st.markdown(
                                f"**AI Match Confidence:** `{conf}%` &nbsp;|&nbsp; "
                                f"**Cosine Similarity:** `{sim_pct}%` (`{sighting['similarity']}`) &nbsp;|&nbsp; "
                                f"**Cosine Distance:** `{sighting['distance']}` (Cutoff: `≤ {user_threshold}`)"
                            )
                            st.progress(conf / 100)

                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown(f"📍 **Location:** `{sighting['location']}`")
                                st.markdown(f"📅 **Date & Time:** `{sighting['submitted_on']}`")
                                st.markdown(f"🔍 **Identifying Features / Birth Marks:** {sighting['birth_marks']}")

                            with c2:
                                st.markdown("#### 📞 Contact / Case Record Info")
                                st.markdown(f"**Submitted By / Complainant:** **{sighting['submitted_by']}**")
                                if sighting["mobile"] and sighting["mobile"] != "N/A":
                                    st.markdown(
                                        f"""
                                        <div style="background-color: #EFF6FF; color: #1D4ED8; border: 1px solid #DBEAFE; padding: 6px 12px; border-radius: 8px; font-size: 0.95rem; font-weight: 700; margin: 4px 0;">
                                            📱 Mobile: <a href="tel:{sighting['mobile']}" style="color: #1D4ED8; text-decoration: underline;">{sighting['mobile']}</a>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )
                                if sighting["email"] and sighting["email"] != "N/A":
                                    st.markdown(f"✉️ **Email:** [{sighting['email']}](mailto:{sighting['email']})")

                            # Action: Confirm match & mark found
                            st.write("")
                            if selected_case[3] != "F":
                                btn_confirm = st.button(
                                    f"✅ Confirm Match & Mark {selected_case[1]} as FOUND",
                                    key=f"confirm_{selected_case_id}_{sighting['sighting_id']}",
                                    type="primary",
                                )
                                if btn_confirm:
                                    db_queries.update_found_status(selected_case_id, sighting["sighting_id"])
                                    case_detail_rows = db_queries.get_registered_case_detail(selected_case_id)
                                    if case_detail_rows:
                                        emailer.send_match_notification(selected_case_id, case_detail_rows[0])
                                    st.success(f"🎉 Success! {selected_case[1]} is now marked as FOUND and linked to {s_title}!")
                                    st.rerun()
                            else:
                                st.info("✅ This case is already confirmed and marked as **Found**.")

                        st.write("---")
