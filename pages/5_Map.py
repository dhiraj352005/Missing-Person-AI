import streamlit as st
import os
import importlib
import pandas as pd

from pages.helper import db_queries
from pages.helper import ui_theme

st.set_page_config(page_title="Cases Map — Suraksha AI", page_icon="🗺️", layout="wide")

# Inject Light Dashboard Theme & Sidebar
ui_theme.inject_custom_theme()
ui_theme.render_sidebar_profile()

if "login_status" not in st.session_state or not st.session_state["login_status"]:
    st.warning("⚠️ Access restricted. Please log in from the Home page to view the jurisdiction map.")
    st.stop()

# Header
ui_theme.render_page_header(
    title="Cases by City — India Geospatial Intelligence",
    subtitle="Interactive national GIS tracking showing real-time missing person cases, investigation hotspots, and safe zones across India.",
    icon="🗺️",
)

try:
    import folium
    from streamlit_folium import st_folium
except ImportError:
    st.error(
        "❌ Map dependencies not installed. Run: `pip install folium streamlit-folium`"
    )
    st.stop()

# Approximate lat/lon for major Indian cities
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
    "Thane": (19.2183, 72.9781),
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
    "Jabalpur": (23.1815, 79.9864),
    "Haora": (22.5958, 88.2636),
    "Faridabad": (28.4089, 77.3178),
    "Unknown": (20.5937, 78.9629),
}

counts = db_queries.get_case_counts_by_city()

if not counts:
    st.info(
        "ℹ️ No cases with city data registered yet. Add a city location when registering cases to view map hotspots."
    )
    st.stop()

from pages.helper import utils
importlib.reload(utils)
from pages.helper.utils import create_base_map, add_city_case_markers

# Summary metrics ribbon
total_cities = len(counts)
unresolved_cities = sum(1 for d in counts.values() if d.get("not_found", 0) > 0)
resolved_cities = total_cities - unresolved_cities
total_geo_cases = sum(d.get("found", 0) + d.get("not_found", 0) for d in counts.values())

stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
with stat_col1:
    st.metric("🗺️ Monitored Cities", total_cities)
with stat_col2:
    st.metric("🚨 Active Hotspots", unresolved_cities)
with stat_col3:
    st.metric("✅ Resolved Safe Zones", resolved_cities)
with stat_col4:
    st.metric("📍 Geotagged Records", total_geo_cases)

st.write("")

# Build map centered on India with vibrant colorful style
mb_token = st.session_state.get("mapbox_token", os.environ.get("MAPBOX_TOKEN", ""))

m = create_base_map(
    location=[22.8, 79.2],
    zoom_start=5,
    mapbox_token=mb_token,
    style="Vibrant Streets (Colorful India)",
)

# Add biometric markers
add_city_case_markers(m, counts, CITY_COORDS)

# Display interactive map
st_folium(m, width="100%", height=560)

# Modern Legend
st.markdown(
    """
    <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 18px; margin-top: 14px; display: flex; gap: 20px; flex-wrap: wrap; align-items: center; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="display: inline-block; width: 14px; height: 14px; background: #e53935; border: 2px solid #ffcdd2; border-radius: 50%; box-shadow: 0 0 6px rgba(229,57,53,0.5);"></span>
            <span style="font-size: 0.88rem; font-weight: 600; color: #0F172A;">Active Investigation Hotspot</span>
            <span style="font-size: 0.8rem; color: #64748B;">(Unresolved missing cases)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="display: inline-block; width: 14px; height: 14px; background: #2e7d32; border: 2px solid #c8e6c9; border-radius: 50%; box-shadow: 0 0 6px rgba(46,125,50,0.5);"></span>
            <span style="font-size: 0.88rem; font-weight: 600; color: #0F172A;">Resolved Safe Zone</span>
            <span style="font-size: 0.8rem; color: #64748B;">(All reported cases found)</span>
        </div>
        <div style="color: #64748B; font-size: 0.82rem; margin-left: auto;">
            • Double-ring marker radius scales dynamically with local case volume
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Identify any cities not in coordinates lookup
skipped_cities = [city for city in counts if not any(k.lower() == city.lower() for k in CITY_COORDS)]
if skipped_cities:
    st.caption(f"ℹ️ Cities without coordinates in database dictionary (not plotted): {', '.join(skipped_cities)}")

# Modern City Summary Data Table
st.write("")
st.markdown("### 📊 City-Wise Case Distribution Breakdown")
rows = [
    {
        "City": city,
        "Total Cases": d["found"] + d["not_found"],
        "Active (Missing)": d["not_found"],
        "Resolved (Found)": d["found"],
        "Resolution Rate (%)": round((d["found"] / (d["found"] + d["not_found"])) * 100, 1) if (d["found"] + d["not_found"]) > 0 else 0.0,
    }
    for city, d in counts.items()
]

df = pd.DataFrame(rows).sort_values("Total Cases", ascending=False).reset_index(drop=True)
st.dataframe(df, use_container_width=True)
