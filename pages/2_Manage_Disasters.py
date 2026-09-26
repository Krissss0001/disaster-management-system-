import streamlit as st
import sys
from pathlib import Path

# Setup project root import
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from logic.disasters import get_all_disasters, create_disaster, update_disaster_status
from logic.alerts import dispatch_emergency_alert, get_recent_alerts
from utils.ui_helpers import apply_custom_styles, render_hero

st.set_page_config(
    page_title="Manage Disasters | Emergency Logistics",
    page_icon="🚨",
    layout="wide"
)
apply_custom_styles()

render_hero(
    title="Disaster Incident Command",
    subtitle="Register emergency incidents, declare disaster severity, and update operational lifecycle statuses.",
    icon="⚠️"
)

tab_create, tab_status, tab_alerts = st.tabs([
    "➕ Register New Disaster",
    "🔄 Update Incident Status",
    "📞 Emergency Dispatch Alerts"
])

# -------------------------------------------------------------
# TAB 1: REGISTER NEW DISASTER
# -------------------------------------------------------------
with tab_create:
    st.subheader("Declare New Emergency Incident")
    st.caption("Submit verified disaster reports to establish operational coordinates and staging parameters.")

    with st.form("create_disaster_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Disaster Incident Name *", placeholder="e.g. Sierra Foothills Wildfire")
            disaster_type = st.selectbox(
                "Disaster Type *",
                ["Wildfire", "Earthquake", "Flood", "Hurricane", "Tornado", "Tsunami", "Severe Storm", "Industrial Incident"]
            )
            severity = st.slider(
                "Severity Level (1 = Minor, 5 = Catastrophic) *",
                min_value=1,
                max_value=5,
                value=3,
                help="Severity scales emergency priority, map threat perimeter, and automatic dispatch alerts."
            )

        with col2:
            preset = st.selectbox(
                "Coordinate Quick Presets (Optional)",
                ["Custom", "San Francisco (37.7749, -122.4194)", "Los Angeles (34.0522, -118.2437)", "Houston (29.7604, -95.3698)", "Miami (25.7617, -80.1918)"]
            )
            default_lat, default_lon = 37.7749, -122.4194
            if "Los Angeles" in preset:
                default_lat, default_lon = 34.0522, -118.2437
            elif "Houston" in preset:
                default_lat, default_lon = 29.7604, -95.3698
            elif "Miami" in preset:
                default_lat, default_lon = 25.7617, -80.1918

            lat = st.number_input("Latitude *", value=default_lat, format="%.5f", min_value=-90.0, max_value=90.0)
            lon = st.number_input("Longitude *", value=default_lon, format="%.5f", min_value=-180.0, max_value=180.0)
            status = st.selectbox("Initial Operational Status", ["ongoing", "contained", "resolved"])

        description = st.text_area(
            "Incident Description & Threat Assessment",
            placeholder="Describe affected zones, critical infrastructure risk, and primary hazards..."
        )

        submit_btn = st.form_submit_button("🚨 Register Incident", use_container_width=True)

        if submit_btn:
            if not name or not name.strip():
                st.error("❌ Error: Disaster Incident Name is mandatory.")
            else:
                try:
                    new_disaster = create_disaster(
                        name=name.strip(),
                        disaster_type=disaster_type,
                        severity=severity,
                        latitude=lat,
                        longitude=lon,
                        description=description,
                        status=status
                    )
                    st.success(f"✅ Successfully declared incident: **{new_disaster['name']}** (ID: `{new_disaster['id']}`)")

                    # Trigger alert for high severity
                    if severity >= 4:
                        alert = dispatch_emergency_alert(
                            event_type="HIGH_SEVERITY_DISASTER",
                            title=f"{new_disaster['name']} Declared",
                            urgency_or_severity=severity,
                            details=f"Type: {disaster_type}, Severity Level {severity}/5. Immediate dispatch alert issued.",
                            location_str=f"{lat:.4f}, {lon:.4f}"
                        )
                        st.warning(f"🚨 **Emergency Alert Triggered:** {alert['summary']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to register disaster: {str(e)}")

# -------------------------------------------------------------
# TAB 2: UPDATE DISASTER STATUS
# -------------------------------------------------------------
with tab_status:
    st.subheader("Manage Lifecycle & Containment Status")
    disasters = get_all_disasters()

    if not disasters:
        st.info("No disasters currently recorded in the platform.")
    else:
        disaster_dict = {
            f"{d['name']} ({d['type']} - Status: {d['status'].upper()} - Sev: {d['severity']}/5)": d['id']
            for d in disasters
        }
        selected_label = st.selectbox("Select Incident to Update", options=list(disaster_dict.keys()))
        selected_id = disaster_dict[selected_label]
        current_disaster = next(d for d in disasters if d["id"] == selected_id)

        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"**Current Status:** `{current_disaster['status'].upper()}`")
            st.write(f"**Severity:** Level {current_disaster['severity']}/5")
            st.write(f"**Location:** `{current_disaster['latitude']:.4f}, {current_disaster['longitude']:.4f}`")

        with col_b:
            new_status = st.selectbox(
                "Set New Operational Status",
                options=["ongoing", "contained", "resolved"],
                index=["ongoing", "contained", "resolved"].index(current_disaster["status"])
            )
            update_btn = st.button("💾 Apply Status Change", use_container_width=True)

            if update_btn:
                if new_status == current_disaster["status"]:
                    st.info("Status is already set to this value.")
                else:
                    success = update_disaster_status(selected_id, new_status)
                    if success:
                        st.success(f"✅ Status updated to **{new_status.upper()}** for incident: {current_disaster['name']}.")
                        st.rerun()
                    else:
                        st.error("Failed to update status. Record not found.")

# -------------------------------------------------------------
# TAB 3: EMERGENCY DISPATCH ALERTS LOG
# -------------------------------------------------------------
with tab_alerts:
    st.subheader("📞 Emergency Call & Alert Dispatch Center")
    st.caption("Real-time logging of automated phone calls, SMS alerts, and webhooks dispatched to field emergency response units.")

    recent_alerts = get_recent_alerts(limit=10)
    if not recent_alerts:
        st.info("No emergency dispatch alerts triggered yet. Alerts are automatically issued when Severity >= 4 disasters or Urgency >= 4 medical needs are registered.")
    else:
        for idx, alert in enumerate(recent_alerts):
            with st.expander(f"🚨 {alert['timestamp']} — {alert['title']} (Level {alert['urgency_or_severity']}/5)", expanded=(idx == 0)):
                st.write(f"**Event Type:** `{alert['event_type']}`")
                st.write(f"**Target Dispatch Phone:** `{alert['target_dispatch']}`")
                st.write(f"**Status:** `{alert['status']}` ({alert['summary']})")
                st.write(f"**Location:** {alert['location']}")
                st.write(f"**Details:** {alert['details']}")
