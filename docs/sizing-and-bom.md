# Sizing and bill of materials

[README](../README.md) · [Architecture](solution-architecture.md) · [Proposal](technical-proposal.md)

**As of 2026-09-03.** Hardware specifications below are sourced; workload figures are explicit planning assumptions, not measured J1010 benchmarks or supplier quotations.

## 1. Hardware baseline and platform choice

| J1010 constraint | Design implication |
|---|---|
| Jetson Nano production module, 4 GB shared RAM, 16 GB eMMC | Keep OS on eMMC; budget model, API and buffers together |
| One USB 3.0 Type-A port; Gigabit Ethernet | Use USB SSD for data and Ethernet for the gateway |
| M.2 Key E, no M.2 Key M | A bare NVMe SSD cannot be installed directly in the carrier |
| USB-C 5 V / 3 A input | Use a suitable regulated supply and cable |
| microSD added to units ordered after July 30, 2022 | Inspect the actual carrier revision before buying a card |

These specifications come from [Seeed's J1010 guide](https://wiki.seeedstudio.com/reComputer_J1010_with_Jetson_getting_start/). A Key E slot does not mean a Wi-Fi module is already fitted. Ethernet avoids needing a wireless adapter for this project.

Seeed lists the J10 product as discontinued and recommends migration to an Orin platform. Reuse the owned unit for the pilot; do not base new fleet procurement on it. [Seeed product notice](https://www.seeedstudio.com/Jetson-10-1-A0-p-5336.html)

NVIDIA's archive lists Nano support in the JetPack 4.6.x family, including 4.6.6. Do not assume modern JetPack, PyTorch, Python wheels or model export packages will run unchanged. Record the installed L4T/JetPack, Python, CUDA and inference runtime, then prove a compatible environment before migrating the service. [NVIDIA JetPack archive](https://developer.nvidia.com/embedded/jetpack-archive)

## 2. Recommended starting envelope

| Stage | Cameras and cadence | Processing | Gate |
|---|---|---|---|
| Baseline | 1 camera, target 10-second sampling | Ingest, persistence, cloud provider; no detector required | Stable restart and 24-hour soak |
| Initial edge pilot | 1 camera, then 2–3 if measured | Bounded worker, filtering, one small compatible detector if useful | RAM, latency, accuracy and backlog pass |
| Expansion experiment | 4–6 low-frequency cameras | Sequential inference and tighter admission limits | Separate load test; no supported-capacity claim |
| Product stage | Determined by measured workloads | Supported gateway or cloud-oriented host | Lifecycle, support cost and multi-household requirements |

Start from the current VGA capture size. Higher-resolution evidence may improve small-item visibility, but requires firmware changes and measured image/network costs. Do not equate video decoder capability with AI inference capacity.

## 3. Frame and storage model

Use decimal units: 1 kB = 1,000 bytes; 1 GB = 1,000,000,000 bytes.

Let N be camera count, T the target interval in seconds, S the **saved** JPEG size in kB, r the retained fraction, and D retention days.

```text
frames/day             = N × 86,400 / T
image GB/day           = frames/day × S / 1,000,000
retained image GB       = image GB/day × r × D
provisioned data GB     = (retained images + metadata + queue + backups) / 0.8
```

The 0.8 factor reserves 20% of the data volume. It does not include OS usage or an independent backup device.

**Continuous-retention scenario: T = 10 s, S = 250 kB, r = 1.**

| Cameras | Frames/day | Image GB/day | Image GB/30 days |
|---:|---:|---:|---:|
| 1 | 8,640 | 2.16 | 64.8 |
| 2 | 17,280 | 4.32 | 129.6 |
| 3 | 25,920 | 6.48 | 194.4 |
| 4 | 34,560 | 8.64 | 259.2 |

250 kB is a sizing scenario, not the measured size of this repository's VGA JPEGs. Measure saved files after normalization; use upload sizes separately for network sizing. At 100/250/500 kB, one camera's 30-day archive is 25.92/64.8/129.6 GB respectively.

The present firmware waits 10 seconds **after** an upload. These figures model a future fixed cadence and are an upper planning baseline for the present loop, not an assertion of current throughput.

### Proposed retention policy

- Latest frames: short rolling buffer with a per-camera byte cap.
- Low-value/unselected snapshots: expire within 24 hours, or sooner under disk pressure.
- Selected event evidence: begin with 30 days, configurable by the household.
- Metadata: begin with 90 days; mark expired evidence explicitly.
- Calibration/review samples: bounded subset of rejected candidates to measure filtering errors.
- Backups: daily metadata and selected evidence to an independent destination.

If each camera retains 1,000 images/day at 250 kB, one camera uses 7.5 GB/30 days; three use 22.5 GB. That is **88.4% fewer images** than retaining 8,640/day. Retention reduction is not automatically the VLM-call reduction: filtering, detection and semantic escalation have different rates.

Example three-camera provision: 22.5 GB selected evidence + 6.48 GB one-day raw buffer + 5 GB metadata/queue/local operational allowance = 33.98 GB; divide by 0.8 = **42.48 GB** before independent backups. Confirm that the 5 GB allowance matches measured logs/indexes. A 256 GB SSD offers headroom without implying that all of it should be filled.

## 4. RAM and worker utilization

Illustrative **peak planning allocation**, in MiB:

| Component | Allocation |
|---|---:|
| Headless OS and system services | 1,200 |
| API, dashboard serving and SQLite | 300 |
| One detector runtime/model | 1,000 |
| Image decode buffers and worker | 250 |
| Network and bounded pending buffers | 150 |
| Target available headroom | 600 |
| Total | 3,500 |

Actual usable RAM is below the nominal 4 GB after reservations. This allocation is a hypothesis: stop adding work if real available memory is below the target, swap activity persists or the model needs more memory. Buffers can overlap runtime accounting, so validate total system memory as well as process RSS. Do not run a local VLM alongside this assumed detector budget.

For a sequential worker:

```text
utilization = (N / T) × mean local processing seconds per frame
```

At 3 cameras / 10 seconds and 1 second per frame, utilization is 0.30. At 4 seconds per frame it is 1.20, so the backlog grows indefinitely. Target under 0.60 sustained utilization to allow bursts, then measure p95 latency. Cloud calls need a separate bounded path: a slow API must not occupy the only local-processing worker.

Begin with a supported lightweight detector only after an import/inference smoke test on the exact JetPack runtime. Do not promise that “YOLO nano” or an embedding model will fit merely because its weights are small.

## 5. Network and inference-cost sizing

With **250 kB uploaded** every 10 seconds, mean payload traffic is 0.2 Mbit/s/camera, or 0.6 Mbit/s for three cameras. Provision additional capacity for TCP/HTTP overhead, retries and synchronized bursts. Wi-Fi reliability and reception can matter more than this average. Use 2.4 GHz camera Wi-Fi and wire the J1010 to the router where possible.

Let q be the fraction of captured frames sent to cloud AI, and P the total effective provider price per image request, including input/output usage.

```text
cloud calls/month = N × (86,400 / T) × 30 × q
monthly AI cost  = cloud calls/month × P
```

For three cameras at 10 seconds:

| Cloud escalation q | Calls/month | Illustrative cost at P = USD 0.001 |
|---:|---:|---:|
| 100% | 777,600 | USD 777.60 |
| 10% | 77,760 | USD 77.76 |
| 1% | 7,776 | USD 7.78 |

**USD 0.001 is an arithmetic example, not a provider quote.** Add query-time calls, summaries, retries, hosting, storage and messaging separately. Actual image tokenization, model selection and output length affect cost. Set daily/monthly application caps; do not rely on a free model being continuously available.

At q = 1%, 250 kB per cloud image and three cameras, image payload upload is about 1.944 GB/month, excluding protocol overhead. Provider payload size may differ from stored JPEG size.

## 6. Storage deployment

**Recommended:** one 256–512 GB USB 3 SSD, mounted as a persistent data volume. Keep it connected while services use it; it is not necessary just to boot the J1010 from its existing eMMC.

Use a filesystem and USB enclosure validated for the device. For the Linux pilot, propose ext4 and mount by UUID. Require the mount before service startup and fail visibly if it is missing. Keep evidence, DB and queue on the data volume; put independent backups elsewhere.

Seeed's legacy USB expansion tutorial recommends no more than 512 GB and discusses peripheral-current/power stability constraints. That tutorial changes root storage; it is not proof of a universal 512 GB hardware addressing limit, nor is moving the OS required for this application's data volume. Test the chosen SSD's peak draw and USB behavior. [Seeed storage guide](https://wiki.seeedstudio.com/reComputer_Jetson_Memory_Expansion/)

A microSD card is optional, conditional on the carrier revision. It is not an additional mandatory purchase when an SSD already meets the data requirement. An SSD improves storage capacity and I/O; it does not add RAM or GPU performance.

## 7. Bill of materials

No live supplier quotations are included. Quantities and specifications form a procurement checklist; prices require regional availability, warranty and shipping checks before purchase.

### One-camera pilot

| Component | Qty | Status / priority | Specification and purpose |
|---|---:|---|---|
| J1010 4 GB | 1 | Already owned; reuse | Edge gateway after compatibility validation |
| ESP32-CAM with OV2640 | 1 | Already owned; reuse | Initial camera; verify board and PSRAM |
| Laptop | 1 | Existing development host | Setup, debugging and fallback |
| J1010 PSU and cable | 1 | Verify existing supply first | Regulated 5 V / 3 A USB-C, correct power port |
| Camera supply/cable | 1 | Required per camera | Stable 5 V supply appropriate to exact board; allow Wi-Fi burst margin |
| USB 3 SSD and cable/enclosure | 1 | First storage purchase if needed | 256–512 GB, tested power draw and Linux operation |
| Ethernet cable | 1 | Required for recommended layout | Gateway-to-router LAN connection |
| Router/access point | 1 | Reuse existing | Reliable 2.4 GHz camera coverage |
| USB serial programmer | 1 shared | Only if not already available | Compatible with camera flashing and logic levels |
| Camera mount/enclosure | 1 | Deployment requirement | Stable view and safe cable routing |

### Reliability and three-camera expansion

| Addition | Incremental qty | Trigger |
|---|---:|---|
| ESP32-CAM nodes | 2 | Only after one-camera accuracy and capacity pass |
| Camera supplies, cables, mounts | 2 sets | Required with additional cameras |
| UPS | 1 | Size for measured loads and desired runtime |
| Independent backup destination | 1 | Required before valuable history accumulates |
| Powered USB hub | 0–1 | Only if tested SSD/peripheral power needs it; avoid backfeed |
| Active cooling | 0–1 | Add if measured thermal throttling occurs |
| High-endurance microSD | 0–1 | Optional alternative/secondary medium after revision check |
| Environment/contact sensor nodes | As scoped | Separate validated sensor use case, not initial last-seen BOM |

For three camera nodes, buy only two additional nodes if the existing one is suitable. Do not count an extra 500 GB SSD on top of a 256–512 GB drive without a retention need.

### Future platform candidates

| Candidate | When to evaluate | Selection criteria |
|---|---|---|
| Supported Jetson Orin-family gateway | More local CV/embeddings needed | RAM, supported JetPack, sustained inference and lifecycle |
| Supported mini PC | Workload is mostly API, DB and cloud AI | Maintenance, RAM, storage, power and total cost |
| Higher-quality IP cameras | Small-item visibility or room coverage limits ESP32 | Lens/detail, accessible documented stream/API, privacy controls |

No assumption is made that an existing consumer camera exposes a usable local API or stream. Prove integration before including it in the supported BOM.

## 8. Power and operating budget

Measure gateway, SSD, router and camera wall power under load. A 5 V / 3 A supply rating is not a measured 15 W steady consumption.

For an illustrative combined 30 W load:

```text
energy/month = 30 W × 24 h × 30 / 1,000 = 21.6 kWh
UPS battery energy for 30 min at 80% efficiency = 30 × 0.5 / 0.8 = 18.75 Wh
```

18.75 Wh is a theoretical minimum before aging/reserve and discharge behavior. Select using the manufacturer's runtime curve and measured watts, not VA alone. Protect the router, relevant camera supplies, and modem/ONT if Internet continuity matters. Keeping only the gateway alive does not preserve camera acquisition or remote access.

Total pilot cost is incremental hardware + installation effort + electricity + provider usage + backup/cloud costs + maintenance time. Reusing equipment reduces purchase cost but does not remove support effort.

## 9. Benchmark and upgrade gates

Record these on the physical J1010 before declaring a supported configuration:

1. Exact carrier revision, OS/L4T/JetPack, Python/runtime, SSD model and power arrangement.
2. One-camera 24-hour run, then seven-day soak including provider delay/outage and service restarts.
3. Capture intervals, saved/upload JPEG size distributions, acceptance failures and processing success separately.
4. Available RAM, swap activity, thermals/throttling, queue age, p95 ingest and local-processing latency.
5. Disk-full/missing-volume behavior, retry deduplication and backup restoration.
6. Registered-object precision, missed observations and filtering recall using labeled examples.

Proposed performance gates: p95 durable upload acknowledgment under 1 second on LAN; p95 local event processing under 5 seconds; at least 600 MiB available RAM under representative load; stable bounded queue; no unresolved data corruption. Cloud interpretation latency is measured separately.

Upgrade or reduce scope when these gates fail after basic tuning, the required model cannot run on the supported runtime, or operating the legacy stack costs more than replacing the host. Camera count is a consequence of these measurements, not a specification inferred from RAM alone.
