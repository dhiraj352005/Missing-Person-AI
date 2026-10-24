import streamlit as st
import pandas as pd
import os

from pages.helper import db_queries, emailer
from pages.helper.ui_theme import inject_custom_theme, render_sidebar_profile, render_page_header

PAGE_SIZE = 10


def _reset_page(key: str):
    """Reset pagination when filters change."""
    st.session_state[key] = 0


def case_viewer(case, is_owner: bool = True):
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
                <span class="officer-badge">Officer: {submitted_by}</span>
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
            st.caption("No matching citizen sightings linked yet.")

    # Action Toolbar
    act_col1, act_col2 = st.columns([1, 1])
    with act_col1:
        if status == "F":
            if st.button("📧 Send Complainant Notification Email", key=f"my_email_{case_id}"):
                case_detail_rows = db_queries.get_registered_case_detail(case_id)
                if case_detail_rows:
                    sent = emailer.send_match_notification(case_id, case_detail_rows[0])
                    if sent:
                        complainant_email = case_detail_rows[0][2] if len(case_detail_rows[0]) > 2 else None
                        st.success(f"✅ Notification email dispatched to {complainant_email or 'complainant'}.")
                    else:
                        st.warning("⚠️ Email could not be sent. Check SMTP credentials.")

    with act_col2:
        with st.expander("✏️ Edit or Delete Case"):
            with st.form(key=f"my_edit_{case_id}"):
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
                key=f"my_del_confirm_{case_id}",
            )
            if st.button("🗑️ Delete Case Record", key=f"my_del_{case_id}"):
                if confirm:
                    db_queries.delete_registered_case(case_id)
                    st.success("Case record deleted!")
                    st.rerun()
                else:
                    st.warning("Please tick the confirmation checkbox first.")

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


# ── Page Controller ───────────────────────────────────────────────────────────
st.set_page_config(page_title="Cases Submitted by Me", page_icon="📋", layout="wide")

inject_custom_theme()
render_sidebar_profile()

if "login_status" not in st.session_state or not st.session_state["login_status"]:
    st.warning("🔒 Please sign in from the Home page to view your registered cases.")
else:
    user = st.session_state["user"]

    render_page_header(
        "Cases Submitted by Me",
        f"Manage and track missing person investigations registered under officer account: {user}",
        icon="📋",
    )

    # Filter Bar Card
    with st.container():
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 20px 8px 20px; margin-bottom: 16px;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                    🔍 Case Search &amp; Filtering
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        filter_col, search_col, date_col = st.columns([2, 3, 2])

        status = filter_col.selectbox(
            "Filter by Status",
            options=["All", "Not Found", "Found"],
            on_change=_reset_page,
            args=("page_my_cases",),
        )

        search_name = search_col.text_input(
            "Search by Name or Case ID",
            placeholder="Type name or case number...",
            on_change=_reset_page,
            args=("page_my_cases",),
        )

        date_filter = date_col.date_input("Filter by Date (On or after)", value=None)

    st.write("")

    cases_data = list(db_queries.fetch_registered_cases(user, status, view_all=False))

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
                .where(RegisteredCases.submitted_by == user)
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

    # Metrics Summary Row & Export Button
    if cases_data:
        exp_col1, exp_col2 = st.columns([3, 1])
        with exp_col1:
            st.caption(f"Showing **{len(cases_data)}** matching case file(s)")
        with exp_col2:
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
                "📥 Export to CSV",
                data=df.to_csv(index=False),
                file_name=f"my_cases_{user}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    if not cases_data:
        st.info("No cases found matching your search and filter criteria. Click 'Register New Case' to create one!")
    else:
        paginated, render_controls = paginate(cases_data, "page_my_cases")
        for case in paginated:
            case_viewer(case, is_owner=True)
        render_controls()
