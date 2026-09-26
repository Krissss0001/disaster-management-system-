import streamlit as st
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from logic.disasters import get_active_disasters_count
from logic.resources import get_resource_metrics
from logic.needs import get_need_metrics
from utils.ui_helpers import apply_custom_styles, render_hero

st.set_page_config(
    page_title="Disaster Response Coordination Platform",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)
apply_custom_styles()

render_hero(
    title="Disaster Response Coordination Platform",
    subtitle="Emergency Logistics Command: Geospatial resource dispatch, real-time demand matching, and disaster lifecycle coordination.",
    icon="🚨"
)

# High Level Overview
st.markdown("""
Welcome to the **Disaster Response Coordination Platform**. This system enables emergency management agencies, 
first responders, and relief organizations to track natural disasters, deploy critical supplies, and match resources 
to urgent local needs with verifiable allocation integrity.
""")

# Quick Stat Summary
active_disasters = get_active_disasters_count()
res_metrics = get_resource_metrics()
need_metrics = get_need_metrics()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("🚨 Active Disasters", f"{active_disasters}")
with c2:
    st.metric("📦 Deployed Units", f"{res_metrics['total_resources']:,}")
with c3:
    st.metric("✅ Available Units", f"{res_metrics['available_resources']:,}")
with c4:
    st.metric("⚠️ Unmet Needs", f"{need_metrics['total_open_needs']}")

from streamlit_folium import st_folium
from logic.disasters import get_all_disasters
from logic.resources import get_all_resources
from logic.needs import get_all_needs
from utils.map_helpers import create_emergency_map

st.markdown("---")
st.subheader("🗺️ Live Incident & Emergency Logistics Map")
st.caption("Free interactive map using OpenStreetMap and Satellite layers. Click markers for details or toggle layers in the top right.")

all_d = get_all_disasters()
all_r = get_all_resources()
all_n = get_all_needs()
home_map = create_emergency_map(all_d, all_r, all_n, height=480)
st_folium(home_map, width=None, height=480, use_container_width=True, returned_objects=[])

st.markdown("---")
st.subheader("📌 Platform Navigation")

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    st.markdown("""
    #### 🌐 1. Dashboard
    Live geospatial map plotting incident perimeters, deployed resources, and emergency needs alongside core operational KPIs.
    """)
    if st.button("Go to Dashboard ➡️", key="btn_dash"):
        st.switch_page("pages/1_Dashboard.py")

    st.markdown("""
    #### 📝 2. Manage Disasters
    Register new disaster incidents, adjust severity levels (1–5), set coordinates, and update status lifecycle.
    """)

with nav_col2:
    st.markdown("""
    #### 📦 3. Resources
    Register staging supplies, rescue teams, medical packages, and equipment tied to disaster operational sectors.
    """)

    st.markdown("""
    #### ⚠️ 4. Needs
    Post urgent relief requests, tag urgency tiers (1–5), and monitor satisfaction state (pending/partial/fulfilled).
    """)

with nav_col3:
    st.markdown("""
    #### ⚖️ 5. Allocations
    Match compatible resources to pending needs. Enforces strict type consistency, availability checks, and non-negative logic.
    """)

    st.markdown("""
    #### 📊 6. Status
    Comprehensive disaster-by-disaster operational review combining resource levels, open needs, and allocation history.
    """)

st.markdown("---")
st.caption("Disaster Response Coordination Platform • Built with Streamlit, SQLAlchemy, SQLite, Folium.")
