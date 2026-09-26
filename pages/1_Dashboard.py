import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import pandas as pd
import sys
from pathlib import Path

# Setup project root import
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from logic.disasters import get_all_disasters, get_active_disasters_count
from logic.resources import get_all_resources, get_resource_metrics
from logic.needs import get_all_needs, get_need_metrics
from utils.ui_helpers import apply_custom_styles, render_hero

st.set_page_config(
    page_title="Dashboard | Disaster Response Coordination",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)
apply_custom_styles()

render_hero(
    title="Emergency Coordination Dashboard",
    subtitle="Live situational awareness, resource readiness, and active emergency operations map.",
    icon="🌐"
)

# -------------------------------------------------------------
# 1. KEY METRICS ROW
# -------------------------------------------------------------
disaster_active_count = get_active_disasters_count()
res_metrics = get_resource_metrics()
need_metrics = get_need_metrics()

all_disasters = get_all_disasters()
total_disasters_count = len(all_disasters)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Active Disasters</div>
        <div class="metric-val" style="color: #e63946;">{disaster_active_count}</div>
        <div class="metric-sub">{total_disasters_count} total disaster records</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Available Resources</div>
        <div class="metric-val" style="color: #2a9d8f;">{res_metrics['available_resources']:,}</div>
        <div class="metric-sub">{res_metrics['total_resources']:,} total units deployed</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Open Needs</div>
        <div class="metric-val" style="color: #f4a261;">{need_metrics['total_open_needs']}</div>
        <div class="metric-sub">{need_metrics['pending_needs']} pending, {need_metrics['partial_needs']} partial</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    fulfillment_rate = (
        (res_metrics['allocated_resources'] / res_metrics['total_resources'] * 100)
        if res_metrics['total_resources'] > 0 else 0
    )
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Resource Utilization</div>
        <div class="metric-val" style="color: #457b9d;">{fulfillment_rate:.1f}%</div>
        <div class="metric-sub">{res_metrics['allocated_resources']:,} allocated units</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# -------------------------------------------------------------
# 2. INTERACTIVE FOLIUM MAP
# -------------------------------------------------------------
st.subheader("🗺️ Live Incident & Logistics Geospatial Map")

# Map Controls
map_ctrl_col1, map_ctrl_col2 = st.columns([3, 1])
with map_ctrl_col1:
    st.caption("Visualizing disaster epicenter zones (Red), staging resources (Blue/Green), and critical unmet needs (Amber).")
with map_ctrl_col2:
    show_legend = st.checkbox("Show Map Legend", value=True)

from utils.map_helpers import create_emergency_map

# Build map using free OpenStreetMap, Satellite, and CartoDB layers
all_resources = get_all_resources()
all_needs = get_all_needs()
m = create_emergency_map(all_disasters, all_resources, all_needs, height=520)

# Render map in Streamlit (returned_objects=[] prevents re-render on map drag/zoom)
st_folium(m, width=None, height=520, use_container_width=True, returned_objects=[])

if show_legend:
    l_c1, l_c2, l_c3 = st.columns(3)
    with l_c1:
        st.markdown("🔴 **Disasters:** Red marker & danger zone (radius scales with severity 1–5)")
    with l_c2:
        st.markdown("🔵 **Resources:** Blue marker with quantity available & provider info")
    with l_c3:
        st.markdown("🟠 **Needs:** Amber/Red marker indicating emergency resource shortages")

st.markdown("---")

# -------------------------------------------------------------
# 3. TABLE OF DISASTERS
# -------------------------------------------------------------
st.subheader("📋 Active Disasters Directory")

f1, f2, f3 = st.columns([2, 2, 3])
with f1:
    status_options = ["All", "ongoing", "contained", "resolved"]
    selected_status = st.selectbox("Filter by Status", options=status_options, index=0)
with f2:
    all_types = sorted(list({d["type"] for d in all_disasters})) if all_disasters else []
    type_options = ["All"] + all_types
    selected_type = st.selectbox("Filter by Type", options=type_options, index=0)
with f3:
    search_query = st.text_input("Search by Name or Keyword", placeholder="e.g. Wildfire, Ridge...")

# Filter logic
filtered_disasters = get_all_disasters(
    status_filter=selected_status if selected_status != "All" else None,
    type_filter=selected_type if selected_type != "All" else None
)

if search_query:
    q = search_query.strip().lower()
    filtered_disasters = [
        d for d in filtered_disasters
        if q in d["name"].lower() or (d["description"] and q in d["description"].lower())
    ]

if filtered_disasters:
    # Format table for display
    display_rows = []
    for d in filtered_disasters:
        display_rows.append({
            "Name": d["name"],
            "Type": d["type"],
            "Severity": f"{'⭐' * d['severity']} ({d['severity']}/5)",
            "Status": d["status"].upper(),
            "Latitude": round(d["latitude"], 4),
            "Longitude": round(d["longitude"], 4),
            "Resources Linked": d["resource_count"],
            "Needs Pending": d["needs_count"],
            "Reported Time": d["created_at"].strftime("%Y-%m-%d %H:%M UTC") if d["created_at"] else "N/A",
            "Description": d["description"] or "—"
        })
    df_disasters = pd.DataFrame(display_rows)
    st.dataframe(df_disasters, use_container_width=True, hide_index=True)
else:
    st.info("No disasters match the selected filters.")
