import os
import streamlit as st


def inject_custom_theme():
    """
    Injects a cohesive, modern Light Dashboard design system into Streamlit.
    Theme Palette:
      - Primary: #2563EB (Professional Blue)
      - Secondary: #0F766E (Teal)
      - Main Background: #F8FAFC (Slate Light Gray)
      - Card Background: #FFFFFF (Clean White)
      - Primary Text: #0F172A (Deep Navy)
      - Secondary Text: #64748B (Slate Gray)
      - Borders: #E2E8F0 (Subtle Border)
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* Base Typography & App Background */
        html, body, [class*="css"], .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            background-color: #F8FAFC !important;
            color: #0F172A !important;
        }

        /* Top Header & Toolbar clean up */
        header[data-testid="stHeader"] {
            background-color: rgba(248, 250, 252, 0.9) !important;
            backdrop-filter: blur(8px);
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E2E8F0 !important;
            box-shadow: 2px 0 8px rgba(15, 23, 42, 0.02) !important;
        }
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {
            color: #1E293B !important;
        }

        /* Navigation Links in Sidebar */
        [data-testid="stSidebarNav"] li div a {
            border-radius: 8px !important;
            margin: 2px 8px !important;
            padding: 8px 12px !important;
            font-weight: 500 !important;
            color: #475569 !important;
            transition: all 0.15s ease-in-out !important;
        }
        [data-testid="stSidebarNav"] li div a:hover {
            background-color: #F1F5F9 !important;
            color: #2563EB !important;
        }
        [data-testid="stSidebarNav"] li div a[aria-current="page"] {
            background-color: #EFF6FF !important;
            color: #2563EB !important;
            font-weight: 600 !important;
            border-left: 3px solid #2563EB !important;
        }

        /* Streamlit Metric Cards */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 12px !important;
            padding: 16px 20px !important;
            box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.04) !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        div[data-testid="stMetric"]:hover {
            box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.08) !important;
            transform: translateY(-1px);
        }
        div[data-testid="stMetric"] label {
            color: #64748B !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #0F172A !important;
            font-size: 1.85rem !important;
            font-weight: 700 !important;
        }

        /* Form Inputs & Selects */
        .stTextInput input, .stSelectbox select, .stTextArea textarea, .stDateInput input, .stTimeInput input {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 8px !important;
            font-size: 0.95rem !important;
            padding: 9px 12px !important;
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }
        .stTextInput input:focus, .stSelectbox select:focus, .stTextArea textarea:focus {
            border-color: #2563EB !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
        }
        .stTextInput label, .stSelectbox label, .stTextArea label, .stFileUploader label, .stRadio label {
            color: #334155 !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            margin-bottom: 4px !important;
        }

        /* Primary and Secondary Buttons */
        .stButton button[kind="primary"] {
            background-color: #2563EB !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 9px 18px !important;
            font-size: 0.95rem !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
            transition: all 0.15s ease;
        }
        .stButton button[kind="primary"]:hover {
            background-color: #1D4ED8 !important;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.25) !important;
            transform: translateY(-1px);
        }
        .stButton button[kind="secondary"] {
            background-color: #FFFFFF !important;
            color: #334155 !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            padding: 8px 16px !important;
            transition: all 0.15s ease;
        }
        .stButton button[kind="secondary"]:hover {
            background-color: #F8FAFC !important;
            border-color: #94A3B8 !important;
            color: #0F172A !important;
        }

        /* Expanders */
        div[data-testid="stExpander"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03) !important;
            margin-bottom: 12px !important;
        }
        div[data-testid="stExpander"] summary {
            color: #1E293B !important;
            font-weight: 600 !important;
        }

        /* Tabs */
        div[data-baseweb="tab-list"] {
            background-color: transparent !important;
            border-bottom: 2px solid #E2E8F0 !important;
            gap: 16px !important;
        }
        button[data-baseweb="tab"] {
            color: #64748B !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            padding: 10px 14px !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #2563EB !important;
            border-bottom: 2px solid #2563EB !important;
        }

        /* Custom Modern Card Classes */
        .modern-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.04);
            transition: box-shadow 0.2s ease, transform 0.2s ease;
        }
        .modern-card:hover {
            box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.08);
        }

        .status-badge-found {
            background-color: #DCFCE7;
            color: #166534;
            border: 1px solid #BBF7D0;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .status-badge-missing {
            background-color: #FEE2E2;
            color: #991B1B;
            border: 1px solid #FECACA;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .case-id-badge {
            background-color: #EFF6FF;
            color: #1D4ED8;
            border: 1px solid #DBEAFE;
            padding: 3px 8px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        .officer-badge {
            background-color: #F1F5F9;
            color: #475569;
            border: 1px solid #E2E8F0;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 500;
        }

        /* Page Headers */
        .page-header-container {
            margin-bottom: 20px;
            border-bottom: 1px solid #E2E8F0;
            padding-bottom: 16px;
        }
        .page-header-title {
            font-size: 1.85rem;
            font-weight: 800;
            color: #0F172A;
            margin: 0 0 6px 0;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .page-header-subtitle {
            font-size: 0.95rem;
            color: #64748B;
            margin: 0;
            font-weight: 400;
            line-height: 1.5;
        }

        /* Quick Action Card */
        .action-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
            transition: all 0.15s ease-in-out;
        }
        .action-card:hover {
            border-color: #2563EB;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.1);
        }
        .action-icon {
            font-size: 2rem;
            margin-bottom: 8px;
        }
        .action-title {
            font-weight: 600;
            color: #0F172A;
            font-size: 1rem;
            margin-bottom: 4px;
        }
        .action-desc {
            font-size: 0.8rem;
            color: #64748B;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str = "", icon: str = ""):
    """Renders a clean, modern page header."""
    icon_str = f"<span>{icon}</span> " if icon else ""
    subtitle_html = f'<p class="page-header-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="page-header-container">
            <h1 class="page-header-title">{icon_str}{title}</h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_profile():
    """
    Renders a clean, modern profile and branding section in the sidebar.
    """
    with st.sidebar:
        # App Branding Header
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; padding: 12px 6px 18px 6px; border-bottom: 1px solid #E2E8F0; margin-bottom: 16px;">
                <div style="background: linear-gradient(135deg, #2563EB, #0F766E); width: 36px; height: 36px; border-radius: 9px; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.25rem; font-weight: bold; box-shadow: 0 2px 4px rgba(37,99,235,0.2);">
                    👁️
                </div>
                <div>
                    <div style="font-weight: 800; font-size: 1.05rem; color: #0F172A; line-height: 1.2;">Suraksha AI</div>
                    <div style="font-size: 0.75rem; color: #64748B; font-weight: 500;">Missing Person ID System</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.get("login_status"):
            user_info = st.session_state.get("user_info", {})
            name = user_info.get("name") or st.session_state.get("username", "Officer")
            role = st.session_state.get("role", "Officer")
            city = user_info.get("city") or "Jurisdiction"
            area = user_info.get("area") or ""
            loc_str = f"{area}, {city}" if area else city

            role_bg = "#EFF6FF" if role.lower() == "admin" else "#F0FDF4"
            role_color = "#1D4ED8" if role.lower() == "admin" else "#15803D"
            role_border = "#BFDBFE" if role.lower() == "admin" else "#BBF7D0"

            st.markdown(
                f"""
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; margin-bottom: 16px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-weight: 700; color: #0F172A; font-size: 0.95rem;">{name}</span>
                        <span style="background-color: {role_bg}; color: {role_color}; border: 1px solid {role_border}; padding: 1px 8px; border-radius: 12px; font-size: 0.72rem; font-weight: 700;">
                            {role}
                        </span>
                    </div>
                    <div style="font-size: 0.78rem; color: #64748B; display: flex; align-items: center; gap: 4px;">
                        📍 {loc_str}
                    </div>
                    <div style="font-size: 0.72rem; color: #0F766E; margin-top: 4px; font-weight: 500;">
                        🔒 Cloud Session Active
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("🚪 Log Out", use_container_width=True, key="sidebar_logout_btn"):
                for k in ["login_status", "username", "user", "role", "jwt_token", "user_info"]:
                    st.session_state.pop(k, None)
                st.rerun()
