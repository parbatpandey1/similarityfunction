"""
🔧 Utility functions v6.0
"""
import pandas as pd
import numpy as np
import re
from pathlib import Path
from config import *

def ensure_output_dir():
    """Create output directory"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ Output directory: {OUTPUT_DIR}")

def parse_roll_number(roll):
    """
    Extract stream from roll number
    Examples: 079BCT055 → 'Computer'
    """
    if pd.isna(roll) or str(roll).strip() == '':
        return 'unknown'
    
    roll_str = str(roll).strip().upper()
    pattern = r'(\d{3})([A-Za-z]{3})(\d{3})'
    match = re.match(pattern, roll_str)
    
    if match:
        stream_code = match.group(2).lower()
        stream = STREAM_MAPPING.get(stream_code, None)
        
        if stream:
            return stream
        else:
            return f'unknown_{stream_code}'
    
    return 'invalid_format'

def normalize_expertise_level(series, min_val=EXPERTISE_MIN, max_val=EXPERTISE_MAX):
    """Normalize 1-5 ratings to 0-1 scale"""
    numeric = pd.to_numeric(series, errors='coerce')
    normalized = (numeric - min_val) / (max_val - min_val)
    return normalized.clip(0.0, 1.0)

def parse_mentor_capacity(series, default=DEFAULT_MENTOR_CAPACITY):
    """Extract and validate mentor capacity"""
    capacities = pd.to_numeric(series, errors='coerce')
    capacities = capacities.fillna(default)
    capacities = capacities.clip(upper=MAX_MENTEES_PER_MENTOR, lower=1)
    return capacities.astype(int)

def save_dataframe(df, filename, index=False):
    """Save dataframe to output directory"""
    filepath = OUTPUT_DIR / filename
    
    try:
        if filename.endswith('.csv'):
            df.to_csv(filepath, index=index)
        elif filename.endswith('.xlsx'):
            df.to_excel(filepath, index=index, engine='openpyxl')
        elif filename.endswith('.pkl'):
            df.to_pickle(filepath)
        else:
            raise ValueError(f"Unsupported file extension: {filename}")
        
        print(f"💾 Saved: {filename} ({len(df)} rows)")
        return filepath
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")
        raise

def save_numpy(array, filename):
    """Save numpy array to output directory"""
    filepath = OUTPUT_DIR / filename
    
    try:
        np.save(filepath, array)
        print(f"💾 Saved: {filename} (shape: {array.shape})")
        return filepath
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")
        raise

def load_from_output(filename):
    """Load file from output directory"""
    filepath = OUTPUT_DIR / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    try:
        if filename.endswith('.csv'):
            return pd.read_csv(filepath)
        elif filename.endswith('.pkl'):
            return pd.read_pickle(filepath)
        elif filename.endswith('.npy'):
            return np.load(filepath)
        else:
            raise ValueError(f"Unsupported file type: {filename}")
    except Exception as e:
        print(f"❌ Error loading {filename}: {e}")
        raise
