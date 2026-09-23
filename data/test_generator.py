"""Quick smoke test for the dataset generator."""
import sys, random
sys.path.insert(0, '.')
from data.generators.profiles import PROFILES
from data.generators.entity_generators import (
    generate_sites, generate_zones, generate_machine_models,
    generate_machines, generate_operators, generate_training_modules,
    generate_operator_training,
)
from data.generators.user_generator import generate_users, generate_operator_certifications
from data.generators.task_generator import generate_tasks, generate_dashcam_events
from data.generators.telemetry_generator import generate_telemetry, generate_wearable_events

profile = PROFILES['demo']
rng = random.Random(42)

sites = generate_sites(profile, rng)
zones = generate_zones(profile, sites, rng)
models = generate_machine_models(profile)
machines = generate_machines(profile, models, sites, zones, rng)
operators = generate_operators(profile, sites, machines, rng)
users = generate_users(operators, 5)
certs = generate_operator_certifications(operators)
modules = generate_training_modules()
training = generate_operator_training(operators, modules, rng)
tasks = generate_tasks(profile, operators, machines, zones, rng)
dashcam = generate_dashcam_events(machines, 10, rng)

telemetry = []
for m in machines[:3]:
    op = next((o for o in operators if o.get('current_machine_id') == m['machine_id']), None)
    telemetry.extend(generate_telemetry(m, op, None, 20, rng))

wearable = []
for op in operators[:3]:
    wearable.extend(generate_wearable_events(op, 20, rng))

print(f"Sites:      {len(sites)}")
print(f"Zones:      {len(zones)}")
print(f"Models:     {len(models)}")
print(f"Machines:   {len(machines)}")
print(f"Operators:  {len(operators)}")
print(f"Users:      {len(users)}")
print(f"Tasks:      {len(tasks)}")
print(f"Telemetry:  {len(telemetry)} rows")
print(f"Wearable:   {len(wearable)} rows")
print(f"Dashcam:    {len(dashcam)} events")
print(f"Training:   {len(training)} records")
print()
print(f"Sample telemetry row:")
print(f"  RPM={telemetry[0]['engine_rpm']}, Temp={telemetry[0]['engine_temperature_c']}C, Fuel={telemetry[0]['fuel_level_pct']}%")
print()
print("GENERATOR SMOKE TEST PASSED")
