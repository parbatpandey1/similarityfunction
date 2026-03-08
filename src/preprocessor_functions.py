"""
📊 Preprocessing utility functions - v6.0

FIX: normalize_level_columns now creates SHORT fixed column names:
     'main_level_norm' and 'additional_level_norm'
     Previously it created 'Your Expertise Level (Above Area)_norm'
     which didn't match the keys in MENTOR_AREAS/MENTEE_AREAS in config.py
     → This caused ALL expertise levels to be NaN downstream
"""
import pandas as pd
import numpy as np
from utils import *
from config import *


def load_and_validate_csv(filepath, role):
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
    cleaned = series.astype(str).str.lower().str.strip()
    cleaned = cleaned.replace(['nan', 'none', '', 'n/a'], np.nan)
    return cleaned


def extract_stream_from_roll(df, roll_col):
    if roll_col not in df.columns:
        df['stream_parsed'] = 'unknown'
        return df
    df['stream_parsed'] = df[roll_col].apply(parse_roll_number)
    stream_counts = df['stream_parsed'].value_counts()
    print(f"  Stream distribution: {dict(list(stream_counts.items())[:5])}")
    return df


def normalize_level_columns(df, level_cols, target_names=None):
    """
    Normalize expertise level columns to 0–1 range.

    FIX: Added 'target_names' parameter so caller can specify SHORT
    fixed column names instead of the auto-generated long ones.

    Args:
        df:           DataFrame to modify
        level_cols:   List of SOURCE column names (long CSV header names)
        target_names: List of TARGET column names to create (short fixed names)
                      If None, falls back to f'{col}_norm' (old broken behavior)
    """
    for i, col in enumerate(level_cols):
        # Determine the target column name
        if target_names and i < len(target_names):
            target = target_names[i]          # ← use short name e.g. 'main_level_norm'
        else:
            target = f'{col}_norm'            # fallback (long name, may cause issues)

        if col in df.columns:
            df[target] = normalize_expertise_level(df[col])
            valid_count = df[target].notna().sum()
            mean_val    = df[target].mean() if valid_count > 0 else 0
            print(f"  ✓ Normalized '{col}' → '{target}': "
                  f"{valid_count} valid, mean={mean_val:.3f}")
        else:
            print(f"  ⚠️  Column not found: '{col}' (setting {target}=NaN)")
            df[target] = np.nan
    return df


def combine_text_fields(df, fields):
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
    print("\n[Mentors] Preprocessing...")

    df = extract_stream_from_roll(df, MENTOR_COLS['roll'])

    # FIX: pass target_names=['main_level_norm', 'additional_level_norm']
    # These MUST match the level_col values in MENTOR_AREAS in config.py
    df = normalize_level_columns(
        df,
        level_cols   = [MENTOR_COLS['main_level'], MENTOR_COLS['additional_level']],
        target_names = ['main_level_norm', 'additional_level_norm']
    )

    if MENTOR_COLS['max_mentees'] in df.columns:
        df['capacity'] = parse_mentor_capacity(df[MENTOR_COLS['max_mentees']])
    else:
        df['capacity'] = DEFAULT_MENTOR_CAPACITY

    text_cols = [
        MENTOR_COLS['main_expertise'], MENTOR_COLS['additional_expertise'],
        MENTOR_COLS['experience'],     MENTOR_COLS['work']
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = clean_text_column(df[col])

    # Build aspiration context from experience + work affiliation
    df['aspiration_context'] = combine_text_fields(
        df, [MENTOR_COLS['experience'], MENTOR_COLS['work']]
    )

    print(f"✓ {len(df)} mentors | Total capacity: {df['capacity'].sum()}")
    return df


def preprocess_mentee_dataframe(df):
    print("\n[Mentees] Preprocessing...")

    df = extract_stream_from_roll(df, MENTEE_COLS['roll'])

    # FIX: pass target_names=['main_level_norm', 'additional_level_norm']
    # These MUST match the level_col values in MENTEE_AREAS in config.py
    df = normalize_level_columns(
        df,
        level_cols   = [MENTEE_COLS['main_level'], MENTEE_COLS['additional_level']],
        target_names = ['main_level_norm', 'additional_level_norm']
    )

    text_cols = [
        MENTEE_COLS['main_interest'],
        MENTEE_COLS['additional_interest'],
        MENTEE_COLS['aspirations']
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = clean_text_column(df[col])

    if MENTEE_COLS['additional_interest'] in df.columns:
        has_additional = df[MENTEE_COLS['additional_interest']].notna().sum()
        print(f"  ✓ Additional interests: {has_additional}/{len(df)} mentees")

    print(f"✓ {len(df)} mentees")
    return df


def generate_preprocessing_summary(mentors_df, mentees_df):
    summary = {
        'total_mentors':           len(mentors_df),
        'total_mentees':           len(mentees_df),
        'total_mentor_capacity':   int(mentors_df['capacity'].sum()),
        'avg_mentor_capacity':     float(mentors_df['capacity'].mean()),
        'mentors_with_main':       int(mentors_df[MENTOR_COLS['main_expertise']].notna().sum()),
        'mentors_with_additional': int(mentors_df[MENTOR_COLS['additional_expertise']].notna().sum()),
        'mentors_with_levels':     int(mentors_df['main_level_norm'].notna().sum()),
        'mentees_with_main':       int(mentees_df[MENTEE_COLS['main_interest']].notna().sum()),
        'mentees_with_additional': int(mentees_df[MENTEE_COLS['additional_interest']].notna().sum()),
        'mentees_with_aspirations':int(mentees_df[MENTEE_COLS['aspirations']].notna().sum()),
        'mentees_with_levels':     int(mentees_df['main_level_norm'].notna().sum()),
        'unique_mentor_streams':   int(mentors_df['stream_parsed'].nunique()),
        'unique_mentee_streams':   int(mentees_df['stream_parsed'].nunique())
    }
    return summary
