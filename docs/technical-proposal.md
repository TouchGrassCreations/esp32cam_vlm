# Technical proposal: evidence-backed household memory

[README](../README.md) · [Solution architecture](solution-architecture.md) · [Sizing and BOM](sizing-and-bom.md)

**Proposal date:** 2026-09-03  
**Decision requested:** proceed with a one-household, one-camera research pilot using existing hardware. Additional cameras and cloud services depend on validation gates. This document is a design proposal, not a claim that the pilot capabilities already exist.

## 1. Executive proposition

Build a Visual Memory Engine that helps a caregiver answer **“Where was this registered object last seen?”** with a location, timestamp and image evidence.

The current repository establishes the sensing-to-caption path. The proposed work adds durable observations, object registration, event memory and evidence retrieval, then evaluates whether those features reduce the effort of finding household items.

**Technical value proposition:** convert camera observations into structured, traceable memory, using a local gateway for collection and persistence and selected cloud reasoning when necessary.

**Business value proposition:** help caregivers find useful context more quickly, while controlling how much household imagery is retained or sent to a provider.

## 2. Problem and users

A camera image records a moment but does not by itself provide a reliable history of a particular watch, wallet or pair of glasses. Users must reconstruct where an item was visible and whether that information is still relevant.

The primary pilot user is an approved household caregiver. The resident's preferences, privacy and ability to pause collection are part of the design. Start in a consented shared space with several registered items and clearly labeled landmarks.

Example target answer:

> “The registered watch was last confirmed on the living-room coffee table at 8:05 PM. Here is the snapshot. Its current location is unknown.”

The answer must remain historical if the camera later loses sight of the object.

## 3. Proposed scope and deliverables

| In the first pilot | Later, subject to evidence |
|---|---|
| One camera and 3–5 registered items | Multi-camera instance continuity |
| Manual room/landmark registration | More automated location mapping |
| Durable observations and compressed events | Episodic summaries and semantic search |
| Last-seen result with timestamp and snapshot | Caregiver notifications |
| Unknown/ambiguous states and correction | Medication-interaction or routine context |
| Retention, health status and restart recovery | Environmental sensors and fleet services |

Deliverables are a reproducible deployment configuration, memory schema/API, simple caregiver query interface, labeled evaluation set, reliability results, cost measurements and an updated architecture decision record.

Medication adherence, fall detection, reliable stove-state detection, diagnosis and guaranteed safety monitoring are outside this pilot. Sparse snapshots can miss short actions; a missing detection does not establish absence or safety.

## 4. Recommended solution

Use ESP32-CAM as the sensing node and evaluate the existing J1010 as the gateway. FastAPI accepts frames, a durable worker processes them, SQLite stores observations/events, and a USB SSD stores retained evidence.

Perception stays replaceable: use cloud VLM descriptions initially with structured validation and human review, then assess whether lightweight local filtering/detection reduces cost without losing important observations. Object-category detection alone does not solve registered-item identity.

Implement the local-first option, then selectively add cloud synchronization for caregiver access. The existing [product brief](../visual_memory_engine_project_brief.md) describes the longer-term memory platform; the [architecture](solution-architecture.md) translates that into interfaces and failure behavior.

## 5. Value hypotheses and how to test them

| Stakeholder value | Technical mechanism | Pilot evidence |
|---|---|---|
| Less time looking for objects | Indexed last-seen retrieval | Time-to-answer versus manually browsing the same evidence |
| More trustworthy context | Snapshot, source time and explicit uncertainty | Evidence coverage and false-memory audit |
| Less repetitive camera review | Event compression and useful summaries later | Relevant observations retrieved per session |
| Greater control over imagery | Local retention and selective upload | Images retained/sent, deletion test and user preferences |
| Predictable operating costs | Admission limits and VLM budget caps | Actual calls, bytes and cost per useful answer |
| Easier maintenance | Replaceable perception and versioned schemas | Swap provider without losing historical records |

These are hypotheses, not demonstrated savings, clinical outcomes or market demand. Research interviews and pilot use should determine whether caregivers value this feature enough to continue.

### Comparison of approaches

| Approach | Strength | Limitation to evaluate |
|---|---|---|
| Manual search of saved images/video | Direct visual evidence | User time and search effort |
| Caption every frame | Simple proof of concept | Repetition, inference cost and weak temporal identity |
| Proposed visual memory | Structured retrieval with provenance | Identity matching and false-memory risk |
| Purpose-built item tag | Direct signal for tagged objects | Requires tagging and a different location infrastructure |

Evaluate the smallest solution that answers the actual household question. Visual memory is most useful where image context adds value beyond a simple item tag.

## 6. Delivery plan and ownership

The following is a **60–100 engineering-hour planning allowance**, excluding hardware lead times and calendar soak duration. It is not a fixed-price or calendar commitment. At 5–8 hours/week, allow approximately 8–20 weeks, with extra time if runtime or object-identity experiments fail.

