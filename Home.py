import os
import streamlit as st

from pages.helper import db_queries, auth
from pages.helper.ui_theme import inject_custom_theme, render_sidebar_profile, render_page_header

# Page config
st.set_page_config(
    page_title="Missing Person Identification System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject modern Light Dashboard Theme
inject_custom_theme()

# Initialise SQLite tables and seed default MongoDB Atlas admin user
db_queries.create_db()
auth.ensure_default_users()

if "login_status" not in st.session_state:
    st.session_state["login_status"] = False

# Render Sidebar Branding & Profile
render_sidebar_profile()

# ── LOGIN / SIGN-UP SCREEN ────────────────────────────────────────────────────
if not st.session_state.get("login_status"):
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem 1rem 1rem 1rem; max-width: 650px; margin: 0 auto;">
            <div style="display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px; background: linear-gradient(135deg, #2563EB, #0F766E); border-radius: 18px; color: white; font-size: 2rem; box-shadow: 0 4px 12px rgba(37,99,235,0.25); margin-bottom: 12px;">
                🔍
            </div>
            <h1 style="font-size: 2.1rem; font-weight: 800; color: #0F172A; margin: 0 0 6px 0; letter-spacing: -0.5px;">
                Missing Person Identification System
            </h1>
            <p style="font-size: 1rem; color: #64748B; margin: 0 0 20px 0;">
                Officer &amp; Investigation Portal — Cloud Biometric Matching
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.8, 1])

    with col2:
        tab_login, tab_signup = st.tabs(["🔐 Officer Sign In", "📝 New Officer Registration"])

        # ── TAB 1: LOGIN ──
        with tab_login:
            with st.form("login_form"):
                st.markdown("#### Sign In to Portal")
                login_username = st.text_input("Username", placeholder="e.g. rajesh").strip()
                login_password = st.text_input("Password", type="password")
                btn_login = st.form_submit_button("Sign In", use_container_width=True, type="primary")

                if btn_login:
                    if not login_username or not login_password:
                        st.error("Please enter both username and password.")
                    else:
                        with st.spinner("Verifying with Argon2id & MongoDB Atlas..."):
                            success, msg, user_doc, jwt_token = auth.authenticate_user(
                                login_username, login_password
                            )

                        if success and user_doc:
                            st.session_state["login_status"] = True
                            st.session_state["username"] = user_doc["username"]
                            st.session_state["user"] = user_doc["username"]
                            st.session_state["role"] = user_doc.get("role", "Officer")
                            st.session_state["jwt_token"] = jwt_token
                            st.session_state["user_info"] = {
                                "name": user_doc.get("name", user_doc["username"]),
                                "email": user_doc.get("email", ""),
                                "city": user_doc.get("city", "Pune"),
                                "area": user_doc.get("area", ""),
                                "role": user_doc.get("role", "Officer"),
                            }
                            st.success(f"✅ Welcome back, Officer {user_doc.get('name')}!")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

        # ── TAB 2: SIGN UP ──
        with tab_signup:
            with st.form("signup_form"):
                st.markdown("#### Officer & Admin Account Setup")
                new_name = st.text_input("Full Name *", placeholder="e.g. Rajesh Kumar")
                new_username = st.text_input("Choose Username *", placeholder="e.g. rajesh").strip().lower()
                new_email = st.text_input("Official Email", placeholder="e.g. rajesh@police.gov.in")
                c_city, c_area = st.columns(2)
                with c_city:
                    new_city = st.text_input("City Jurisdiction *", value="Pune")
                with c_area:
                    new_area = st.text_input("Police Station / Division", placeholder="e.g. Shivajinagar")
                new_role = st.selectbox("Role *", options=["Officer", "Admin"], index=0)
                new_pw = st.text_input("Create Password *", type="password")
                new_pw_confirm = st.text_input("Confirm Password *", type="password")

                btn_signup = st.form_submit_button("Register Account in MongoDB", use_container_width=True)

                if btn_signup:
                    if not new_name.strip() or not new_username or not new_city.strip() or not new_pw:
                        st.error("Please fill in all required fields (*).")
                    elif new_pw != new_pw_confirm:
                        st.error("Passwords do not match!")
                    elif len(new_pw) < 4:
                        st.error("Password must be at least 4 characters long.")
                    else:
                        with st.spinner("Hashing with Argon2id and storing in MongoDB Atlas..."):
                            ok, msg, created_doc = auth.register_user(
                                username=new_username,
                                name=new_name.strip(),
                                email=new_email.strip(),
                                password=new_pw,
                                city=new_city.strip(),
                                area=new_area.strip(),
                                role=new_role,
                            )
                        if ok:
                            st.success("✅ Account created successfully in MongoDB Atlas! Switch to Sign In tab.")
                        else:
                            st.error(f"❌ {msg}")

