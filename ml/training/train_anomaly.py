#!/usr/bin/env python3
"""
Operator Anomaly Detection Model — Training Script
===================================================
Trains an IsolationForest on operator telemetry features.
Anomalous patterns are defined as statistically unusual operating behaviour.

This is a behavioural anomaly detector — NOT a safety diagnosis tool.
Output labels: NORMAL / UNUSUAL

Usage:
    python ml/training/train_anomaly.py
    python ml/training/train_anomaly.py --data data/generated/demo_telemetry.parquet
    python ml/training/train_anomaly.py --synthetic --samples 10000
"""
import argparse
import sys
import random
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))


FEATURE_COLS = [
    "avg_speed_kmh",
    "max_speed_kmh",
    "sudden_acceleration_count",
    "sudden_braking_count",
    "avg_idle_time_min",
    "avg_fuel_consumption_rate_lph",
    "avg_engine_rpm",
    "avg_machine_load_pct",
    "avg_cycle_time_min",
]


def build_operator_windows(df: pd.DataFrame, window_size: int = 30) -> pd.DataFrame:
    """
    Aggregate telemetry into operator-level windows (last N rows per operator).
    Each row in output represents an operator's recent behaviour window.
    """
    if "operator_id" not in df.columns:
        df["operator_id"] = "UNKNOWN"

    records = []
    for op_id, group in df.groupby("operator_id"):
        g = group.tail(window_size)
        records.append({
            "operator_id": op_id,
            "avg_speed_kmh":               g.get("machine_speed_kmh", pd.Series([0])).mean(),
            "max_speed_kmh":               g.get("machine_speed_kmh", pd.Series([0])).max(),
            "sudden_acceleration_count":   g.get("sudden_acceleration", pd.Series([False])).sum(),
            "sudden_braking_count":        g.get("sudden_braking",      pd.Series([False])).sum(),
            "avg_idle_time_min":           g.get("idle_time_min",        pd.Series([0])).mean(),
            "avg_fuel_consumption_rate_lph": g.get("fuel_consumption_rate_lph", pd.Series([12])).mean(),
            "avg_engine_rpm":              g.get("engine_rpm",           pd.Series([1400])).mean(),
            "avg_machine_load_pct":        g.get("machine_load_pct",     pd.Series([50])).mean(),
            "avg_cycle_time_min":          g.get("cycle_time_min",        pd.Series([6])).mean(),
        })
    return pd.DataFrame(records)


def generate_synthetic_windows(n_samples: int = 10000, seed: int = 42, contamination: float = 0.05) -> pd.DataFrame:
    """
    Generate synthetic operator window data.
    ~contamination% are injected anomalies.
    """
    rng = random.Random(seed)
    np.random.seed(seed)

    rows = []
    n_anomalies = int(n_samples * contamination)

    # Normal operating windows
    for _ in range(n_samples - n_anomalies):
        rows.append({
            "operator_id": f"OP{rng.randint(1000, 9999)}",
            "avg_speed_kmh":                 rng.uniform(1, 6),
            "max_speed_kmh":                 rng.uniform(5, 12),
            "sudden_acceleration_count":     rng.choices([0, 1, 2], weights=[0.80, 0.15, 0.05])[0],
            "sudden_braking_count":          rng.choices([0, 1], weights=[0.90, 0.10])[0],
            "avg_idle_time_min":             rng.uniform(0, 8),
            "avg_fuel_consumption_rate_lph": rng.uniform(9, 16),
            "avg_engine_rpm":                rng.uniform(1100, 1800),
            "avg_machine_load_pct":          rng.uniform(35, 75),
            "avg_cycle_time_min":            rng.uniform(4, 9),
        })

    # Anomalous windows — inject unusual patterns
    anomaly_patterns = [
        # Extended idling
        lambda r: {"avg_idle_time_min": r.uniform(30, 55), "avg_machine_load_pct": r.uniform(0, 5)},
        # Excessive speed
        lambda r: {"avg_speed_kmh": r.uniform(15, 28), "max_speed_kmh": r.uniform(25, 40)},
        # Repeated sudden acceleration
        lambda r: {"sudden_acceleration_count": r.randint(8, 20)},
        # Very high fuel consumption (possible mechanical issue)
        lambda r: {"avg_fuel_consumption_rate_lph": r.uniform(22, 35), "avg_idle_time_min": r.uniform(20, 40)},
        # Extremely short cycle times (possible data anomaly or reckless operation)
        lambda r: {"avg_cycle_time_min": r.uniform(0.5, 2.0)},
    ]

    for i in range(n_anomalies):
        base = {
            "operator_id": f"OP{rng.randint(1000, 9999)}",
            "avg_speed_kmh":                 rng.uniform(1, 6),
            "max_speed_kmh":                 rng.uniform(5, 12),
            "sudden_acceleration_count":     0,
            "sudden_braking_count":          0,
            "avg_idle_time_min":             rng.uniform(0, 8),
            "avg_fuel_consumption_rate_lph": rng.uniform(9, 16),
            "avg_engine_rpm":                rng.uniform(1100, 1800),
            "avg_machine_load_pct":          rng.uniform(35, 75),
            "avg_cycle_time_min":            rng.uniform(4, 9),
        }
        pattern = rng.choice(anomaly_patterns)
        base.update(pattern(rng))
        rows.append(base)

    return pd.DataFrame(rows)


