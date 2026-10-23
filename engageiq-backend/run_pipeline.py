"""
EngageIQ Data Pipeline - Command Line Interface (CLI)
Runs the end-to-end data pipeline from the terminal.

Usage:
    python run_pipeline.py
    python run_pipeline.py --csv path/to/dataset.csv
    python run_pipeline.py --csv path/to/dataset.csv --verbose
"""

import argparse
import sys
from pathlib import Path
import pandas as pd

# Set up paths
PIPELINE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PIPELINE_ROOT))

from config import config
from database.db_session import SessionLocal, init_db
from database.repository import PipelineRepository
from preprocessing.validator import DataValidator
from preprocessing.cleaner import DataCleaner
from preprocessing.normalizer import RoleAwareNormalizer
from scoring.pace_engine import PACEEngine
from scoring.pattern_detector import PatternDetector


def print_banner():
    banner = r"""
  ______                      __      ____ 
 |  ____|                    |  |    / __ \
 | |__   _ __   __ _  __ _  __ _  ___| |  | |
 |  __| | '_ \ / _` |/ _` |/ _` |/ _ \ |  | |
 | |____| | | | (_| | (_| | (_| |  __/ |__| |
 |______|_| |_|\__, |\__,_|\__,_|\___|\___\_\
                __/ |   DATA PIPELINE v2.0  
               |___/                        
    """
    print(banner)
    print("=" * 72)
    print(" EHS (40%) + OPI (60%) => PACE Scoring & Relational Store Engine")
    print("=" * 72)


def run_pipeline(csv_file: Path, verbose: bool = False):
    """Executes the data pipeline end-to-end."""
    print_banner()
    print(f"\n[+] Step 1: Loading Dataset from {csv_file}")
    if not csv_file.exists():
        print(f"[-] Error: File {csv_file} does not exist.")
        sys.exit(1)

    try:
        df_raw = pd.read_csv(csv_file)
        print(f"    Loaded {len(df_raw)} records with columns: {list(df_raw.columns[:6])}...")
    except Exception as e:
        print(f"[-] Error reading CSV: {e}")
        sys.exit(1)

    # 1. Validation
    print("\n[+] Step 2: Data Validation & Schema Enforcement")
    validator = DataValidator(strict_bounds=False)
    valid_df, invalid_df, val_result = validator.validate_dataframe(df_raw)
    print(f"    Total records:   {val_result.total_records}")
    print(f"    Valid records:   {val_result.valid_records}")
    print(f"    Invalid records: {val_result.invalid_records}")

    if val_result.warnings:
        for w in val_result.warnings[:3]:
            print(f"    [!] Warning: {w}")

    if len(valid_df) == 0:
        print("[-] Pipeline halted: No valid records to process.")
        sys.exit(1)

    # 2. Cleaning & Imputation
    print("\n[+] Step 3: Cleaning & Median Imputation")
    cleaner = DataCleaner()
    cleaned_df = cleaner.clean_dataframe(valid_df)
    print(f"    Roles mapped: {dict(cleaned_df['role'].value_counts())}")

    # 3. Role-Aware Normalization
    print("\n[+] Step 4: Role-Aware Normalization")
    normalizer = RoleAwareNormalizer()
    normalized_df = normalizer.normalize_dataframe(cleaned_df)
    print(f"    Normalized signal & output dimensions [0.0 - 1.0]")

    # 4. Calculation: EHS & OPI -> 40:60 PACE
    print("\n[+] Step 5: Scoring with 40:60 PACE Formula")
    print("    Formula: PACE = (0.40 * EHS) + (0.60 * OPI)")
    pace_engine = PACEEngine(ehs_weight=config.EHS_WEIGHT, opi_weight=config.OPI_WEIGHT)
    scored_df = pace_engine.process_dataframe(normalized_df)
    
    avg_ehs = scored_df['ehs_score'].mean()
    avg_opi = scored_df['opi_score'].mean()
    avg_pace = scored_df['pace_score'].mean()
    print(f"    Org Average EHS:  {avg_ehs:.2f}")
    print(f"    Org Average OPI:  {avg_opi:.2f}")
    print(f"    Org Average PACE: {avg_pace:.2f}")

    # 5. Pattern Detection
    print("\n[+] Step 6: Organizational Pattern & Anomaly Detection")
    detector = PatternDetector()
    detected_risks = detector.detect_patterns(scored_df)
    print(f"    Detected {len(detected_risks)} risk patterns:")
    for r in detected_risks[:5]:
        print(f"    - [{r.severity.upper()}] {r.employee_name} ({r.employee_id}): {r.pattern_id}")

    # 6. Database Storage
    print("\n[+] Step 7: Storing in Relational Database")
    init_db()
    db = SessionLocal()
    try:
        repo = PipelineRepository(db)
        stored = repo.store_pipeline_batch(scored_df, detected_risks)
        print(f"    Successfully persisted {stored} employee score records and {len(detected_risks)} risk events.")
        print(f"    Database location: {config.DATABASE_URL}")
    finally:
        db.close()

    # 7. Summary Report
    print("\n" + "=" * 72)
    print(f"{'EMP ID':<10} {'NAME':<18} {'ROLE':<12} {'EHS':<6} {'OPI':<6} {'PACE':<6} {'RISK':<10}")
    print("-" * 72)
    for _, row in scored_df.head(15).iterrows():
        print(
            f"{row['employee_id']:<10} "
            f"{str(row['employee_name'])[:16]:<18} "
            f"{row['role']:<12} "
            f"{row['ehs_score']:<6.2f} "
            f"{row['opi_score']:<6.2f} "
            f"{row['pace_score']:<6.2f} "
            f"{row['risk_category']:<10}"
        )
    print("=" * 72)
    print(f"\n[+] Pipeline Run Finished Successfully!")


def main():
    parser = argparse.ArgumentParser(description="EngageIQ PACE Data Pipeline CLI")
    parser.add_argument(
        "--csv",
        type=str,
        default=str(PIPELINE_ROOT / "dataset" / "employees_sample.csv"),
        help="Path to input CSV dataset"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    run_pipeline(Path(args.csv), verbose=args.verbose)


if __name__ == "__main__":
    main()