# ── POST-LOGIN DASHBOARD ──────────────────────────────────────────────────────
else:
    user_info = st.session_state.get(
        "user_info",
        {
            "name": st.session_state.get("username", "Officer"),
            "role": st.session_state.get("role", "Officer"),
            "city": "Pune",
            "area": "",
        },
    )
    role = st.session_state.get("role", "Officer")
    officer_name = user_info.get("name", "Officer")
    station_str = f"{user_info.get('area')}, {user_info.get('city')}" if user_info.get("area") else user_info.get("city", "Jurisdiction")

    # Clean Welcome Header
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(15,23,42,0.04);">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                <div>
                    <div style="font-size: 0.85rem; font-weight: 600; color: #2563EB; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px;">
                        Investigation Command Dashboard
                    </div>
                    <h2 style="font-size: 1.75rem; font-weight: 800; color: #0F172A; margin: 0;">
                        Welcome back, {officer_name}
                    </h2>
                    <div style="font-size: 0.9rem; color: #64748B; margin-top: 4px;">
                        📍 Assigned Division: <b>{station_str}</b> &nbsp;|&nbsp; 🛡️ Access Level: <b>{role}</b>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="background-color: #DCFCE7; color: #166534; border: 1px solid #BBF7D0; padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600;">
                        ● System Online
                    </span>
                    <span style="background-color: #EFF6FF; color: #1D4ED8; border: 1px solid #DBEAFE; padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600;">
                        AI SFace CNN Active
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Database Statistics ───────────────────────────────────────────────────
    total_found = len(db_queries.get_registered_cases_count(None, "F"))
    total_non_found = len(db_queries.get_registered_cases_count(None, "NF"))
    my_found = len(db_queries.get_registered_cases_count(st.session_state["user"], "F"))
    my_non_found = len(db_queries.get_registered_cases_count(st.session_state["user"], "NF"))
    total_cases = total_found + total_non_found

    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    col_m1.metric("Total Case Files", total_cases)
    col_m2.metric("Department Resolved", total_found)
    col_m3.metric("Department Open Cases", total_non_found)
    col_m4.metric("My Resolved Cases", my_found)
    col_m5.metric("My Open Cases", my_non_found)

    st.write("")

    # ── Quick Action Tiles ────────────────────────────────────────────────────
    st.markdown("### ⚡ Quick Actions")
    qa_col1, qa_col2, qa_col3, qa_col4 = st.columns(4)

    with qa_col1:
        st.markdown(
            """
            <div class="action-card">
                <div class="action-icon">📝</div>
                <div class="action-title">Register Case</div>
                <div class="action-desc">Add a new missing person report with photo &amp; AI landmark mesh</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with qa_col2:
        st.markdown(
            """
            <div class="action-card">
                <div class="action-icon">🎯</div>
                <div class="action-title">Match Cases</div>
                <div class="action-desc">Run SFace CNN + KNN matching against citizen photo/video sightings</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with qa_col3:
        st.markdown(
            """
            <div class="action-card">
                <div class="action-icon">🗺️</div>
                <div class="action-title">Geographic Map</div>
                <div class="action-desc">Explore nationwide case density on interactive Mapbox India</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with qa_col4:
        st.markdown(
            """
            <div class="action-card">
                <div class="action-icon">📂</div>
                <div class="action-title">Case Directory</div>
                <div class="action-desc">Browse, search, filter, and export department case reports</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("---")

    # ── Recent Cases Preview ──────────────────────────────────────────────────
    all_cases_list = list(db_queries.fetch_registered_cases(st.session_state["user"], status="All", view_all=True))
    if all_cases_list:
        st.markdown("### 🕒 Recent Registered Reports")
        recent_cases = all_cases_list[:3]

        rc_cols = st.columns(len(recent_cases))
        for idx, c in enumerate(recent_cases):
            # c: [id, name, age, status, last_seen, submitted_by, matched_with, case_number, gender, height, last_seen_datetime, city]
            c_id = c[0]
            c_name = c[1]
            c_age = c[2]
            c_status = c[3]
            c_loc = c[4]
            c_no = c[7] if len(c) > 7 and c[7] else f"CASE-{c_id[:8].upper()}"
            c_gender = c[8] if len(c) > 8 and c[8] else "N/A"
            c_city = c[11] if len(c) > 11 and c[11] else ""
            loc_full = f"{c_loc}, {c_city}" if c_city else c_loc

            status_badge = (
                '<span class="status-badge-found">✅ Found</span>'
                if c_status == "F"
                else '<span class="status-badge-missing">🔴 Open</span>'
            )

            with rc_cols[idx]:
                st.markdown(
                    f"""
                    <div class="modern-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span class="case-id-badge">{c_no}</span>
                            {status_badge}
                        </div>
                        <h4 style="margin: 0 0 6px 0; color: #0F172A; font-weight: 700;">{c_name}</h4>
                        <div style="font-size: 0.85rem; color: #64748B; line-height: 1.5;">
                            • <b>Age/Gender:</b> {c_age} yrs, {c_gender}<br>
                            • <b>Location:</b> {loc_full}<br>
                            • <b>Officer:</b> {c[5]}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.write("---")

    # ── Cases by City Map ─────────────────────────────────────────────────────
    st.subheader("Cases by City — India Intelligence Map")

    try:
        import folium
        from streamlit_folium import st_folium
        import importlib
        from pages.helper import utils
        importlib.reload(utils)
        from pages.helper.utils import create_base_map, add_city_case_markers

        CITY_COORDS = {
            "Delhi": (28.6139, 77.2090),
            "New Delhi": (28.6139, 77.2090),
            "Mumbai": (19.0760, 72.8777),
            "Bengaluru": (12.9716, 77.5946),
            "Bangalore": (12.9716, 77.5946),
            "Hyderabad": (17.3850, 78.4867),
            "Chennai": (13.0827, 80.2707),
            "Kolkata": (22.5726, 88.3639),
            "Pune": (18.5204, 73.8567),
            "Ahmedabad": (23.0225, 72.5714),
            "Jaipur": (26.9124, 75.7873),
            "Lucknow": (26.8467, 80.9462),
            "Kanpur": (26.4499, 80.3319),
            "Nagpur": (21.1458, 79.0882),
            "Indore": (22.7196, 75.8577),
            "Bhopal": (23.2599, 77.4126),
            "Visakhapatnam": (17.6868, 83.2185),
            "Patna": (25.5941, 85.1376),
            "Vadodara": (22.3072, 73.1812),
            "Surat": (21.1702, 72.8311),
            "Noida": (28.5355, 77.3910),
            "Gurgaon": (28.4595, 77.0266),
            "Gurugram": (28.4595, 77.0266),
            "Chandigarh": (30.7333, 76.7794),
            "Coimbatore": (11.0168, 76.9558),
            "Kochi": (9.9312, 76.2673),
            "Agra": (27.1767, 78.0081),
            "Varanasi": (25.3176, 82.9739),
            "Meerut": (28.9845, 77.7064),
            "Raipur": (21.2514, 81.6296),
            "Ranchi": (23.3441, 85.3096),
            "Guwahati": (26.1445, 91.7362),
            "Jodhpur": (26.2389, 73.0243),
            "Amritsar": (31.6340, 74.8723),
            "Faridabad": (28.4089, 77.3178),
            "Allahabad": (25.4358, 81.8463),
            "Prayagraj": (25.4358, 81.8463),
            "Unknown": (20.5937, 78.9629),
        }

        counts = db_queries.get_case_counts_by_city()

        if not counts:
            st.info("No cases with city data yet. Add a city when registering cases.")
        else:
            mb_token = st.session_state.get("mapbox_token", os.environ.get("MAPBOX_TOKEN", ""))

            m = create_base_map(
                location=[22.8, 79.2],
                zoom_start=5,
                mapbox_token=mb_token,
                style="Vibrant Streets (Colorful India)",
            )

            add_city_case_markers(m, counts, CITY_COORDS)
            st_folium(m, width="100%", height=460, returned_objects=[])

            # Modern Badge Legend
            st.markdown(
                """
                <div style="display: flex; gap: 14px; flex-wrap: wrap; align-items: center; margin-top: 8px; font-size: 0.9rem;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="display: inline-block; width: 14px; height: 14px; background: #e53935; border: 2px solid #ffcdd2; border-radius: 50%; box-shadow: 0 0 6px rgba(229,57,53,0.5);"></span>
                        <b>Active Hotspot</b> (Unresolved Cases)
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="display: inline-block; width: 14px; height: 14px; background: #2e7d32; border: 2px solid #c8e6c9; border-radius: 50%; box-shadow: 0 0 6px rgba(46,125,50,0.5);"></span>
                        <b>Safe Zone</b> (All Cases Safely Located)
                    </div>
                    <div style="color: #64748B; font-size: 0.82rem;">
                        • Click or hover over markers for live statistics
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    except ImportError:
        st.info("Install `folium` and `streamlit-folium` to enable the map.")
