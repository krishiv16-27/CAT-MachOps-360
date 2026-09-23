#!/usr/bin/env python3
"""
Task ETA Prediction Model — Training Script
============================================
Trains a RandomForestRegressor to predict task_duration_minutes.
Works with either the generated Parquet dataset or synthetic training data.

Usage:
    python ml/training/train_eta.py
    python ml/training/train_eta.py --data data/generated/demo_tasks.parquet
    python ml/training/train_eta.py --synthetic --samples 5000
"""
import argparse
import sys
import os
import random
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))


def generate_synthetic_training_data(n_samples: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic training data when no dataset is available."""
    rng = random.Random(seed)
    np.random.seed(seed)

    TASK_TYPES = ["EXCAVATION", "LOADING", "TRENCHING", "GRADING", "HAULING", "COMPACTION", "BACKFILL"]
    MACHINE_TYPES = ["EXCAVATOR", "BULLDOZER", "GRADER", "LOADER", "DUMP_TRUCK", "COMPACTOR"]
    WEATHER = ["CLEAR", "CLOUDY", "RAIN", "HEAVY_RAIN", "FOG"]
    TERRAIN = ["FLAT", "SLOPE", "ROUGH", "ROCKY", "WET", "COMPACTED"]
    MATERIALS = ["CLAY", "SAND", "ROCK", "TOPSOIL", "GRAVEL"]

    # Base durations
    BASE_DUR = {"EXCAVATION": 75, "LOADING": 45, "TRENCHING": 90,
                "GRADING": 60, "HAULING": 40, "COMPACTION": 50, "BACKFILL": 55}
    WEATHER_F = {"CLEAR": 1.0, "CLOUDY": 1.0, "RAIN": 1.25, "HEAVY_RAIN": 1.50, "FOG": 1.20}
    TERRAIN_F = {"FLAT": 1.0, "SLOPE": 1.20, "ROUGH": 1.30, "ROCKY": 1.40, "WET": 1.35, "COMPACTED": 0.90}
    SKILL_F   = {1: 1.35, 2: 1.15, 3: 1.00, 4: 0.88, 5: 0.78}

    rows = []
    for _ in range(n_samples):
        task_type = rng.choice(TASK_TYPES)
        machine_type = rng.choice(MACHINE_TYPES)
        machine_age = rng.uniform(0.5, 10)
        skill = rng.randint(1, 5)
        exp = rng.uniform(0.5, 20)
        quantity = rng.uniform(50, 1000)
        weather = rng.choice(WEATHER)
        temp = rng.uniform(5, 42)
        rainfall = rng.uniform(0, 20) if weather in ("RAIN", "HEAVY_RAIN") else 0
        wind = rng.uniform(0, 50)
        terrain = rng.choice(TERRAIN)
        load = rng.uniform(20, 95)
        material = rng.choice(MATERIALS)

        # Correlated target
        base = BASE_DUR[task_type]
        duration = (
            base
            * WEATHER_F.get(weather, 1.0)
            * TERRAIN_F.get(terrain, 1.0)
            * SKILL_F.get(skill, 1.0)
            * (1 + machine_age * 0.01)       # older machines slightly slower
            * (1 + load * 0.002)             # higher load slightly slower
            * rng.uniform(0.80, 1.20)        # natural variance
        )
        historical_avg = base * SKILL_F.get(skill, 1.0) * rng.uniform(0.90, 1.10)

        rows.append({
            "task_type": task_type,
            "machine_type": machine_type,
            "machine_age_years": machine_age,
            "operator_skill_level": skill,
            "operator_experience_years": exp,
            "target_quantity": quantity,
            "weather_condition": weather,
            "temperature_celsius": temp,
            "rainfall_mm": rainfall,
            "wind_speed_kmh": wind,
            "terrain_type": terrain,
            "machine_load_percent": load,
            "material_type": material,
            "historical_avg_duration_minutes": historical_avg,
            "actual_duration_minutes": duration,
        })

    return pd.DataFrame(rows)


def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    """Encode categorical features as integers."""
    encodings = {
        "task_type":        ["EXCAVATION", "LOADING", "TRENCHING", "GRADING", "HAULING", "COMPACTION", "BACKFILL"],
        "machine_type":     ["EXCAVATOR", "BULLDOZER", "GRADER", "LOADER", "DUMP_TRUCK", "COMPACTOR"],
        "weather_condition": ["CLEAR", "CLOUDY", "RAIN", "HEAVY_RAIN", "FOG", "DUST"],
        "terrain_type":     ["FLAT", "SLOPE", "ROUGH", "ROCKY", "WET", "COMPACTED"],
        "material_type":    ["CLAY", "SAND", "ROCK", "TOPSOIL", "GRAVEL", "LIMESTONE", "COAL"],
    }
    df = df.copy()
    for col, categories in encodings.items():
        if col in df.columns:
            cat_map = {c: i for i, c in enumerate(categories)}
            df[col] = df[col].map(cat_map).fillna(0).astype(int)
    return df


FEATURE_COLS = [
    "task_type", "machine_type", "machine_age_years",
    "operator_skill_level", "operator_experience_years",
    "target_quantity", "weather_condition", "temperature_celsius",
    "rainfall_mm", "wind_speed_kmh", "terrain_type",
    "machine_load_percent", "material_type",
    "historical_avg_duration_minutes",
]
TARGET_COL = "actual_duration_minutes"


def train(data_path: str | None = None, synthetic_samples: int = 5000, seed: int = 42):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    import joblib

    print("=" * 60)
    print("CAT MachOps 360 — ETA Model Training")
    print("=" * 60)

    # Load or generate data
    if data_path and Path(data_path).exists():
        print(f"\nLoading data from: {data_path}")
        ext = Path(data_path).suffix
        df = pd.read_parquet(data_path) if ext == ".parquet" else pd.read_csv(data_path)
        print(f"Loaded {len(df):,} records")
    else:
        print(f"\nGenerating {synthetic_samples:,} synthetic training samples (seed={seed})...")
        df = generate_synthetic_training_data(synthetic_samples, seed)
        print(f"Generated {len(df):,} synthetic records")

    # Check we have the required columns
    missing = [c for c in FEATURE_COLS + [TARGET_COL] if c not in df.columns]
    if missing:
        print(f"\nMissing columns: {missing}")
        print("Generating synthetic data instead...")
        df = generate_synthetic_training_data(synthetic_samples, seed)

    # Drop rows with missing target
    df = df.dropna(subset=[TARGET_COL])
    df = df[df[TARGET_COL] > 0]

    # Fill missing historical avg with task-type mean
    if "historical_avg_duration_minutes" not in df.columns:
        df["historical_avg_duration_minutes"] = df[TARGET_COL].mean()
    df["historical_avg_duration_minutes"] = df["historical_avg_duration_minutes"].fillna(df[TARGET_COL].mean())

    # Encode
    df_enc = encode_features(df)
    X = df_enc[FEATURE_COLS].values
    y = df_enc[TARGET_COL].values

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed)
    print(f"\nTrain: {len(X_train):,} | Test: {len(X_test):,}")

    # Train
    print("\nTraining RandomForestRegressor (n_estimators=100)...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_leaf=3,
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print(f"\nTest metrics:")
    print(f"  MAE  : {mae:.1f} minutes")
    print(f"  RMSE : {rmse:.1f} minutes")
    print(f"  R²   : {r2:.3f}")

    # Feature importance
    print("\nTop 5 feature importances:")
    importances = sorted(zip(FEATURE_COLS, model.feature_importances_), key=lambda x: -x[1])
    for feat, imp in importances[:5]:
        print(f"  {feat:40s}: {imp:.3f}")

    # Save model + metadata
    models_dir = ROOT / "ml" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / "eta_model.joblib"

    metadata = {
        "feature_cols": FEATURE_COLS,
        "target_col": TARGET_COL,
        "n_train": len(X_train),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 3),
        "seed": seed,
        "note": "Trained on synthetic data — not validated on real CAT telemetry",
    }

    joblib.dump({"model": model, "metadata": metadata}, model_path)
    print(f"\nModel saved: {model_path}")
    print(f"Size: {model_path.stat().st_size / 1024:.0f} KB")
    print("\nRestart the backend to load the trained model.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train ETA prediction model")
    parser.add_argument("--data", type=str, default=None, help="Path to tasks Parquet/CSV file")
    parser.add_argument("--synthetic", action="store_true", help="Force synthetic data generation")
    parser.add_argument("--samples", type=int, default=5000, help="Synthetic sample count")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    data_path = None if args.synthetic else args.data
    train(data_path=data_path, synthetic_samples=args.samples, seed=args.seed)