def train(data_path: str | None = None, synthetic_samples: int = 10000, seed: int = 42):
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    import joblib

    print("=" * 60)
    print("CAT MachOps 360 — Anomaly Detection Model Training")
    print("=" * 60)
    print("NOTE: This detects unusual operating patterns.")
    print("It is NOT a diagnostic or safety certification tool.")
    print("=" * 60)

    # Load or generate data
    if data_path and Path(data_path).exists():
        print(f"\nLoading telemetry from: {data_path}")
        ext = Path(data_path).suffix
        raw = pd.read_parquet(data_path) if ext == ".parquet" else pd.read_csv(data_path)
        print(f"Building operator windows from {len(raw):,} telemetry rows...")
        df = build_operator_windows(raw)
        print(f"Built {len(df):,} operator windows")
    else:
        print(f"\nGenerating {synthetic_samples:,} synthetic operator windows (seed={seed})...")
        df = generate_synthetic_windows(synthetic_samples, seed)
        print(f"Generated {len(df):,} windows (includes ~5% injected anomalies)")

    X = df[FEATURE_COLS].fillna(0).values

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train IsolationForest
    contamination = 0.05  # expect ~5% anomalies
    print(f"\nTraining IsolationForest (contamination={contamination}, n_estimators=100)...")
    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    # Evaluate on training data
    scores = model.decision_function(X_scaled)
    labels = model.predict(X_scaled)  # 1=normal, -1=anomaly
    n_anomalies = (labels == -1).sum()
    print(f"\nTraining result:")
    print(f"  Total windows: {len(labels):,}")
    print(f"  Flagged as UNUSUAL: {n_anomalies:,} ({100 * n_anomalies / len(labels):.1f}%)")
    print(f"  Score range: [{scores.min():.3f}, {scores.max():.3f}]")
    print(f"  Threshold (0 = boundary): scores < 0 → UNUSUAL")

    # Save
    models_dir = ROOT / "ml" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / "anomaly_model.joblib"

    metadata = {
        "feature_cols": FEATURE_COLS,
        "contamination": contamination,
        "n_train": len(X),
        "n_anomalies_detected": int(n_anomalies),
        "seed": seed,
        "note": "Detects unusual operating patterns — NOT a diagnostic or safety certification tool",
        "disclaimer": "Operational risk indicator — not a medical diagnosis",
    }

    joblib.dump({"model": model, "scaler": scaler, "metadata": metadata}, model_path)
    print(f"\nModel saved: {model_path}")
    print(f"Size: {model_path.stat().st_size / 1024:.0f} KB")
    print("\nRestart the backend to load the trained model.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train anomaly detection model")
    parser.add_argument("--data", type=str, default=None, help="Path to telemetry Parquet/CSV")
    parser.add_argument("--synthetic", action="store_true", help="Force synthetic data")
    parser.add_argument("--samples", type=int, default=10000, help="Synthetic window count")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    data_path = None if args.synthetic else args.data
    train(data_path=data_path, synthetic_samples=args.samples, seed=args.seed)