| Phase | Work | Effort assumption | Exit evidence |
|---|---|---:|---|
| 0: baseline | Measure current path, verify gateway/runtime and storage | 6–10 h | Recorded environment, sample sizes and latency |
| 1: reliable sensing | Durable acknowledgment, IDs, retries, health and retention | 16–24 h | Restart/outage tests; bounded storage and backlog |
| 2: memory loop | Registration, observations/events and last-seen retrieval | 20–32 h | Correct deterministic queries before perception integration |
| 3: perception evaluation | Identity candidates, confidence rules and human correction | 12–22 h | Held-out labeled scenarios and failure analysis |
| 4: household pilot | UI refinement, backup restore, user trials and report | 6–12 h | Seven-day soak plus acceptance results |

One developer can cover the initial implementation, supported by a household caregiver who helps define meaningful locations, consent boundaries and labels. Additional CV expertise may be needed if instance identity is the bottleneck. Clinical review becomes relevant only if future claims enter clinical workflows.

After phase 1, stop expanding hardware if the existing host cannot run the baseline reliably. After phase 3, narrow the object set or improve camera placement if precision/coverage is insufficient.

## 7. Pilot acceptance criteria

Targets below are proposed gates, not current results or service-level guarantees.

| Metric | Definition and proposed target |
|---|---|
| Ingestion success | At least 98% of scheduled capture opportunities durably accepted in a seven-day trial; report all outages and failure causes |
| Local service availability | At least 99% of one-minute probes succeed during the trial; planned tests reported separately |
| Acceptance latency | p95 under 1 second from LAN upload start to durable 202 |
| Local processing latency | p95 under 5 seconds from acceptance to local event outcome; cloud delay reported separately |
| Query latency | p95 under 3 seconds for stored last-seen retrieval, excluding new inference |
| Evidence coverage | 100% of asserted answers reference available evidence or clearly state that it expired |
| Answer precision | At least 90% correct item/location/time among asserted answers on held-out scenarios |
| Answer coverage | At least 70% of eligible in-view test cases receive a correct asserted answer; prevents “always unknown” from passing |
| False memory | At most 5% of accepted factual events incorrect on manual audit; report sample count |
| Recovery | No unexplained loss of acknowledged jobs through controlled restarts; backup restoration demonstrated |
| User value | Target median task time at least 30% lower than manual image search on matched cases |

These targets are appropriate to a **research go/no-go discussion**, not safety deployment. Even a 5% false-memory rate can be unacceptable for care decisions; do not reuse it as an alert acceptance threshold.

Evaluation protocol:

1. Prepare at least 100 labeled episodes across 3–5 objects, multiple lighting conditions and placements, including similar-looking distractors and occlusion.
2. Include at least 20 negative/unknown cases where the item is outside view or identity is ambiguous.
3. Reserve held-out episodes for evaluation; do not tune on the final set. Record object identity, landmark, latest visible time and evidence.
4. Score item, location and timestamp separately. Use a tolerance of one configured sampling interval for observed time; distinguish events that happen between captures from processing failures.
5. Test ten or more matched caregiver search tasks, recording median time and failures. Do not generalize a small household pilot to a population.
6. Report counts and uncertainty, abstentions, filtering misses and subgroup failures. Keep any human-assisted results separate from automatic performance.

The current firmware does not expose all counters needed for these metrics; instrumentation is part of phase 1.

## 8. Risks, mitigations and decision triggers

| Risk | Mitigation | Decision trigger |
|---|---|---|
| Small or occluded objects | Closer views, controlled landmarks and explicit unknown states | Narrow objects or change camera when coverage fails |
| Confident wrong identity | Registered references, provenance and human review | Block automatic memory acceptance if precision fails |
| J1010 software/RAM limits | Benchmark legacy runtime early; retain laptop fallback | Evaluate supported mini PC or Orin-class gateway |
| Provider outage or cost | Local history, bounded retries and application caps | Reduce semantic escalation or choose another validated provider |
| Storage/power failure | SSD mount guard, retention, recovery tests and independent backup | Resolve failures before unattended use |
| Privacy or resident discomfort | Placement agreement, pause/delete controls, minimal upload | Suspend household pilot if acceptable controls cannot be met |
| Excessive user interruptions | Queue low-priority clarifications; measure burden | Simplify identity scope before adding alerts |
| Maintenance overhead | Versioned configuration and limited service count | Include support hours in platform choice |

The J1010 is a reusable pilot asset, not a default commercial hardware commitment. Lifecycle and compatibility decisions are documented in [sizing and BOM](sizing-and-bom.md).

## 9. Commercial path and economics

Potential later offerings include a household gateway plus application subscription, an installation/support service, or a visual-memory component integrated into another care platform. These are business-model options requiring demand validation.

Before pricing, establish:

- Who pays, who installs, who maintains, and who may access household evidence.
- Hardware replacement, installation and support hours per household.
- Cloud inference/storage cost per household and cost per successful answer.
- Whether recurring usage and caregiver time savings justify a subscription.
- Security, privacy and applicable legal review before external deployment.
- Whether a supported non-GPU gateway is sufficient when most reasoning is cloud based.

A budget model should include hardware amortization, field support, compute/storage, notifications and payment overhead. No revenue forecast, market-size estimate or ROI guarantee is supported by this prototype.

## 10. Proposed next action

Implement and demonstrate the memory contract first with deterministic observations: an item on a table, then in a hand, then no longer visible. The query must return the last supported observation and its evidence without inventing a current location.

Connect camera perception only after that behavior works. This isolates memory correctness from model quality and produces a reviewable milestone: **one registered item, one reliable historical answer, one supporting snapshot.**
