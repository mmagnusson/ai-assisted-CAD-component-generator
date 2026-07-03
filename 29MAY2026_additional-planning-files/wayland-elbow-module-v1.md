# Project Wayland — Elbow Module v1 (`WAYLAND-EM-01`)

The first unit cell of a modular power-augmentation exosuit. Goal: a single backdrivable
powered elbow joint that **measurably augments** (hold/curl a load with a fraction of the
effort), built fast, and designed so the suit later becomes N copies of this module on a
shared bus + a coordinator.

**Three constraints this design serves:** ship something real, iterate in evenings,
extend later without redesign.

---

## 0. The shortcut — fork, don't design

Do **not** design the actuator from scratch. Fork an open QDD reference and adapt the
structure around it:

- **OpenQDD** (Aaed Musa) — open-source quasi-direct-drive actuator: 90KV pancake BLDC +
  ODrive S1 + low-ratio planetary. This is the drivetrain, solved.
- **TOPS** (Hackaday) — quadruped using Eaglepower 8308 90KV motors + ODrive S1 over CAN,
  good reference for CAN node setup and clamp-style housing mounts.

You are building the *exo structure + control + safety* around a known-good actuator, not
reinventing motor control.

---

## 1. Sizing (the gating calc)

Static torque at the elbow, forearm horizontal (worst case):

```
T_elbow = m_load · g · L_forearm  +  m_forearm · g · L_cg
```

| Term            | Value                    | Torque    |
|-----------------|--------------------------|-----------|
| 10 kg @ 0.30 m  | 10 · 9.81 · 0.30         | 29.4 N·m  |
| forearm+hand    | ~1.6 kg · 9.81 · 0.15 m  | ~2.4 N·m  |
| **Total**       |                          | **~32 N·m** |

**Design targets** (suit shares load with wearer, so < full support is fine and safer):
- Peak: **35–40 N·m**
- Continuous assist: **15–20 N·m**
- Range of motion: **0°–145°** flexion (hard-stopped)
- Speed: elbow flexion in normal use ~few rad/s — trivial for a QDD actuator

**Actuator:** forked OpenQDD-class — 90KV pancake BLDC + planetary **6–8:1** (keep < 10:1
to stay backdrivable) + ODrive S1, torque control over CAN.

> **The QDD tradeoff to accept:** low ratio = no self-locking, so holding a static load
> draws current continuously. Acceptable for a demo/MVP. Endurance fix (brake/clutch) is a
> v2 concern, not a v1 blocker. Note it; don't solve it now.

---

## 2. Bill of materials (ballpark — verify current prices at purchase)

| Item | Notes | Rough $ |
|------|-------|---------|
| Pancake BLDC, ~90KV (e.g. Eaglepower 8308) | high torque density, AliExpress | ~60 |
| ODrive S1 controller | FOC torque/pos/vel, CAN, up to 12S | ~150 |
| Planetary gearset 6–8:1 | off-the-shelf or printed/belt reduction | 60–150 |
| Magnetic encoder (AS5047-class) | often pairs with S1; for output-side add a 2nd | 10–30 |
| LiPo 6S + charger | 24V is plenty for the elbow; S1 supports more | 80–120 |
| Load cell + HX711 amp | interaction-force sensing at the cuff | ~15 |
| Host MCU (Teensy 4.x or Pi) | CAN coordinator + control loop | 20–70 |
| Cuffs / bearings / straps / fasteners / filament | PETG/nylon cuffs, alu output arm | 80–120 |
| **Total** | | **~$500–800** |

Budget route: SimpleFOC + a generic BLDC driver board instead of the S1 (cheaper, more
fiddly, less safety tooling). Recommend the S1 for v1 — its torque limiting and watchdog
features are safety-relevant.

---

## 3. Mechanical architecture

A 1-DOF hinge. **Do not** augment pronation/supination in v1 — leave forearm rotation
free. The module is: upper-arm cuff → actuator at the elbow axis → forearm cuff →
load path to the hand.

**The pitfall that wrecks elbow exos: axis misalignment.** If the actuator's rotation
axis doesn't track the biological elbow axis, the cuffs migrate and bind, causing pain and
shear on the arm. The elbow's axis also isn't perfectly fixed (it shifts slightly through
flexion). Mitigations:
- A self-aligning / floating cuff interface (a slotted or sprung link between cuff and
  structure) that absorbs small misalignment.
- Generous soft padding; distribute force over area, never a point.
- Don't over-constrain — one rigid axis + compliant cuffs beats two rigid attachment points.

