# Visual Memory Engine for Cognitive & Elderly Care

> **Working concept:** An evidence-first, multi-camera visual memory
> system that helps caregivers answer practical questions such as
> **"Where was Dad's watch last seen?"** without guessing.

------------------------------------------------------------------------

## 1. Executive Summary

Traditional home cameras record video. This project aims to turn camera
observations into a **searchable visual memory**.

The system continuously observes registered people, important personal
objects, and meaningful places. Instead of requiring a caregiver to
manually scrub through hours of footage, it creates structured memories
such as:

> **Dad's watch --- last visually confirmed in Dad's hand, living room,
> 8:05 PM.**\
> Evidence: snapshot + camera + timestamp + confidence.

The initial product is deliberately narrow: **reliable "last seen"
retrieval for registered objects**. Medication adherence, routines,
anomaly detection, voice assistance, and richer caregiver intelligence
can later be built on the same memory foundation.

### Core design philosophy

-   **Evidence first:** report what was visually observed, not what the
    system guesses.
-   **No false certainty:** uncertain observations should be marked
    uncertain.
-   **Memory, not surveillance search:** convert video into meaningful
    events.
-   **Human-in-the-loop learning:** ask approved users when identity or
    location is ambiguous.
-   **Low interruption:** learn actively during setup; queue non-urgent
    clarification later.
-   **Shared multi-camera memory:** cameras are sensors; the memory
    service is the core product.
-   **Question-driven development:** add capabilities according to
    questions the system can answer reliably.

------------------------------------------------------------------------

## 2. Problem

Caregivers supporting people with Alzheimer's disease or cognitive
decline repeatedly face questions such as:

-   Where are the keys?
-   Where was the watch last seen?
-   Who last handled the wallet?
-   Has this item moved today?
-   Where has this object been throughout the day?
-   Eventually: was medication likely taken, and what evidence supports
    that?

Existing cameras preserve footage, but footage is not memory. The
caregiver still has to search it.

### Product opportunity

**Camera footage → observations → semantic events → searchable memory →
evidence-backed answers**

------------------------------------------------------------------------

## 3. Product Vision

``` mermaid
flowchart LR
    A[Home Cameras] --> B[Perception Layer]
    B --> C[Observation Stream]
    C --> D[Visual Memory Engine]
    D --> E[Query & Reasoning Layer]
    E --> F[Caregiver App / Web]
    F --> G["Where was the watch last seen?"]
    D --> H[Evidence Store]
    H --> F
```

The **ESP32-CAM is not the product**. It is one possible sensing device.

The defensible system is the **Visual Memory Engine** that turns
observations from one or many cameras into structured, queryable,
explainable memories.

------------------------------------------------------------------------

## 4. Primary MVP Question

### MVP must answer one question extremely well

> **"Where was this registered object last seen?"**

A successful answer contains:

  Field                              Example
  ---------------------------------- --------------------------------
  Object                             Dad's watch
  Last visually confirmed location   Coffee table, living room
  Time                               8:15 PM
  State                              On surface / carried / visible
  Associated person                  Dad, if relevant
  Camera                             Living Room Camera
  Confidence                         High / numeric score
  Evidence                           Snapshot
  Claim type                         Visually confirmed

### Important rule

If the watch is later seen in Dad's hand and then disappears from view:

**Correct:** "Last visually confirmed in Dad's hand at 8:05 PM."

**Incorrect:** "Probably in Dad's bedroom."

The system should preserve the boundary between **observation** and
**inference**.

------------------------------------------------------------------------

## 5. User Experience

### Example query

``` mermaid
sequenceDiagram
    actor U as Caregiver
    participant UI as App/Web
    participant Q as Query Service
    participant M as Memory Service
    participant L as Live Camera Search

    U->>UI: Where is Dad's watch?
    UI->>Q: Query object profile
    Q->>M: Get latest confirmed event
    M-->>Q: Last seen + evidence
    Q->>L: Check current camera feeds
    L-->>Q: Current observation / none
    Q-->>UI: Best factual answer
    UI-->>U: Location + time + snapshot
```

### Query strategy

1.  Search structured memory.
2.  Check current camera feeds for fresher evidence.
3.  Reconcile the results.
4.  Return the newest reliable observation.
5.  Never silently convert uncertainty into fact.

