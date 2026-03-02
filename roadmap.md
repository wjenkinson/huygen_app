### Huygen App

#### **Blurb: Scope and Non-Scope**
**Scope:** Upcycle the Huygen solver demo into a shareable app. The user can play with simulation and physical parameters to tune and play with an acoustics solver.

**Non-Scope:** 3D geometries, generalized geometries, multicore simulations.

---

#### **Phase 0: Project Audit**
**Description:** Audit the sandbox project, identify areas to improve, artefacts to keep and to discard. 

**Tasks:**
- The flowchart for the sandbox project was obscure, build a reference flowchart in advance for the rebuild.
- Large amounts of deadcode; pick out the core modules, distill the best features, discard the rest.
- Identified leverage from the USNDT project.

**Success Criteria:**
- Clean, skimmable flowchart build around running the streamlit app.
- 80% code reduction.
- Clear steps to roll out the new implementation.
- Insight from USNDT
- Written summary of insights

**Failure Criteria:**
- By the end of this phase, the codebase is a mess and the broader plan is unclear


**Audit Summary**
The project contains the app directory (UI layer, streamlit), the source code (backend, huygen solvers using numpy), and the outputs (visualizations, diagnostics etc.). The flow chart is simple: app calls the src, src deposits results in the output, and app retrieves from output.

Simple streamlit app shouldn't overflow to more than one module. Add a runnable test to load up the app using stubs for the simulation and physical parameters:
Use slide bars for all parameters, and a run button to start the simulation. Set the following options and slidebar limits:
SIMULATION PARAMETERS
Grid resolution: X: 10-100, Y: 10-200 (intervals of 10)
Box dimensions: X: 1-1000, Y: 1-1000 (0.5 intervals, log scale)
Number of reflections: 1-3 (integer intervals)
PHYSICAL PARAMETERS
Frequency: 1-10 MHz (integer intervals, log scale)
Medium: Water 1500 m/s, 1000 kg/m^3 (Drop-down menu, just water)
Attenuation: 0-1 (integer intervals)
Attenuation power: 1-2 (integer intervals)
Boundary: Rigid or free (4 boundaries, each has a toggle between rigid and free)
Transducer: Point source or line source, user can add as many transducers as the want with a +, each transducer has it's own card (toggle line source, optional length, power, left or right wall, position as % from the bottom, and delete transducer)
Other notes on the transducers: line sources are handled as point sources with separation equal to gridpoint separations, and total power divided by the number of point sources. 

Besides these options, there is also two visualization options kept under tabs:
1. a preview visualization (the box and the position and locations of the transducers)
2. a visualization of the colour map (v_min = 0.1*min, v_max = 0.9*max) that appears after run.
If parameters are changed after the user clicks "Run" and message appears informing that the simulation is not up to date.

WHAT CODE TO KEEP
Solver is carried over, potential acceleration by switching to float32 away from float64 (and complex64 from complex128) and Acoustic separator should be striped for parts, the rest can be discarded.
Pay attention to how streamlit manages python packages, take a look back at the FV project. Check requirements, perhaps.

WHAT REQUIREMENTS
 - streamlit
 - numpy
 - matplotlib



#### **Phase 1: Build the streamlit app with placeholders**
**Description:** Have a frontend built out and deployed, usable and public (with no physics backend)

**Tasks:**
- Visualization of the acoustic field
- List of parameters organized by "simulation" and "physical"
- On the fly analytics (estimated run time or at least a loadbar)
- Logo and branding, disclaimer on limits (2D, single core, simple geometry, uniform homogenous liquid, etc.)

**Success Criteria:**
- Nice looking streamlit app
- All subtasks satisfied
- Deployed
- Satisfactory codebase

**Failure Criteria:**
- Failed deployment
- Rotten codebase
- Incomplete features or feature limitations.

#### **Phase 2: Core solver**
**Description:** Core Huygen solver is built out with testing. Based on the original solver, it takes as an input the grid, sources, and physical parameters, and outputs the acoustic field to the output directory (where the appp picks it up).

**Tasks:**
- Build the solver
- Build the tests
- Run it end-to-end in the application

**Success Criteria**
- Passes test
- Passes during integration
- App identifying beginning and end of simulation, presents a loading bar and updates app accordingly. 

**Failure Criteria**
- Messy incomprehensible codebase
- Integration unclear or illogical