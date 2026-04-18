"""
Execute ML pipeline for election prediction analysis
Run from project root directory
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ml_analysis import run_full_ml_pipeline

if __name__ == '__main__':
    csv_path = project_root / 'raw data' / 'election_analysis_dataset.csv'
    
    print(f"CSV Path: {csv_path}")
    print(f"File exists: {csv_path.exists()}")
    
    predictor, summary, features, descriptions = run_full_ml_pipeline(str(csv_path))
    
    print("\n" + "="*60)
    print("ML PIPELINE EXECUTION COMPLETE")
    print("="*60)
    print(f"\nModels trained: {list(predictor.models.keys())}")
    print(f"Features engineered: {len(features)}")
    print(f"Artifacts saved to: models/")
