"""
📊 Stage 1: Data Preprocessing v6.0
"""
import pandas as pd
from preprocessor_functions import *
from utils import *
from config import *

def main():
    """Main preprocessing pipeline"""
    print("="*80)
    print("STAGE 1: DATA PREPROCESSING v6.0")
    print("  ✅ Mentee: main_interest + additional_interest (both with levels)")
    print("  ✅ Aspirations: separate matching with mentor work/experience")
    print("="*80)
    
    ensure_output_dir()
    
    print("\n[1/4] Loading CSV files...")
    mentors_raw = load_and_validate_csv(MENTOR_FILE, 'mentor')
    mentees_raw = load_and_validate_csv(MENTEE_FILE, 'mentee')
    
    print("\n[2/4] Processing mentor data...")
    mentors_df = preprocess_mentor_dataframe(mentors_raw)
    
    print("\n[3/4] Processing mentee data...")
    mentees_df = preprocess_mentee_dataframe(mentees_raw)
    
    print("\n[4/4] Saving processed data...")
    save_dataframe(mentors_df, 'mentors_processed.pkl')
    save_dataframe(mentees_df, 'mentees_processed.pkl')
    
    summary = generate_preprocessing_summary(mentors_df, mentees_df)
    save_dataframe(pd.DataFrame([summary]), 'preprocessing_summary.csv')
    
    print("\n📊 PREPROCESSING SUMMARY:")
    for key, val in summary.items():
        print(f"  {key}: {val}")
    
    print("\n✅ PREPROCESSING COMPLETE")

if __name__ == "__main__":
    main()
