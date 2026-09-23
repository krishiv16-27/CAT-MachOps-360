#!/usr/bin/env python3
"""
CAT MachOps 360 — Synthetic Dataset Generator
==============================================

Usage:
    python generate_data.py --profile demo --seed 42
    python generate_data.py --profile dev --seed 42
    python generate_data.py --profile stress --seed 42 --no-parquet

Profiles:
    demo    ~5k telemetry rows, instant generation (~2s)
    dev     ~100k rows, moderate (~30s)
    stress  ~1M+ rows, enterprise scale (~5-10 min)

Output:
    data/seed/<profile>_seed.sql     — INSERT statements for application DB
    data/generated/<profile>_telemetry.parquet
    data/generated/<profile>_wearable_events.parquet

All data is synthetic and reproducible with the same seed.
Not derived from real Caterpillar data.
"""
import argparse
import sys
import time
import random
from pathlib import Path

# Allow running from anywhere
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.generators.profiles import PROFILES
from data.generators.faker_setup import uid
from data.generators.entity_generators import (
    generate_sites, generate_zones, generate_machine_models, generate_machines,
    generate_operators, generate_machine_maintenance, generate_machine_faults,
    generate_training_modules, generate_operator_training,
)
from data.generators.user_generator import generate_users, generate_operator_certifications
from data.generators.task_generator import (
    generate_tasks, generate_alerts_from_telemetry, generate_incidents,
    generate_proximity_events, generate_dashcam_events,
)
from data.generators.telemetry_generator import (
    generate_telemetry, generate_wearable_events, generate_environmental_data,
)
from data.generators.writers import write_dataset


def build_dataset(profile_name: str, seed: int, no_parquet: bool = False) -> dict:
    profile = PROFILES[profile_name]
    rng = random.Random(seed)

    print(f"\n{'='*60}")
    print(f"CAT MachOps 360 — Dataset Generator")
    print(f"Profile : {profile_name.upper()} — {profile.description}")
    print(f"Seed    : {seed}")
    print(f"{'='*60}\n")

    t0 = time.time()

    # ── Static entities ──────────────────────────────────────────
    print("Generating sites + zones...")
    sites = generate_sites(profile, rng)
    zones = generate_zones(profile, sites, rng)

    print("Generating machine models + machines...")
    machine_models = generate_machine_models(profile)
    machines = generate_machines(profile, machine_models, sites, zones, rng)

    print("Generating operators + users...")
    operators = generate_operators(profile, sites, machines, rng)
    users = generate_users(operators, profile.num_users_extra)
    operator_certifications = generate_operator_certifications(operators)

    print("Generating maintenance + faults...")
    machine_maintenance = generate_machine_maintenance(machines, rng)
    machine_faults = generate_machine_faults(machines, rng, fault_probability=0.15)

    print("Generating training modules + operator training...")
    training_modules = generate_training_modules()
    operator_training = generate_operator_training(operators, training_modules, rng)

    print("Generating tasks...")
    tasks = generate_tasks(profile, operators, machines, zones, rng)

    # ── Time-series data ─────────────────────────────────────────
    print(f"Generating telemetry ({profile.telemetry_rows_per_machine} rows × {len(machines)} machines)...")
    all_telemetry = []
    active_machines = [m for m in machines if m["status"] == "ACTIVE"]
    for machine in active_machines:
        op = next((o for o in operators if o.get("current_machine_id") == machine["machine_id"]), None)
        active_tasks = [t for t in tasks if t["machine_id"] == machine["machine_id"] and t["status"] == "IN_PROGRESS"]
        task = active_tasks[0] if active_tasks else None
        rows = generate_telemetry(machine, op, task, profile.telemetry_rows_per_machine, rng)
        all_telemetry.extend(rows)

    print(f"  Total telemetry rows: {len(all_telemetry):,}")

    print(f"Generating wearable events ({profile.wearable_rows_per_operator} rows × {len(operators)} operators)...")
    all_wearable = []
    on_shift = [o for o in operators if o["shift_status"] == "ON_SHIFT"]
    for op in on_shift:
        rows = generate_wearable_events(op, profile.wearable_rows_per_operator, rng)
        all_wearable.extend(rows)

    print(f"  Total wearable rows: {len(all_wearable):,}")

    print("Generating environmental data...")
    env_hours = max(24, profile.telemetry_rows_per_machine // 60)
    environmental_data = generate_environmental_data(sites, env_hours, rng)

    # ── Safety events ─────────────────────────────────────────────
    print("Generating alerts + incidents + proximity + dashcam events...")
    alerts = generate_alerts_from_telemetry(all_telemetry, {m["machine_id"]: m for m in machines}, rng, alert_rate=0.008)
    incidents = generate_incidents(alerts, rng)
    proximity_events = generate_proximity_events(all_telemetry, rng, rate=0.004)
    dashcam_events = generate_dashcam_events(machines, profile.num_dashcam_events, rng)

    # Empty prestart_checks — these are generated interactively
    prestart_checks = []

    elapsed = time.time() - t0
    print(f"\nGeneration complete in {elapsed:.1f}s")

    all_data = {
        "sites": sites,
        "zones": zones,
        "machine_models": machine_models,
        "machines": machines,
        "machine_faults": machine_faults,
        "machine_maintenance": machine_maintenance,
        "operators": operators,
        "users": users,
        "operator_certifications": operator_certifications,
        "training_modules": training_modules,
        "operator_training": operator_training,
        "tasks": tasks,
        "telemetry": all_telemetry,
        "wearable_events": all_wearable,
        "environmental_data": environmental_data,
        "alerts": alerts,
        "incidents": incidents,
        "proximity_events": proximity_events,
        "dashcam_events": dashcam_events,
        "prestart_checks": prestart_checks,
    }

    print("\nRow counts:")
    for table, rows in all_data.items():
        if rows:
            print(f"  {table:30s}: {len(rows):>8,}")

    return all_data


def main():
    parser = argparse.ArgumentParser(
        description="CAT MachOps 360 — Synthetic Dataset Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--profile", "-p",
        choices=list(PROFILES.keys()),
        default="demo",
        help="Dataset size profile (default: demo)",
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--out-dir", "-o",
        type=str,
        default=None,
        help="Output directory (default: data/seed/ for SQL, data/generated/ for Parquet)",
    )
    parser.add_argument(
        "--no-parquet",
        action="store_true",
        help="Write CSV instead of Parquet (if pyarrow not available)",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available profiles and exit",
    )

    args = parser.parse_args()

    if args.list_profiles:
        print("\nAvailable profiles:")
        for name, p in PROFILES.items():
            telemetry_est = p.num_machines * p.telemetry_rows_per_machine
            print(f"  {name:8s} — {p.description}")
            print(f"           {p.num_operators} operators, {p.num_machines} machines, ~{telemetry_est:,} telemetry rows")
        return

    # Determine output directory
    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        # Default: place SQL in data/seed/, large files in data/generated/
        script_dir = Path(__file__).parent.parent  # data/
        out_dir = script_dir / "seed"

    all_data = build_dataset(args.profile, args.seed, args.no_parquet)
    write_dataset(args.profile, all_data, out_dir, write_parquet_flag=not args.no_parquet)

    print(f"\nDone. Load seed into DB:")
    print(f"  sqlite3 backend/machops360_demo.db < {out_dir}/{args.profile}_seed.sql")
    print(f"\nOr use the backend's auto-seeder:")
    print(f"  cd backend && uvicorn app.main:app --reload  # seeds on startup")


if __name__ == "__main__":
    main()
