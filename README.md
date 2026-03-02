# Huygen App

A shareable Streamlit app for exploring a 2D Huygens-based acoustics solver.

This repository is a clean rebuild from the previous sandbox work. The goal is to provide an interactive UI first (Phase 1), then connect and test the physics backend (Phase 2).

---

## Project Scope

### In Scope
- 2D acoustic simulation workflow
- Interactive UI for simulation and physical parameters
- Placeholder-driven frontend in Phase 1
- Solver integration and tests in Phase 2

### Out of Scope
- 3D geometries
- Arbitrary generalized geometries
- Multicore/distributed simulation

---

## Current Status

Phase 0 (Project Audit) is complete.

What exists now:
- `roadmap.md`: project scope, phased plan, Phase 0 audit summary, and success/failure criteria.
- `README_OLD.md`: legacy sandbox postmortem and old architecture notes.
- `app/`: currently empty (no Streamlit implementation yet).

What this means:
- Planning is in place.
- Implementation for the new app has not started yet in this repository.

---

## New App Flowchart (Target Architecture)

```mermaid
flowchart TD
    A[User opens Streamlit app] --> B[UI loads default simulation + physical parameters]
    B --> C[User edits parameters\n(simulation, physical, boundaries, transducers)]
    C --> D[Parameter validation + state update]
    D --> E[Preview tab updates geometry + transducer layout]
    D --> F{Run clicked?}
    F -- No --> C
    F -- Yes --> G[Phase 1: placeholder run\nprogress bar + estimated runtime]
    G --> H[Generate placeholder acoustic field]
    H --> I[Result tab renders colormap]
    I --> J[User modifies parameters]
    J --> K[Mark results stale / not up to date]
    K --> C

    L[Phase 2: real solver module] --> M[Compute field from validated params]
    M --> I
    G -. replaced by .-> L
```

---

## Planned Parameter Surface (Phase 1 UI)

### Simulation Parameters
- Grid resolution: X = 10-100, Y = 10-200 (step 10)
- Box dimensions: X and Y = 1-1000
- Number of reflections: 1-3 (integer)

### Physical Parameters
- Frequency: 1-10 MHz
- Medium: Water (c = 1500 m/s, rho = 1000 kg/m^3)
- Attenuation coefficient: 0-1
- Attenuation power: 1-2
- Boundary conditions: rigid/free for 4 boundaries
- Transducers:
  - Point or line source
  - Add/remove multiple sources
  - Per-source controls: type, optional length, power, wall side, position

### Visual Tabs
- **Preview**: domain and transducer placement
- **Field view**: acoustic colormap after run

---

## Phase Plan

## Phase 0 - Complete
- Audited old sandbox
- Identified reusable concepts
- Defined streamlined architecture and rollout

## Phase 1 - In Progress (next execution target)
Build and deploy a polished Streamlit frontend with placeholders (no physics backend yet):
1. Parameter panels grouped into simulation and physical sections
2. Preview and field visualization tabs
3. Placeholder run path with load/progress indicator
4. Branded UI + explicit model limitations disclaimer
5. Deployment setup for public access

## Phase 2 - Next
- Implement solver module with tests
- Integrate solver into app run path
- Preserve run status/loading behavior and stale-result detection

---

## Recommended Repository Layout

```text
Huygen_app/
├── app/
│   ├── streamlit_app.py
│   ├── ui_components.py
│   └── placeholder_solver.py
├── src/
│   └── huygens_solver.py          # Phase 2
├── tests/
│   ├── test_app_smoke.py
│   └── test_solver.py             # Phase 2
├── roadmap.md
├── README.md
└── requirements.txt
```

---

## Local Setup (once code is added)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Expected base dependencies:
- streamlit
- numpy
- matplotlib

---

## Model Limitations (to surface in UI)

- 2D slice model only
- Single-core execution
- Simple geometry assumptions
- Uniform homogeneous liquid medium
- Intended as an exploratory engineering tool, not a full multiphysics production simulator
# huygen_app
