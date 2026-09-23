"""
Output writers: SQL INSERT statements and Parquet files.
"""
import os
import json
from pathlib import Path
from datetime import datetime


def _sql_val(v) -> str:
    """Convert a Python value to a SQL literal."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, dict):
        return "'" + json.dumps(v).replace("'", "''") + "'"
    if isinstance(v, list):
        return "'" + json.dumps(v).replace("'", "''") + "'"
    return "'" + str(v).replace("'", "''") + "'"


def write_sql(records: list[dict], table_name: str, out_file, batch_size: int = 500):
    """Write INSERT statements for a list of records to file."""
    if not records:
        return
    cols = list(records[0].keys())
    col_str = ", ".join(cols)

    for i in range(0, len(records), batch_size):
        batch = records[i: i + batch_size]
        values_parts = []
        for row in batch:
            vals = ", ".join(_sql_val(row[c]) for c in cols)
            values_parts.append(f"  ({vals})")
        stmt = f"INSERT INTO {table_name} ({col_str}) VALUES\n"
        stmt += ",\n".join(values_parts) + ";\n\n"
        out_file.write(stmt)


def write_parquet(records: list[dict], out_path: Path):
    """Write records to a Parquet file using pyarrow."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        # Fall back to CSV if pyarrow not available
        write_csv(records, out_path.with_suffix(".csv"))
        return

    if not records:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(records)
    pq.write_table(table, str(out_path))
    print(f"    → Parquet: {out_path} ({len(records):,} rows)")


def write_csv(records: list[dict], out_path: Path):
    """CSV fallback."""
    import csv
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        if records:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
    print(f"    → CSV: {out_path} ({len(records):,} rows)")


def write_dataset(
    profile_name: str,
    all_data: dict[str, list[dict]],
    out_dir: Path,
    write_parquet_flag: bool = True,
):
    """
    Write the full dataset:
    - SQL seed file: all application entities as INSERT statements
    - Parquet files: large telemetry tables
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    sql_path = out_dir / f"{profile_name}_seed.sql"
    generated_dir = out_dir / "generated"
    generated_dir.mkdir(exist_ok=True)

    # Tables that go in SQL seed (application entities, small enough to INSERT)
    sql_tables = [
        "sites", "zones", "machine_models", "machines",
        "machine_faults", "machine_maintenance",
        "operators", "users",
        "operator_certifications",
        "training_modules", "operator_training",
        "tasks",
        "alerts", "incidents", "proximity_events",
        "dashcam_events",
        "prestart_checks",
        "environmental_data",
    ]

    # Tables that go to Parquet (large time-series)
    parquet_tables = ["telemetry", "wearable_events"]

    print(f"\nWriting SQL seed: {sql_path}")
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write(f"-- CAT MachOps 360 — {profile_name.upper()} profile seed\n")
        f.write(f"-- Generated: {datetime.utcnow().isoformat()}Z\n")
        f.write(f"-- Synthetic data only — not real CAT data\n\n")
        f.write("BEGIN;\n\n")

        for table in sql_tables:
            records = all_data.get(table, [])
            if records:
                print(f"  {table}: {len(records):,} rows")
                write_sql(records, table, f)

        f.write("COMMIT;\n")

    print(f"\nSQL seed written: {sql_path.stat().st_size / 1024:.1f} KB")

    for table in parquet_tables:
        records = all_data.get(table, [])
        if not records:
            continue
        print(f"  {table}: {len(records):,} rows")
        if write_parquet_flag:
            write_parquet(records, generated_dir / f"{profile_name}_{table}.parquet")
        else:
            write_csv(records, generated_dir / f"{profile_name}_{table}.csv")

    print(f"\nDataset generation complete for profile '{profile_name}'.")
    print(f"SQL seed: {sql_path}")
    print(f"Parquet/CSV: {generated_dir}/")
