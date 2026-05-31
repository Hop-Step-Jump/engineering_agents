"""Run mock ECLSS for N steps and write telemetry JSONL."""

from __future__ import annotations

import argparse
from pathlib import Path

from core.event_log import EventLog
from environment.eclss_ops.telemetry import compute_health_metrics
from environment.protocol import AnomalySpec
from environment.ssos.mock_eclss import MockEclssSimulator


def run_mock_simulation(
    steps: int = 50,
    output_dir: Path | None = None,
    inject_scrubber_anomaly: bool = True,
    anomaly_start_step: int = 20,
) -> Path:
    base = Path(__file__).resolve().parents[1] / "experiments" / "results"
    if output_dir is None:
        run_dir = EventLog.prepare_run_dir(base, run_id="mock_eclss_demo")
    else:
        run_dir = Path(output_dir)
        run_dir.mkdir(parents=True, exist_ok=True)

    sim = MockEclssSimulator()
    if inject_scrubber_anomaly:
        sim.inject_anomaly(
            AnomalySpec(
                name="scrubber_degradation",
                start_step=anomaly_start_step,
                scrubber_efficiency_decay_per_step=0.015,
                power_margin_decay_per_step=8.0,
                co2_production_multiplier=1.2,
            )
        )

    log = EventLog(run_dir)
    peak_co2 = 0.0

    for _ in range(steps):
        snap = sim.step()
        peak_co2 = max(peak_co2, snap.co2_ppm)
        health = compute_health_metrics(snap)
        log.append("telemetry", snap.to_dict())
        log.append("health_metrics", health.to_dict())
        for event in sim.get_events():
            if event.get("step") == snap.step:
                log.append("events", {"step": snap.step, **{k: v for k, v in event.items() if k != "step"}})

    log.write_summary(
        {
            "simulator": "mock_eclss",
            "steps": steps,
            "peak_co2_ppm": peak_co2,
            "final_co2_ppm": snap.co2_ppm,
            "final_health": health.to_dict(),
        }
    )
    return run_dir


def main():
    parser = argparse.ArgumentParser(description="Mock ECLSS step runner (Day 2 demo)")
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--no-anomaly", action="store_true")
    args = parser.parse_args()

    run_dir = run_mock_simulation(
        steps=args.steps,
        output_dir=args.output,
        inject_scrubber_anomaly=not args.no_anomaly,
    )
    print(f"Wrote telemetry to {run_dir}")


if __name__ == "__main__":
    main()
