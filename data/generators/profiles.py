"""
Dataset generation profiles.
Each profile defines scale parameters and is passed to all generators.
"""
from dataclasses import dataclass


@dataclass
class Profile:
    name: str
    num_sites: int
    num_zones_per_site: int
    num_machine_models: int
    num_machines: int
    num_operators: int
    num_users_extra: int          # non-operator staff users
    num_tasks_per_operator: int
    telemetry_rows_per_machine: int  # rows = minutes of operation
    wearable_rows_per_operator: int
    num_dashcam_events: int
    num_scenarios: int            # how many anomaly scenarios to inject
    description: str


PROFILES: dict[str, Profile] = {
    "demo": Profile(
        name="demo",
        num_sites=2,
        num_zones_per_site=3,
        num_machine_models=3,
        num_machines=10,
        num_operators=10,
        num_users_extra=5,
        num_tasks_per_operator=4,
        telemetry_rows_per_machine=120,       # ~2 hours @ 1 row/min
        wearable_rows_per_operator=60,
        num_dashcam_events=20,
        num_scenarios=3,
        description="Demo profile — instant generation, suitable for hackathon demo",
    ),
    "dev": Profile(
        name="dev",
        num_sites=5,
        num_zones_per_site=5,
        num_machine_models=6,
        num_machines=50,
        num_operators=100,
        num_users_extra=15,
        num_tasks_per_operator=10,
        telemetry_rows_per_machine=2880,      # ~48 hours @ 1 row/min
        wearable_rows_per_operator=480,
        num_dashcam_events=500,
        num_scenarios=20,
        description="Dev profile — moderate scale, ~100k telemetry rows",
    ),
    "stress": Profile(
        name="stress",
        num_sites=20,
        num_zones_per_site=10,
        num_machine_models=10,
        num_machines=200,
        num_operators=500,
        num_users_extra=50,
        num_tasks_per_operator=20,
        telemetry_rows_per_machine=10080,     # ~7 days @ 1 row/min
        wearable_rows_per_operator=1440,
        num_dashcam_events=5000,
        num_scenarios=100,
        description="Stress profile — enterprise scale, 1M+ telemetry rows",
    ),
}
