"""Project Wayland — Elbow Module v1 : single-joint control sandbox.

Tune the v1 control stack BEFORE hardware exists:
  1. Gravity compensation  -> arm feels weightless (cancel qfrc_bias)
  2. Admittance assist      -> motor adds `alpha` * the wearer's own effort

The wearer's muscles are modeled as `tau_human(t)` injected on the joint via
qfrc_applied (this is what a forearm-cuff load cell would measure). The motor commands
tau_grav + alpha*tau_human, clamped to the firmware torque limit. We then measure the
*effort multiplier*: how much less the wearer works to produce the same motion.

Run:  python sim_elbow.py            # writes ./out/elbow_tuning.png + run.json
"""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import mujoco

logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("wayland.elbow.sim")


@dataclass
class Gains:
    alpha: float = 2.0        # admittance assist gain (motor adds alpha * human effort)
    tau_max: float = 40.0     # N*m firmware clamp (matches actuator ctrlrange)
    duration: float = 6.0     # s
    grav_comp: bool = True


def tau_human(t: float) -> float:
    """Modeled wearer intent torque (N*m), as a cuff load cell would sense it.

    Phase A (0-2s):   relax, hold position        -> 0
    Phase B (2-4s):   curl the load up            -> ramped flexor effort
    Phase C (4-6s):   hold the curled position    -> small steady effort
    Sign: negative torque flexes (curls up), matching the joint range.
    """
    if t < 2.0:
        return 0.0
    if t < 4.0:
        return -6.0 * (t - 2.0) / 2.0      # ramp to -6 N*m of human effort
    return -3.0                             # steady hold effort


def simulate(g: Gains, model_path: Path):
    m = mujoco.MjModel.from_xml_path(str(model_path))
    d = mujoco.MjData(m)
    jid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "elbow")
    dof = m.jnt_dofadr[jid]
    aid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, "elbow_mot")

    # start hanging at rest near horizontal so gravity is doing real work
    d.qpos[dof] = 0.0
    mujoco.mj_forward(m, d)

    log = {k: [] for k in ("t", "angle_deg", "vel", "human", "grav", "assist", "motor")}
    n = int(g.duration / m.opt.timestep)
    for _ in range(n):
        th = tau_human(d.time)
        d.qfrc_applied[dof] = th                       # the wearer's muscles

        tau_grav = d.qfrc_bias[dof] if g.grav_comp else 0.0   # cancels gravity+coriolis
        tau_assist = g.alpha * th
        tau_motor = float(np.clip(tau_grav + tau_assist, -g.tau_max, g.tau_max))
        d.ctrl[aid] = tau_motor

        for k, v in (("t", d.time), ("angle_deg", np.degrees(d.qpos[dof])),
                     ("vel", d.qvel[dof]), ("human", th),
                     ("grav", tau_grav), ("assist", tau_assist), ("motor", tau_motor)):
            log[k].append(v)
        mujoco.mj_step(m, d)

    return {k: np.asarray(v) for k, v in log.items()}


def effort_multiplier(res) -> float:
    """During active curl (phase B), total joint torque the wearer *feels* assisted by."""
    mask = (res["t"] >= 2.0) & (res["t"] < 4.0)
    human = np.abs(res["human"][mask])
    assist = np.abs(res["assist"][mask])
    human_work = human.sum()
    if human_work < 1e-6:
        return 1.0
    return float((human.sum() + assist.sum()) / human_work)


def plot(res, g: Gains, out: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

    ax1.plot(res["t"], res["angle_deg"], color="#2b6cb0", lw=2)
    ax1.axhspan(-145, 5, color="#2b6cb0", alpha=0.04)
    ax1.set_ylabel("elbow angle (deg)")
    ax1.set_title(f"Wayland elbow — gravity comp + admittance (alpha={g.alpha}, "
                  f"effort multiplier x{effort_multiplier(res):.1f})")
    for x in (2.0, 4.0):
        ax1.axvline(x, color="k", ls=":", lw=0.8)
    ax1.text(1.0, ax1.get_ylim()[1]*0.9, "hold", ha="center", fontsize=9)
    ax1.text(3.0, ax1.get_ylim()[1]*0.9, "curl", ha="center", fontsize=9)
    ax1.text(5.0, ax1.get_ylim()[1]*0.9, "hold", ha="center", fontsize=9)

    ax2.plot(res["t"], res["human"], label="human effort", color="#c05621", lw=2)
    ax2.plot(res["t"], res["grav"], label="gravity comp", color="#2f855a", lw=1.5, ls="--")
    ax2.plot(res["t"], res["assist"], label="assist", color="#6b46c1", lw=1.5)
    ax2.plot(res["t"], res["motor"], label="motor total", color="#1a202c", lw=2)
    ax2.axhline(g.tau_max, color="r", ls=":", lw=0.8)
    ax2.axhline(-g.tau_max, color="r", ls=":", lw=0.8)
    ax2.set_ylabel("torque (N*m)"); ax2.set_xlabel("time (s)")
    ax2.legend(loc="upper left", ncol=2, fontsize=8)
    plt.tight_layout(); plt.savefig(out, dpi=120, bbox_inches="tight")
    logger.info("plot written", extra={"path": str(out)})


def main():
    here = Path(__file__).parent
    out = here / "out"; out.mkdir(exist_ok=True)
    g = Gains()
    res = simulate(g, here / "elbow.xml")

    hold_torque = float(np.abs(res["grav"][res["t"] < 2.0]).mean())
    summary = {
        "gains": asdict(g),
        "effort_multiplier": round(effort_multiplier(res), 2),
        "static_hold_motor_torque_Nm": round(hold_torque, 2),  # = continuous holding cost
        "peak_motor_torque_Nm": round(float(np.abs(res["motor"]).max()), 2),
        "final_angle_deg": round(float(res["angle_deg"][-1]), 1),
        "hit_torque_limit": bool(np.any(np.abs(res["motor"]) >= g.tau_max - 1e-6)),
    }
    (out / "run.json").write_text(json.dumps(summary, indent=2))
    logger.info("summary %s", json.dumps(summary))
    plot(res, g, out / "elbow_tuning.png")


if __name__ == "__main__":
    main()