Materials: 3D-printed cuffs (PETG or nylon for toughness), aluminum or CF for the actuator
output arm that carries the torque, real bearings at the joint axis (not printed bushings
under load).

---

## 4. Control stack

**v1 — admittance + gravity comp (robust, no EMG):**
1. **Gravity compensation:** read elbow angle (encoder) → compute and cancel the
   forearm+suit weight torque so the arm feels weightless through its range.
2. **Admittance / interaction control:** load cell at the forearm cuff measures the
   human's intent force → command assist torque proportional to it ("help me push").
   Tune the gain = how much amplification the wearer feels.
3. Torque command → ODrive S1 in current/torque mode.

**v2 extensions (the platform is built for these):**
- EMG intent detection (biceps/triceps) for anticipatory assist.
- Online load estimation (know the held mass, scale assist).
- Adaptive gains; per-user calibration.

---

## 5. Safety architecture — non-negotiable, body-worn powered

- **Mechanical hard stops** at 0°/145° so the actuator physically cannot drive past
  anatomical limits regardless of firmware state.
- **Firmware torque/current clamp** set well below any injury threshold; start far lower
  during bring-up and raise deliberately.
- **Physical e-stop** (kill switch) reachable by the *free* hand at all times.
- **Backdrivable by design** (the < 10:1 choice): unpowered = free, human can always override.
- **Comms watchdog:** loss of host heartbeat → torque to zero (fail-to-passive).
- **First power-on is ALWAYS on the dyno**, never the arm. Low gains first.
- **Fresh-eyes safety review before the first on-body test** — a second review pass of the
  limits, e-stop wiring, and failure modes. Mandatory for this class of device, not optional.

---

## 6. Rapid-iteration loop (where the existing toolchain plugs in)

```
CAD Forge ──parametric cuffs + actuator mount──┐
                                               ▼
                              cadverify harness:
                                • clearance: actuator clears arm
                                • kinematics sweep: cuff clears through full 0–145° flexion
                                • mounting: bolt pattern matches actuator face
                                • mass_properties → feeds sim inertials
                                               │
                              MuJoCo single-joint model:
                                • tune gravity-comp + admittance gains BEFORE hardware
                                               │
                              Bench dyno fixture:
                                • known loads → characterize torque, backdrivability,
                                  holding current; set torque limits empirically
                                               │
                              Telemetry (Postgres/Grafana, ITOIP-style):
                                • log angle, current, cmd vs actual torque per run
                                • debug_export(run_id) → one-action state dump per session
```

Every loop iteration is reconstructable from the logs; bad-session/no-converge rule applies
(stop, export, fresh session) just like the SOC tooling.

---

## 7. Build order (each step produces something testable)

- [ ] **Phase 0 — actuator alive.** Fork OpenQDD; source motor + S1; one actuator spinning
      under torque control on the bench, addressable over CAN. *Deliverable: commanded N·m → measured motion.*
- [ ] **Phase 1 — dyno + characterization.** Build a single-joint dyno fixture; hang known
      loads; measure torque curve, backdrivability, holding current. Set firmware torque
      and current clamps from real data.
- [ ] **Phase 2 — sim + gains.** MuJoCo single-joint model; tune gravity-comp + admittance
      gains against the characterized actuator.
- [ ] **Phase 3 — structure.** CAD Forge cuffs + mount; run cadverify (clearance + full-ROM
      kinematics sweep + mounting); print; fit-check on the dyno with a dummy arm.
- [ ] **Phase 4 — closed-loop on dyno.** Integrate load cell; admittance control assisting a
      dummy arm + load. Verify e-stop, watchdog, hard stops all behave under fault injection.
- [ ] **Phase 5 — fresh-eyes review → first on-body.** Low gain, free hand on e-stop. The
      augmentation demo: hold/curl a load with measurably less effort.
- [ ] Iterate. Log everything.

---

## 8. How this extends to the suit (extensibility is by design, not by luck)

This module defines the template:
- **Mechanical:** the cuff-mount-bracket interface pattern → module 2 (shoulder, or a knee
  on the legs) reuses it with new CAD Forge parameters.
- **Electrical:** new joint = new CAN node on the same battery + bus.
- **Software:** new joint = same firmware, new per-joint config (limits, gravity model);
  the host coordinator gains a node, not a rewrite.
- **Sidekick crossover:** the per-module mass properties + joint definitions drop straight
  into the CAD→URDF bridge, so the same modules describe a wearable suit *or* a Sidekick limb.

Refine the unit cell. The suit is what the unit cell becomes.
