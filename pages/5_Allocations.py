import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Setup project root import
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from logic.disasters import get_all_disasters
from logic.needs import get_all_needs
from logic.resources import get_all_resources
from logic.allocations import validate_allocation, execute_allocation, get_all_allocations
from database.connection import get_db
from database.models import Allocation, ResourceNeed
from sqlalchemy import func
from utils.ui_helpers import apply_custom_styles, render_hero

st.set_page_config(
    page_title="Allocations | Disaster Response",
    page_icon="⚖️",
    layout="wide"
)
apply_custom_styles()

render_hero(
    title="Resource Allocation Command",
    subtitle="Pair field emergency shortages with available staging inventory under strict business validation.",
    icon="⚖️"
)

tab_dispatch, tab_history = st.tabs(["🚀 Execute Allocation", "📜 Allocation Ledger & Audit Log"])

disasters = get_all_disasters()

# -------------------------------------------------------------
# TAB 1: EXECUTE ALLOCATION FORM
# -------------------------------------------------------------
with tab_dispatch:
    st.subheader("Dispatch & Match Allocation")
    st.caption("Select an open emergency need and assign an available matching supply inventory.")

    # Calculate remaining needs for all open needs
    all_needs = get_all_needs(status_filter=None)
    open_needs = [n for n in all_needs if n["status"] in ["pending", "partial"]]

    if not open_needs:
        st.success("🎉 All logged resource needs are 100% fulfilled! No pending requests.")
    else:
        # Compute exact remaining for each open need
        with get_db() as db:
            need_remaining_map = {}
            for n in open_needs:
                allocated_so_far = db.query(
                    func.coalesce(func.sum(Allocation.quantity_allocated), 0)
                ).filter(Allocation.need_id == n["id"]).scalar()
                remaining = max(0, n["quantity_needed"] - int(allocated_so_far))
                need_remaining_map[n["id"]] = remaining

        # Filter out if remaining is 0
        open_needs = [n for n in open_needs if need_remaining_map.get(n["id"], 0) > 0]

        need_options = {
            f"[{n['status'].upper()}] {n['type']} (Rem: {need_remaining_map[n['id']]} / Req: {n['quantity_needed']} - Urg {n['urgency']}/5) — {n['disaster_name']}": n["id"]
            for n in open_needs
        }

        col_n, col_r = st.columns(2)

        with col_n:
            st.markdown("#### 1. Select Emergency Need")
            selected_need_label = st.selectbox("Open Need *", list(need_options.keys()))
            selected_need_id = need_options[selected_need_label]
            selected_need = next(n for n in open_needs if n["id"] == selected_need_id)
            need_rem = need_remaining_map[selected_need_id]

            st.info(
                f"**Need Summary:** {selected_need['type']}\n\n"
                f"- **Remaining Unmet:** `{need_rem}` units\n"
                f"- **Incident:** {selected_need['disaster_name']}\n"
                f"- **Urgency:** Level {selected_need['urgency']}/5"
            )

        with col_r:
            st.markdown("#### 2. Select Source Resource")
            # Fetch resources for this disaster or all available
            all_resources = get_all_resources()
            available_resources = [r for r in all_resources if r["available"] > 0]

            if not available_resources:
                st.error("No resources with positive available quantity are currently registered.")
                selected_resource = None
            else:
                # Group: Matching type first
                res_options = {}
                for r in available_resources:
                    match_badge = "✅ MATCH" if r["type"].lower() == selected_need["type"].lower() else "❌ MISMATCH"
                    label = f"{match_badge} | {r['type']} ({r['available']} avail) — {r['provider']} ({r['disaster_name']})"
                    res_options[label] = r

                selected_res_label = st.selectbox("Available Resource *", list(res_options.keys()))
                selected_resource = res_options[selected_res_label]

                st.info(
                    f"**Resource Summary:** {selected_resource['type']}\n\n"
                    f"- **Available:** `{selected_resource['available']}` units\n"
                    f"- **Provider:** {selected_resource['provider']}\n"
                    f"- **Location Incident:** {selected_resource['disaster_name']}"
                )

        if selected_resource:
            st.markdown("---")
            st.markdown("#### 3. Allocation Quantity & Validation Preview")

            default_qty = min(selected_resource["available"], need_rem)
            alloc_qty = st.number_input(
                "Quantity to Allocate *",
                min_value=1,
                value=max(1, default_qty),
                step=1,
                help="Amount must not exceed available resource quantity or remaining need."
            )

            # Test pure validation function
            is_valid, validation_error = validate_allocation(
                need_type=selected_need["type"],
                resource_type=selected_resource["type"],
                available_quantity=selected_resource["available"],
                quantity_to_allocate=int(alloc_qty),
                remaining_needed=need_rem
            )

            if not is_valid:
                st.error(f"⛔ **Validation Rejected:** {validation_error}")
            else:
                st.success(
                    f"✅ **Validation Passed:** Allocating `{alloc_qty}` units of **{selected_need['type']}** "
                    f"from **{selected_resource['provider']}**."
                )

            confirm_btn = st.button("🚀 Confirm & Commit Allocation", disabled=not is_valid, use_container_width=True)

            if confirm_btn and is_valid:
                try:
                    result = execute_allocation(
                        need_id=selected_need["id"],
                        resource_id=selected_resource["id"],
                        quantity_to_allocate=int(alloc_qty)
                    )
                    st.success(
                        f"🎉 Allocation successful! Created record `{result['allocation_id']}`.\n\n"
                        f"- Need Status is now **{result['need_status'].upper()}** (Remaining need: {result['remaining_need']} units).\n"
                        f"- Remaining resource available: **{result['remaining_resource_available']}** units."
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to commit allocation: {str(e)}")

# -------------------------------------------------------------
# TAB 2: ALLOCATION AUDIT LOG
# -------------------------------------------------------------
with tab_history:
    st.subheader("Disaster Allocation Audit Ledger")
    st.caption("Immutable transaction history of all resource allocations and dispatch operations.")

    history = get_all_allocations()

    if not history:
        st.info("No allocations have been committed yet.")
    else:
        df_allocs = pd.DataFrame([
            {
                "Disaster Incident": h["disaster_name"],
                "Item Type": h["need_type"],
                "Quantity Allocated": h["quantity_allocated"],
                "Provider": h["provider"],
                "Need Urgency": f"Level {h['urgency']}/5",
                "Timestamp (UTC)": h["created_at"].strftime("%Y-%m-%d %H:%M:%S") if h["created_at"] else "N/A",
                "Allocation ID": h["id"]
            }
            for h in history
        ])
        st.dataframe(df_allocs, use_container_width=True, hide_index=True)
