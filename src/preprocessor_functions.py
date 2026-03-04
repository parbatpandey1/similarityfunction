"""
📊 Preprocessing utility functions - UPDATED FOR v6.0
✅ Mentee additional_interest handling
"""
import pandas as pd
import numpy as np
from utils import *
from config import *

def load_and_validate_csv(filepath, role):
    """Load CSV with validation"""
    try:
        df = pd.read_csv(filepath)
        print(f"📥 Loaded {len(df)} {role}s from {filepath.name}")
        
        if len(df) == 0:
            raise ValueError(f"Empty CSV file: {filepath}")
        
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ Missing file: {filepath}")
    except Exception as e:
        raise Exception(f"❌ Error loading {filepath}: {e}")

def clean_text_column(series):
    """Clean text column"""
    cleaned = series.astype(str).str.lower().str.strip()
    cleaned = cleaned.replace(['nan', 'none', '', 'n/a'], np.nan)
    return cleaned

def extract_stream_from_roll(df, roll_col):
    """Extract stream from roll number column"""
    if roll_col not in df.columns:
        print(f"⚠️  Roll column '{roll_col}' not found, skipping stream extraction")
        df['stream_parsed'] = 'unknown'
        return df
    
    df['stream_parsed'] = df[roll_col].apply(parse_roll_number)
    
    stream_counts = df['stream_parsed'].value_counts()
    print(f"  Stream distribution: {dict(list(stream_counts.items())[:5])}")
    
    return df

def normalize_level_columns(df, level_cols):
    """Normalize all level columns"""
    for col in level_cols:
        if col in df.columns:
            df[f'{col}_norm'] = normalize_expertise_level(df[col])
            valid_count = df[f'{col}_norm'].notna().sum()
            if valid_count > 0:
                print(f"  ✓ Normalized {col}: {valid_count} valid, range [{df[f'{col}_norm'].min():.2f}, {df[f'{col}_norm'].max():.2f}]")
        else:
            print(f"  ⚠️  Column not found: {col}")
    return df

def combine_text_fields(df, fields):
    """
    🔥 NEW: Combine multiple text fields for aspiration matching
    Example: experience="Industry, Academia" + work="ML Engineer at Google"
    → "Industry Academia ML Engineer Google"
    """
    combined = []
    
    for _, row in df.iterrows():
        texts = []
        for field in fields:
            val = row.get(field, '')
            if pd.notna(val) and str(val).strip() and str(val).lower() != 'nan':
                texts.append(str(val).strip())
        
        combined.append(' '.join(texts) if texts else np.nan)
    
    return pd.Series(combined, index=df.index)

def preprocess_mentor_dataframe(df):
    """Complete mentor preprocessing with aspiration context"""
    print("\n[Mentors] Preprocessing...")
    
    df = extract_stream_from_roll(df, MENTOR_COLS['roll'])
    
    df = normalize_level_columns(df, [MENTOR_COLS['main_level'], MENTOR_COLS['additional_level']])
    
    if MENTOR_COLS['max_mentees'] in df.columns:
        df['capacity'] = parse_mentor_capacity(df[MENTOR_COLS['max_mentees']])
        print(f"  ✓ Capacity: min={df['capacity'].min()}, max={df['capacity'].max()}, total={df['capacity'].sum()}")
    else:
        df['capacity'] = DEFAULT_MENTOR_CAPACITY
        print(f"  ⚠️  No capacity column, using default: {DEFAULT_MENTOR_CAPACITY}")
    
    # Clean text columns
    text_cols = [MENTOR_COLS['main_expertise'], MENTOR_COLS['additional_expertise'], 
                 MENTOR_COLS['experience'], MENTOR_COLS['work']]
    for col in text_cols:
        if col in df.columns:
            df[col] = clean_text_column(df[col])
    
    # 🔥 NEW: Create combined aspiration context (experience + work)
    df['aspiration_context'] = combine_text_fields(df, [MENTOR_COLS['experience'], MENTOR_COLS['work']])
    valid_context = df['aspiration_context'].notna().sum()
    print(f"  ✓ Aspiration context: {valid_context}/{len(df)} mentors have work/experience data")
    
    print(f"✓ {len(df)} mentors | Total capacity: {df['capacity'].sum()}")
    return df

def preprocess_mentee_dataframe(df):
    """Complete mentee preprocessing with additional_interest"""
    print("\n[Mentees] Preprocessing...")
    
    df = extract_stream_from_roll(df, MENTEE_COLS['roll'])
    
    # 🔥 UPDATED: Normalize BOTH main and additional interest levels
    df = normalize_level_columns(df, [MENTEE_COLS['main_level'], MENTEE_COLS['additional_level']])
    
    # Clean text columns
    text_cols = [MENTEE_COLS['main_interest'], MENTEE_COLS['additional_interest'], MENTEE_COLS['aspirations']]
    for col in text_cols:
        if col in df.columns:
            df[col] = clean_text_column(df[col])
    
    # Check additional interest coverage
    if MENTEE_COLS['additional_interest'] in df.columns:
        has_additional = df[MENTEE_COLS['additional_interest']].notna().sum()
        print(f"  ✓ Additional interests: {has_additional}/{len(df)} mentees")
    
    print(f"✓ {len(df)} mentees")
    return df

def generate_preprocessing_summary(mentors_df, mentees_df):
    """Generate preprocessing summary"""
    summary = {
        'total_mentors': len(mentors_df),
        'total_mentees': len(mentees_df),
        'total_mentor_capacity': int(mentors_df['capacity'].sum()),
        'avg_mentor_capacity': float(mentors_df['capacity'].mean()),
        'mentors_with_main': int(mentors_df[MENTOR_COLS['main_expertise']].notna().sum()),
        'mentors_with_additional': int(mentors_df[MENTOR_COLS['additional_expertise']].notna().sum()),
        'mentees_with_main': int(mentees_df[MENTEE_COLS['main_interest']].notna().sum()),
        'mentees_with_additional': int(mentees_df[MENTEE_COLS['additional_interest']].notna().sum()),
        'mentees_with_aspirations': int(mentees_df[MENTEE_COLS['aspirations']].notna().sum()),
        'unique_mentor_streams': int(mentors_df['stream_parsed'].nunique()),
        'unique_mentee_streams': int(mentees_df['stream_parsed'].nunique())
    }
    return summary