------------------------------------------------------------------------

## 6. What the System Knows

The initial domain can be modeled around four primary entities.

``` mermaid
flowchart TD
    P[People]
    O[Objects]
    L[Places]
    E[Events / Interactions]

    P --> E
    O --> E
    L --> E

    P -->|"owns / associated with"| O
    L -->|"contains"| O
```

### People

Examples: - Person receiving care - Primary caregiver - Approved family
member / collaborator

Stored information may include: - Profile ID - Name/display label -
Reference photos - Role - Authorization level

### Objects

Examples: - Watch - Keys - Wallet - Bag - Medication container

Stored information may include: - Object ID - Friendly name: "Dad's
watch" - Multiple reference photos - Owner / associated person -
Priority - Learned visual embeddings/features - Registration history

### Places

Places should be human-readable rather than centimeter-level
coordinates.

Example hierarchy:

``` text
Home
└── Living Room
    ├── Coffee Table
    ├── TV Cabinet
    └── Sofa
```

The system should distinguish **generic semantics** ("this is a table")
from **house-specific identity** ("this is the living-room coffee
table").

### Events / interactions

Long term, the cleanest model is an interaction:

``` text
PERSON / OBJECT → ACTION / STATE → OBJECT / PLACE
```

Examples:

``` text
Watch → located_on → Coffee Table
Dad → picked_up → Watch
Dad → carrying → Watch
Watch → last_visible_with → Dad
```

This interaction model may feel abstract initially, so the MVP can
expose a simpler event structure while keeping room to evolve.

------------------------------------------------------------------------

## 7. Observation vs Event vs Current State

This distinction is central.

### Observation

A perception result at a point in time.

``` json
{
  "object": "dad_watch",
  "camera": "living_room_cam",
  "timestamp": "20:05:10",
  "place": "coffee_table",
  "confidence": 0.93
}
```

### Event

A meaningful change derived from observations.

``` text
20:00–20:05 — Dad's watch remained on the coffee table.
20:05 — Dad picked up the watch.
```

### Current state

A derived convenience view:

``` text
Dad's watch:
last_confirmed = Dad's hand
last_confirmed_at = 20:05
```

### Architectural principle

**Do not silently overwrite history.**

Append observations/events, then derive the latest state.

------------------------------------------------------------------------

## 8. Event Compression Logic

Storing every frame forever is wasteful and makes search noisy.

If a watch remains on one table for six hours, the semantic memory
should represent that as one continuous event rather than thousands of
identical entries.

``` mermaid
flowchart TD
    A[New Observation] --> B{Same object?}
    B -- No --> C[Create observation]
    B -- Yes --> D{Human-meaningful state changed?}
    D -- No --> E[Extend current event]
    D -- Yes --> F[Close previous event]
    F --> G[Create new event]
```

### Proposed event-change rule

Create a new event when a change would materially alter the answer to:

> **"Where is / where was this object?"**

Examples:

  ------------------------------------------------------------------------
  Change                                  New event? Why
  --------------------- ---------------------------- ---------------------
  Watch moves 10 cm on                            No Same human-meaningful
  same coffee table                                  location

  Watch moves coffee                             Yes Location changed
  table → shelf                                      

  Watch picked up by                             Yes State + association
  Dad                                                changed

  Watch stays in Dad's                    Usually no Same meaningful state
  hand while he moves                                
  slightly                                           

  Watch moves Living                             Yes Room changed
  Room → Bedroom                                     

  Watch becomes                      State-dependent Preserve last
  occluded                                           confirmed evidence

  Similar unknown watch                Clarification Identity uncertain
  appears                                            
  ------------------------------------------------------------------------

------------------------------------------------------------------------

## 9. Human-in-the-Loop Learning

The system should not repeatedly ask the same question.

### During initial setup

Use an explicit learning mode:

1.  Register home / rooms.
2.  Register cameras and assign rooms.
3.  Register meaningful landmarks.
4.  Register people.
5.  Register focus objects using several photos.
6.  Define ownership/association and priority.
7.  Add approved collaborators.

### During normal operation

If the system encounters uncertainty:

``` mermaid
flowchart LR
    A[Ambiguous Observation] --> B{Seen ambiguity before?}
    B -- No --> C[Add clarification to review queue]
    C --> D[Approved user confirms]
    D --> E[Update object/place profile]
    E --> F[Reuse learning later]
    B -- Yes --> F
```

Examples: - "Is this the same black wallet?" - "Which side table is
this?" - "A new table appeared. Should I register it?"

**Design principle:** learn continuously, disturb as little as possible.

------------------------------------------------------------------------

## 10. Identity Strategy

The system needs **instance recognition**, not merely category
recognition.

It must distinguish:

``` text
a watch
```

from:

``` text
Dad's specific watch
```

Object identity can eventually combine:

  Signal                    Purpose
  ------------------------- -------------------------
  Registration photos       Primary visual identity
  Visual embedding          Similarity matching
  Owner association         Context
  Typical rooms             Context
  Common paired objects     Context
  Historical observations   Long-term evidence
  Human confirmation        Ground truth

For V1, begin with **photos + object ID + owner + priority**. Add
contextual identity signals later.

------------------------------------------------------------------------

## 11. Place Learning

### Human-defined room identity

Rooms should initially be manually named:

-   Living Room
-   Kitchen
-   Bedroom
-   Hallway

Each camera is assigned to a room.

### Landmark identity

The vision model may already understand generic categories such as
table, shelf, sofa, cabinet.

The caregiver provides **house-specific meaning**:

> "That table is the Living Room Coffee Table."

If two landmarks are visually similar, the system asks once and
remembers.

A full floor plan is valuable later, especially for movement timelines,
but **not required for the first MVP**.

------------------------------------------------------------------------

## 12. Multi-Camera Shared Memory

Each camera should not own an isolated memory.

``` mermaid
flowchart TD
    C1[Living Room Camera]
    C2[Kitchen Camera]
    C3[Bedroom Camera]
    C4[Future Sensors]

    C1 --> P[Perception Services]
    C2 --> P
    C3 --> P
    C4 --> P

    P --> M[(Shared Visual Memory)]

    M --> Q[Query Service]
    Q --> UI[Caregiver App]
```

Example timeline:

``` text
18:02  Watch — Bedroom dresser — Camera 3
18:47  Watch — Dad's hand — Camera 2
19:05  Watch — Living-room coffee table — Camera 1
```

Default answer:

> Last visually confirmed on the living-room coffee table at 7:05 PM.

Optional action:

> **Show full timeline**

------------------------------------------------------------------------

## 13. Memory Service

### The memory service is intentionally "boring"

It should **not be the vision model**.

Its job is to:

1.  Accept observations.
2.  Validate/store evidence.
3.  Convert observations into semantic events.
4.  Maintain derived current state.
5.  Answer deterministic memory queries.
6.  Preserve history.
7.  expose confidence and provenance.

### Minimal API surface

``` text
POST /observations
GET  /objects/{id}/last-seen
GET  /objects/{id}/timeline
GET  /places/{id}/objects
GET  /people/{id}/interactions
POST /clarifications
```

For the first implementation, only the first three are necessary.

------------------------------------------------------------------------

## 14. Minimal Data Model

``` mermaid
erDiagram
    PERSON ||--o{ OBJECT : owns
    PLACE ||--o{ CAMERA : contains
    OBJECT ||--o{ OBSERVATION : observed_as
    CAMERA ||--o{ OBSERVATION : produces
    PLACE ||--o{ OBSERVATION : located_at
    PERSON ||--o{ OBSERVATION : associated_with
    OBSERVATION ||--o| EVIDENCE : supported_by
    OBJECT ||--o{ EVENT : has
    PLACE ||--o{ EVENT : occurs_at
```

### Suggested tables

  Table                 Purpose
  --------------------- -----------------------------------
  `people`              Registered people
  `users`               Caregivers/collaborators
  `permissions`         Who may register/confirm/edit
  `objects`             Registered focus items
  `object_references`   Registration images/features
  `places`              Rooms and landmarks
  `cameras`             Camera identity and assigned room
  `observations`        Raw structured perception results
  `events`              Compressed semantic memory
  `evidence`            Snapshot/video references
  `clarifications`      Human review queue
  `current_state`       Optional derived/cache table

------------------------------------------------------------------------

## 15. Suggested Technical Architecture

``` mermaid
flowchart LR
    ESP[ESP32-CAM / IP Cameras]
    ING[Camera Ingestion]
    DET[Detection / Tracking]
    EMB[Instance Embedding]
    VLM[VLM / Scene Understanding]
    OBS[Observation Builder]
    MEM[Memory Service]
    DB[(PostgreSQL)]
    OBJ[(Evidence Storage)]
    API[Query API]
    WEB[Web / Mobile UI]

    ESP --> ING
    ING --> DET
    DET --> EMB
    ING --> VLM
    EMB --> OBS
    VLM --> OBS
    OBS --> MEM
    MEM --> DB
    MEM --> OBJ
    DB --> API
    OBJ --> API
    API --> WEB
```

### Practical first-stack candidates

  -----------------------------------------------------------------------
  Layer                   Initial choice          Why
  ----------------------- ----------------------- -----------------------
  Camera                  ESP32-CAM / existing    Cheap sensing prototype
                          stream                  

  Backend API             FastAPI                 Lightweight Python API

  Structured DB           PostgreSQL              Reliable event/query
                                                  storage

  Object detection        YOLO-family detector    Fast baseline

  Visual similarity       CLIP / DINOv2-style     Instance matching
                          embeddings              experiments

  VLM                     Swappable API/local VLM Semantic scene
                                                  interpretation

  Evidence                Files/object storage    Snapshots, optional
                                                  clips

  UI                      React / Next.js or      Query + timeline
                          simple web UI           dashboard

  Deployment              Local workstation       Faster experimentation
                          initially               
  -----------------------------------------------------------------------

**Do not make the architecture dependent on one VLM vendor.**

Perception should be replaceable.

------------------------------------------------------------------------

## 16. Three-Layer Memory Strategy

A strong long-term architecture can combine three kinds of memory.

### Layer 1 --- Event memory

Fast factual retrieval.

``` text
Watch moved from coffee table → Dad's hand.
```

Best for: - last seen - timeline - state transitions

### Layer 2 --- Episodic memory

Groups events into meaningful episodes.

``` text
Between 8:00 and 8:20, Dad prepared to leave home and handled
his watch, keys and wallet.
```

Best for: - summaries - routine understanding - longer-term search

### Layer 3 --- Knowledge graph

Persistent relationships.

``` text
Dad → owns → Watch
Watch → usually_found_in → Bedroom
Dad → uses → Medication Box
```

Best for: - reasoning - relationships - future caregiver questions

### Recommended order

**Event memory first → episodic memory second → knowledge graph when
justified by real queries.**

------------------------------------------------------------------------

## 17. Authorization & Privacy

Not everyone should be allowed to teach the system.

### Roles

  Role                      Example capability
  ------------------------- -------------------------------------------
  Primary caregiver/admin   Full setup and permissions
  Approved collaborator     Confirm identities, register objects
  Viewer                    Search memory and view permitted evidence
  Person receiving care     Configurable access

High-level privacy requirements:

-   Authentication
-   Role-based permissions
-   Encryption in transit/at rest
-   Audit trail for profile changes
-   Explicit camera/room configuration
-   Configurable evidence retention
-   Local processing where practical
-   Clear distinction between caregiver support and medical diagnosis

------------------------------------------------------------------------

## 18. MVP Scope

### In scope

-   One registered person
-   One to several registered focus objects
-   One camera initially
-   Manual room/camera labeling
-   Object registration from several photos
-   Structured observations
-   Event compression
-   Last-seen query
-   Object timeline
-   Snapshot evidence
-   Confidence
-   Basic clarification flow
-   Simple web interface

### Explicitly out of scope initially

-   Full medication-adherence inference
-   Fall detection
-   Natural voice companion
-   Predictive behavior
-   Complete house digital twin
-   Autonomous medical decisions
-   Perfect person re-identification
-   Sophisticated knowledge graph
-   Production-scale mobile app

------------------------------------------------------------------------

## 19. Five-Day Engineering Sprint

### Goal

At the end of five days, demonstrate:

> **Camera/observation → memory → "Where was the watch last seen?" →
> answer + evidence**

  -----------------------------------------------------------------------
  Day                     Objective               Deliverable
  ----------------------- ----------------------- -----------------------
  1                       Freeze MVP architecture One-page architecture +
                                                  success criteria

  2                       Design memory schema    Objects, observations,
                                                  events, evidence

  3                       Build memory service    Working `last-seen` +
                          using fake observations timeline APIs

  4                       Connect perception/VLM  Real observation enters
                          output                  memory

  5                       Build end-to-end demo   Query → result →
                                                  timestamp + snapshot
  -----------------------------------------------------------------------

### First coding exercise

Before using a camera or VLM, hardcode:

``` text
08:00 — Dad's watch — coffee table
08:05 — Dad's watch — Dad's hand
08:10 — Dad's watch — kitchen counter
```

Then make the service correctly answer:

``` text
Where was Dad's watch last seen?
```

If that works, the core memory loop exists.

------------------------------------------------------------------------

## 20. Development Roadmap

``` mermaid
gantt
    title Proposed Visual Memory Engine Roadmap
    dateFormat  YYYY-MM-DD
    axisFormat  %b

    section Foundation
    Architecture & data model       :a1, 2026-08-24, 2w

    section MVP
    Single-camera last-seen loop    :a2, after a1, 5w
    Reliability & event memory      :a3, after a2, 5w

    section Scale
    Multi-camera shared memory      :a4, after a3, 6w
    Human-in-loop learning          :a5, after a4, 4w

    section Caregiver Layer
    Caregiver intelligence          :a6, after a5, 6w
```

### Phase breakdown

  ------------------------------------------------------------------------
  Phase                   Target                  Exit criterion
  ----------------------- ----------------------- ------------------------
  0 --- Foundation        Architecture + data     Team can explain
                          model                   observation → event →
                                                  query

  1 --- Single-camera MVP Last-seen retrieval     One object reliably
                                                  returns
                                                  location/time/evidence

  2 --- Reliable memory   Event compression +     Stable timelines over
                          confidence              longer sessions

  3 --- Multi-camera      Shared cross-camera     One object timeline
                          memory                  spans rooms/cameras

  4 --- Learning          Human clarification +   Ambiguities can be
                          permissions             corrected and remembered

  5 --- Caregiver         Higher-level questions  System supports selected
  intelligence                                    care workflows

  6 --- Platform          Broader memory engine   Additional sensors/apps
                                                  can use same core
  ------------------------------------------------------------------------

A solo, part-time **research-grade MVP** is reasonably planned as a
multi-month project; production reliability is a substantially larger
effort.

------------------------------------------------------------------------

## 21. Success Metrics

Do not measure progress by feature count.

Measure the number of **caregiver questions answered reliably**.

### Capability ladder

1.  **Where was this object last seen?**
2.  **Show me this object's timeline today.**
3.  **Who last handled this object?**
4.  **What important objects are currently visible in this room?**
5.  **What did Dad interact with today?**
6.  **What expected item appears to be missing?**
7.  **Was medication likely handled/taken, and what evidence supports
    that?**

Each new question should become a measurable system milestone.

### Example evaluation dimensions

  Metric                    Meaning
  ------------------------- --------------------------------------------
  Last-seen accuracy        Correct object + meaningful location
  Timestamp error           Difference from ground truth
  Instance-ID accuracy      Correct specific watch/wallet/etc.
  Cross-camera continuity   Correct identity across cameras
  False-memory rate         Incorrect events stored as facts
  Retrieval latency         Time to answer a query
  Clarification frequency   How often humans are interrupted
  Evidence coverage         Answers supported by snapshot/clip
  User trust                Caregiver assessment of answer reliability

------------------------------------------------------------------------

## 22. Major Technical Challenges

### 1. Specific-object recognition

Recognizing **Dad's black wallet** rather than merely **a black
wallet**.

### 2. Cross-camera identity

Maintaining the same object/person identity when appearance, angle,
lighting, and camera change.

### 3. Occlusion

The object may disappear into a hand, pocket, drawer, or bag.

### 4. Semantic location

Converting pixels into human concepts:

``` text
x=382, y=220
```

is much less useful than:

``` text
Living Room → Coffee Table
```

### 5. Long-term memory scale

Raw video grows rapidly. Structured memory must remain compact and
searchable.

### 6. Uncertainty

A system that confidently stores a false event can corrupt future
answers.

### 7. Human interruption

Continuous clarification would make the system unusable.

### 8. Privacy

The application handles sensitive in-home visual data.

### 9. Evaluation

A research prototype must prove that its memories and answers are
actually correct.

------------------------------------------------------------------------

## 23. Startup / Company Perspective

### Positioning

Avoid positioning the company merely as:

> "an AI camera company."

A stronger technical framing is:

> **A visual memory platform that turns continuous sensor streams into
> evidence-backed, searchable memory.**

Alzheimer's and elderly care can be the first high-value application.

Potential later domains: - aging in place - smart homes - assistive
robotics - inventory/location memory - warehouses - household automation

### Early technical team

  -----------------------------------------------------------------------
  Role                                Core skill
  ----------------------------------- -----------------------------------
  Computer Vision / ML Engineer       Detection, tracking, embeddings,
                                      VLMs

  Backend / Data Engineer             Event systems, databases, APIs,
                                      search

  Embedded / IoT Engineer             Cameras, networking, edge
                                      deployment

  Frontend / Product Engineer         Caregiver dashboard and workflows

  Product/UX Designer                 Low-friction caregiver experience

  Clinical / Care Advisor             Real-world workflow and safety
                                      guidance

  Technical Founder / Architect       System integration and product
                                      direction
  -----------------------------------------------------------------------

A very early prototype does **not** require all of these as full-time
hires.

------------------------------------------------------------------------

## 24. Architecture Principles to Protect

### 1. Separate perception from memory

``` text
VLM / detector = “What do I see?”
Memory service = “What should I remember?”
Query layer = “What does the user want to know?”
```

### 2. Make perception replaceable

Models will improve. Historical memory should survive model changes.

### 3. Preserve provenance

Every important claim should be traceable to: - camera - timestamp -
confidence - snapshot/clip - model/version if useful

### 4. Append history; derive state

Do not make `current_location` the only truth.

### 5. Human meaning beats pixel precision

"Coffee table" is more useful than bounding-box coordinates.

### 6. Uncertainty is a first-class state

Unknown is an acceptable answer.

### 7. Build from questions backward

Do not add a knowledge graph because it sounds sophisticated. Add it
when a real caregiver question requires it.

------------------------------------------------------------------------

## 25. One-Slide Stakeholder Version

### The problem

Home cameras record everything but **remember nothing useful**.

### The solution

An AI visual memory layer that converts camera streams into structured,
searchable memories.

### First use case

A caregiver asks:

> **"Where was Dad's watch last seen?"**

and receives:

> **"Last visually confirmed on the living-room coffee table at 7:05
> PM."**

with the supporting snapshot.

### Why it matters

Caregivers spend less time reconstructing routine events from memory or
video footage.

### Technical differentiation

-   Multi-camera shared memory
-   Specific-object identity
-   Event-based semantic memory
-   Evidence-backed answers
-   Human-in-the-loop learning
-   Explicit uncertainty instead of guessing

### Long-term opportunity

A reusable **visual memory engine** for assistive care, smart homes, and
embodied AI.

------------------------------------------------------------------------

## 26. Recommended Repository Structure

``` text
visual-memory-engine/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── data-model.md
│   ├── event-model.md
│   ├── privacy.md
│   └── evaluation.md
├── services/
│   ├── memory/
│   ├── perception/
│   └── query/
├── apps/
│   └── caregiver-web/
├── experiments/
│   ├── object-identity/
│   └── event-compression/
├── tests/
│   ├── fixtures/
│   └── scenarios/
└── docker/
```

------------------------------------------------------------------------

## 27. Immediate Next Decision

Before expanding the AI stack, formalize this pipeline:

``` mermaid
flowchart LR
    A[Object Profile] --> B[Observation]
    B --> C[Event]
    C --> D[Memory]
    D --> E[Query Result]
    E --> F[Evidence]
```

For every box, answer:

1.  What data enters?
2.  What data leaves?
3.  What gets a permanent ID?
4.  What can change?
5.  What must never be silently overwritten?
6.  What evidence supports the result?
7.  What happens when confidence is low?

That design becomes the contract for the first memory service.

------------------------------------------------------------------------

## 28. North Star

> **The system should not try to remember everything. It should preserve
> the smallest amount of trustworthy evidence needed to answer important
> human questions.**

That principle keeps the architecture useful, explainable, scalable, and
aligned with the caregiver experience.
