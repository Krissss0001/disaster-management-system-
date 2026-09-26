# Disaster Response Coordination Platform

A full-stack emergency response coordination web application built with **Streamlit**, **SQLAlchemy**, and **SQLite**. The platform enables emergency management agencies, logistics officers, and first responders to declare disaster incidents, track critical resource staging, post urgent field needs, and match resources to demands under strict business validation rules.

---

## 🚀 Quick Setup & Installation

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.11)
- `pip` package manager

### 2. Clone and Setup Environment
Navigate to the project root directory:
```powershell
# Copy environment configuration
cp .env.example .env

# Install dependencies
pip install -r requirements.txt
```

### 3. Initialize and Seed Database
Run the database seeder to create SQLite tables and load sample incident data:
```powershell
python seed.py --reset
```
This initializes the database schema and populates:
- **1 Sample Disaster**: *Cascade Ridge Wildfire* (Severity 4, Status `ongoing`)
- **3 Deployed Resources**: Medical Supplies (100 units), Food & Water (500 units), Rescue Team (20 units)
- **2 Urgent Needs**: Medical Supplies (40 units, Urgency 5), Food & Water (200 units, Urgency 4)

### 4. Run the Application
Launch the multi-page Streamlit application:
```powershell
streamlit run streamlit_app.py
```
Open your browser at: **[http://localhost:8501](http://localhost:8501)**

### 5. Run the Automated Test Suite
Execute the comprehensive test suite (23 tests across all 7 phases):
```powershell
pytest -v
```

---

## 🏛️ Architecture Overview

The system follows a strict three-tier modular architecture with clean separation of concerns:

```
disaster-response-platform/
├── streamlit_app.py          # Landing portal, KPI metrics summary & page routing
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .env                      # Local environment configuration
├── seed.py                   # Convenience database seeder entrypoint
├── conftest.py               # Pytest path and runner configuration
├── database/                 # Persistence Layer
│   ├── connection.py         # SQLAlchemy engine, session maker & scoped get_db()
│   ├── models.py             # Declarative models with UUIDs & foreign keys
│   └── init_db.py            # Table initialization and seed scripts
├── logic/                    # Core Business Logic Layer (Decoupled from UI)
│   ├── disasters.py          # Disaster queries, creation & status lifecycles
│   ├── resources.py          # Resource inventory staging & metrics
│   ├── needs.py              # Urgent request posting & triage metrics
│   ├── allocations.py        # Pure validation logic & transaction execution
│   └── alerts.py             # Emergency calling & automated dispatch service
├── pages/                    # Presentation Layer (Streamlit Multi-Page)
│   ├── 1_Dashboard.py        # Geospatial map (Folium) + Live operational KPIs
│   ├── 2_Manage_Disasters.py # Incident declaration form + status update
│   ├── 3_Resources.py        # Supply staging form + per-disaster directory
│   ├── 4_Needs.py            # Field shortage form + urgency color-coded directory
│   ├── 5_Allocations.py      # Matching UI with instant validation preview & audit ledger
│   └── 6_Status.py           # Per-disaster operational balance (Surplus vs Deficit)
├── tests/                    # Test Suite
│   ├── test_phase1.py        # Database models & seeding tests
│   ├── test_phase2.py        # Dashboard queries & metrics tests
│   ├── test_phase3.py        # Disaster creation & status transition tests
│   ├── test_phase4.py        # Resource registration & filtering tests
│   ├── test_phase5.py        # Needs triage & urgency tests
│   ├── test_phase6.py        # Pure validation & allocation execution tests
│   └── test_phase7.py        # Per-disaster summary & balance tests
├── README.md                 # Complete system documentation
└── AI_USAGE.md               # Transparency report of AI assistance
```

---

## 💡 Technology Stack Rationale

### Why Streamlit?
- **Rapid Operational Turnaround:** Ideal for crisis management tools where interactive dashboards, forms, and dynamic data tables need to be built quickly without complex front-end build pipelines (React, Webpack, etc.).
- **Python-Native Reactivity:** Directly integrates with scientific, spatial, and analytical Python libraries (Folium, Pandas).
- **Embedded Multi-Page Routing:** Built-in sidebar navigation allows seamless partitioning into specialized incident response consoles.

### Why SQLite?
- **Zero-Infrastructure Footprint:** File-based storage requires no external database server process, making it resilient for rapid local deployment in disconnected or edge environments.
- **Portability:** Database files (`disaster_response.db`) can be backed up or transferred as a single file.
- **ACID Compliant:** Supports atomic transactions to guarantee allocation integrity.

### Why SQLAlchemy?
- **Domain Modeling & Type Safety:** Declarative models enforce relationships, foreign key constraints, and column validations.
- **Decoupling:** Keeps business logic independent of underlying SQL dialect. Allows moving to PostgreSQL for enterprise production without rewriting core application code.
- **Transactional Contexts:** Scoped session managers (`get_db()`) guarantee automatic rollbacks on errors.

---

## ⚖️ Allocation Validation Logic Explained

All allocation validation is encapsulated in a pure Python function [`validate_allocation()`](file:///c:/disaster/logic/allocations.py#L7) located in `logic/allocations.py`. It has zero dependencies on Streamlit, allowing comprehensive unit testing.

### Plain Language Business Rules:
1. **Strict Type Matching:** A resource cannot be assigned to an incompatible need (e.g., *Food & Water* cannot fulfill a *Medical Supplies* shortage).
2. **Positive Quantity:** Any allocation attempt with 0 or negative quantities is immediately rejected.
3. **Capacity Protection (No Over-Allocation):** The allocated quantity cannot exceed the resource provider's currently available inventory (`quantity_to_allocate <= resource.available`).
4. **Demand Boundary Enforcement:** The system prevents allocating more units than are actually required by the remaining need (`quantity_to_allocate <= remaining_need`).
5. **State Lifecycle Progression:**
   - On commit, `resource.available` is decremented by the allocated quantity.
   - If the total allocated units satisfy 100% of the request, `need.status` transitions from `pending` or `partial` to **`fulfilled`**.
   - If partially satisfied, the status transitions to **`partial`**.
   - An immutable `Allocation` audit record is stored with a timestamp.

---

## 📞 Emergency Call & Alert Dispatch System

The platform features an automated dispatch alert system (`logic/alerts.py`) configured via `.env`:
- **Trigger Conditions:**
  - Any disaster declared with **Severity Level 4 or 5**.
  - Any emergency resource need posted with **Urgency Level 4 or 5** (especially medical emergencies).
- **Operational Modes:**
  - `ALERT_MODE=mock` *(Default)*: Simulates automated emergency calls and SMS dispatches to field coordinators (`EMERGENCY_DISPATCH_PHONE`), creating an audit log without third-party telecom costs.
  - `ALERT_MODE=live`: Direct REST integration with Twilio (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`) and custom Webhook endpoints (e.g., PagerDuty, Slack emergency channel).

---

## ⚠️ Known Limitations
1. **Single-Node SQLite Concurrency:** SQLite serializes writes. Under extreme high-throughput concurrent write loads from hundreds of simultaneous dispatchers, SQLite may produce table locks.
2. **Distance-Agnostic Dispatching:** Allocations currently match resources based on type and availability; distance/travel time calculations are visualized on the map but not yet automatically minimized by an optimization solver.
3. **No Role-Based Access Control (RBAC):** All connected operators currently have uniform permissions to create disasters, stage supplies, and commit allocations.

---

## 🔮 Concrete Future Improvements
1. **Geographic Routing & Haversine Distance Optimization:**
   - Integrate the Open Source Routing Machine (OSRM) to calculate realistic travel times between resource staging depots and need locations, automatically ranking closest providers first.
2. **PostgreSQL Migration with PostGIS:**
   - Replace SQLite with PostgreSQL + PostGIS for spatial spatial indexing (`ST_DWithin`), enabling automated radius-based supply queries and multi-agency concurrent write support.
3. **Offline-First PWA Synchronization:**
   - Equip field responders with offline Progressive Web App caching so urgent needs can be collected in zones with intermittent cellular connectivity and synced upon reconnection.
