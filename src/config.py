"""
🎯 MENTORSHIP MATCHING SYSTEM v6.0 - CORRECTED DATA STRUCTURE
✅ Mentee: main_interest + additional_interest (both with levels)
✅ Aspirations matched separately with mentor work/experience
✅ Final score: 80% skill match + 20% aspiration match

FIXES APPLIED:
  - SEMANTIC_MIN_THRESHOLD: 0.25 → 0.40  (stops false cross-domain matches)
  - FINAL_SIMILARITY_THRESHOLD: 0.30 → 0.35
  - OPTIMAL_EXPERTISE_GAP: 2.0 → 0.5    (normalized scale: 2/4 = 0.5)
  - EXPERTISE_GAP_TOLERANCE: 1.5 → 0.375 (normalized scale: 1.5/4 = 0.375)
"""
import os
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent.parent
SRC_DIR    = BASE_DIR / "src"
OUTPUT_DIR = BASE_DIR / "output"

MENTOR_FILE = BASE_DIR / "mentor_basic_info_updated.csv"
MENTEE_FILE = BASE_DIR / "mentee_basic_info_updated.csv"

# ── Stream Mapping ───────────────────────────────────────────────────────────
STREAM_MAPPING = {
    'bct': 'Computer',
    'bei': 'Electronics (Communication/Information)',
    'bel': 'Electrical',
    'bar': 'Architecture',
    'bce': 'Civil',
    'bme': 'Mechanical',
    'bae': 'Aerospace',
    'bch': 'Chemical',
    'bex': 'Electronics (Communication/Information)'
}

# ── Column Mappings ──────────────────────────────────────────────────────────
MENTOR_COLS = {
    'name':                'Name',
    'roll':                'Campus Roll Number',
    'email':               'Personal email address',
    'stream':              'Engineering stream you will mentor for',
    'experience':          'Your Experience',
    'work':                'Current Work Affiliation (if applicable)',
    'main_expertise':      'Main Expertise',
    'main_level':          'Your Expertise Level (Above Area)',
    'additional_expertise':'Additional Mentorship Areas (Optional)',
    'additional_level':    'Your Expertise Level (Optional)',
    'max_mentees':         'How many mentees will you be taking?',
    'hours':               'How many hours per week can you realistically dedicate to mentoring sessions ?',
    'contact':             'Where should your mentee contact you?'
}

MENTEE_COLS = {
    'name':              'Name',
    'roll':              'Campus Roll Number',
    'email':             'Personal email address',
    'department':        'Department',
    'main_interest':     'Main Interest',
    'main_level':        'Your Expertise Level (Above Area)',
    'additional_interest':'Additional Interest',
    'additional_level':  'Expertise Level (Additional Interest)',
    'aspirations':       'Future Aspirations'
}

# ── Skill Areas ──────────────────────────────────────────────────────────────
# (skill_col_key, normalized_level_col, area_name)
# normalized_level_col MUST match what preprocessor_functions.normalize_level_columns creates
MENTOR_AREAS = [
    ('main_expertise',       'main_level_norm',       'main_expertise'),
    ('additional_expertise', 'additional_level_norm', 'additional_expertise')
]

MENTEE_AREAS = [
    ('main_interest',       'main_level_norm',       'main_interest'),
    ('additional_interest', 'additional_level_norm', 'additional_interest')
]

# ── Embedding Model ──────────────────────────────────────────────────────────
EMBEDDING_MODEL      = "all-mpnet-base-v2"
EMBEDDING_BATCH_SIZE = 16
EMBED_SKILL_TEXT_ONLY    = True
MEAN_CENTER_EMBEDDINGS   = False

# ── Similarity Thresholds ────────────────────────────────────────────────────
# FIX: raised from 0.25 → 0.40 to stop false cross-domain matches
# e.g. "machine learning" ↔ "structural analysis" was passing at 0.25
SEMANTIC_MIN_THRESHOLD  = 0.40
USE_SEMANTIC_POWER      = True
SEMANTIC_POWER          = 1.2

# ── Expertise Gap (Gaussian Bell Curve) ──────────────────────────────────────
# FIX: these constants are now in NORMALIZED (0–1) scale, not raw (1–5) scale
# Raw optimal gap = 2 levels  →  normalized = 2/4 = 0.5
# Raw tolerance   = 1.5 levels →  normalized = 1.5/4 = 0.375
OPTIMAL_EXPERTISE_GAP      = 0.5    # was 2.0 (raw scale) — now 0.5 (normalized)
EXPERTISE_GAP_TOLERANCE    = 0.375  # was 1.5 (raw scale) — now 0.375 (normalized)
EXPERTISE_MULTIPLIER_MAX   = 1.40
EXPERTISE_MULTIPLIER_MIN   = 0.65
EXPERTISE_MULTIPLIER_NEUTRAL = 1.0
MENTOR_LOWER_PENALTY       = 0.70

# ── Scoring ──────────────────────────────────────────────────────────────────
STREAM_MATCH_BONUS         = 0.08
# FIX: raised from 0.30 → 0.35
FINAL_SIMILARITY_THRESHOLD = 0.35

ASPIRATION_MIN_THRESHOLD   = 0.20
SKILL_WEIGHT               = 0.80
ASPIRATION_WEIGHT          = 0.20

# ── Data Constraints ─────────────────────────────────────────────────────────
EXPERTISE_MIN              = 1
EXPERTISE_MAX              = 5
MAX_MENTEES_PER_MENTOR     = 4
DEFAULT_MENTOR_CAPACITY    = 2
TOP_N_MATCHES              = 5
SAVE_ALL_SCORES            = True
