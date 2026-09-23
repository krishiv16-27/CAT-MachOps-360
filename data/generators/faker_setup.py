"""Shared Faker instance and common utilities for all generators."""
import uuid
import random
from faker import Faker

fake = Faker("en_AU")  # Australian locale — relevant for CAT mining/construction


def uid() -> str:
    return str(uuid.uuid4())


def rng_from_seed(seed: int) -> random.Random:
    return random.Random(seed)


# Task types with realistic distributions
TASK_TYPES = [
    ("EXCAVATION", 0.30),
    ("LOADING", 0.20),
    ("TRENCHING", 0.15),
    ("GRADING", 0.12),
    ("HAULING", 0.13),
    ("COMPACTION", 0.05),
    ("BACKFILL", 0.05),
]

MATERIAL_TYPES = ["CLAY", "SAND", "ROCK", "TOPSOIL", "GRAVEL", "LIMESTONE", "COAL"]
WEATHER_CONDITIONS = ["CLEAR", "CLOUDY", "RAIN", "HEAVY_RAIN", "FOG", "DUST"]
TERRAIN_TYPES = ["FLAT", "SLOPE", "ROUGH", "ROCKY", "WET", "COMPACTED"]
ZONE_TYPES = ["EXCAVATION", "LOADING_BAY", "HAUL_ROAD", "DUMP_ZONE", "WORKSHOP", "SAFE_AREA"]

# Machine catalogue
MACHINE_CATALOGUE = [
    {"model_name": "CAT 390F",    "machine_type": "EXCAVATOR",  "fuel_tank_l": 1085, "service_interval_h": 500, "max_load_t": 45, "nominal_hydraulic_bar": 250},
    {"model_name": "CAT 374F",    "machine_type": "EXCAVATOR",  "fuel_tank_l": 840,  "service_interval_h": 500, "max_load_t": 35, "nominal_hydraulic_bar": 245},
    {"model_name": "CAT D9T",     "machine_type": "BULLDOZER",  "fuel_tank_l": 684,  "service_interval_h": 500, "max_load_t": 20, "nominal_hydraulic_bar": 220},
    {"model_name": "CAT D11T",    "machine_type": "BULLDOZER",  "fuel_tank_l": 1060, "service_interval_h": 500, "max_load_t": 30, "nominal_hydraulic_bar": 235},
    {"model_name": "CAT 992K",    "machine_type": "LOADER",     "fuel_tank_l": 750,  "service_interval_h": 500, "max_load_t": 35, "nominal_hydraulic_bar": 235},
    {"model_name": "CAT 140M3",   "machine_type": "GRADER",     "fuel_tank_l": 430,  "service_interval_h": 500, "max_load_t": 15, "nominal_hydraulic_bar": 210},
    {"model_name": "CAT 775G",    "machine_type": "DUMP_TRUCK", "fuel_tank_l": 1250, "service_interval_h": 500, "max_load_t": 90, "nominal_hydraulic_bar": 200},
    {"model_name": "CAT CS64B",   "machine_type": "COMPACTOR",  "fuel_tank_l": 280,  "service_interval_h": 500, "max_load_t": 10, "nominal_hydraulic_bar": 190},
    {"model_name": "CAT 336 GC",  "machine_type": "EXCAVATOR",  "fuel_tank_l": 680,  "service_interval_h": 500, "max_load_t": 28, "nominal_hydraulic_bar": 240},
    {"model_name": "CAT 972M",    "machine_type": "LOADER",     "fuel_tank_l": 510,  "service_interval_h": 500, "max_load_t": 22, "nominal_hydraulic_bar": 225},
]

CERTIFICATION_TYPES = {
    "EXCAVATOR":  ["CAT-EXC-L1", "CAT-EXC-L2", "CAT-EXC-L3", "CAT-EXC-L4"],
    "BULLDOZER":  ["CAT-BUL-L1", "CAT-BUL-L2", "CAT-BUL-L3"],
    "LOADER":     ["CAT-LDR-L1", "CAT-LDR-L2", "CAT-LDR-L3"],
    "GRADER":     ["CAT-GRD-L1", "CAT-GRD-L2"],
    "DUMP_TRUCK": ["CAT-TRK-L1", "CAT-TRK-L2"],
    "COMPACTOR":  ["CAT-CMP-L1", "CAT-CMP-L2"],
}

FAULT_CODES = [
    ("E-ENG-001", "Engine oil pressure low",              "CRITICAL"),
    ("E-ENG-002", "Engine coolant temperature high",      "HIGH"),
    ("E-ENG-003", "Engine RPM out of range",              "MEDIUM"),
    ("E-HYD-041", "Hydraulic oil temperature high",       "MEDIUM"),
    ("E-HYD-042", "Hydraulic filter service overdue",     "MEDIUM"),
    ("E-HYD-043", "Hydraulic pump pressure low",          "HIGH"),
    ("E-ELC-021", "Battery voltage low",                  "LOW"),
    ("E-ELC-022", "Alternator fault",                     "HIGH"),
    ("E-TRN-011", "Transmission oil temperature high",    "MEDIUM"),
    ("E-BRK-031", "Brake pressure warning",               "HIGH"),
    ("E-FUL-051", "Fuel level critical",                  "HIGH"),
    ("E-AIR-061", "Air filter restriction",               "LOW"),
]
