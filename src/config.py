"""
🎯 MENTORSHIP MATCHING SYSTEM v6.0 - CORRECTED DATA STRUCTURE
✅ Mentee: main_interest + additional_interest (both with levels)
✅ Aspirations matched separately with mentor work/experience
✅ Final score: 80% skill match + 20% aspiration match
"""
import os
from pathlib import Path

# ===== PATHS =====
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"
OUTPUT_DIR = BASE_DIR / "output"

MENTOR_FILE = BASE_DIR / "mentor_basic_info_updated.csv"
MENTEE_FILE = BASE_DIR / "mentee_basic_info_updated.csv"

# ===== STREAM MAPPING =====
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

# ===== CSV COLUMN MAPPINGS =====
MENTOR_COLS = {
    'name': 'Name',
    'roll': 'Campus Roll Number',
    'email': 'Personal email address',
    'stream': 'Engineering stream you will mentor for',
    'experience': 'Your Experience',
    'work': 'Current Work Affiliation (if applicable)',
    'main_expertise': 'Main Expertise',
    'main_level': 'Your Expertise Level (Above Area)',
    'additional_expertise': 'Additional Mentorship Areas (Optional)',
    'additional_level': 'Your Expertise Level (Optional)',
    'max_mentees': 'How many mentees will you be taking?',
    'hours': 'How many hours per week can you realistically dedicate to mentoring sessions ?',
    'contact': 'Where should your mentee contact you?'
}

MENTEE_COLS = {
    'name': 'Name',
    'roll': 'Campus Roll Number',
    'email': 'Personal email address',
    'department': 'Department',
    'main_interest': 'Main Interest',
    'main_level': 'Your Expertise Level (Above Area)',
    'additional_interest': 'Additional Interest',  # NEW!
    'additional_level': 'Expertise Level (Additional Interest)',  # NEW!
    'aspirations': 'Future Aspirations'
}

# ===== SKILL AREAS (CORRECTED!) =====
# 🔥 NEW: Both mentor and mentee have 2 skill entities
MENTOR_AREAS = [
    ('main_expertise', 'main_level_norm', 'main_expertise'),
    ('additional_expertise', 'additional_level_norm', 'additional_expertise')
]

MENTEE_AREAS = [
    ('main_interest', 'main_level_norm', 'main_interest'),
    ('additional_interest', 'additional_level_norm', 'additional_interest')  # NEW!
]

# ===== EMBEDDING CONFIGURATION =====
EMBEDDING_MODEL = "all-mpnet-base-v2"
EMBEDDING_BATCH_SIZE = 16

EMBED_SKILL_TEXT_ONLY = True
MEAN_CENTER_EMBEDDINGS = False

# ===== SKILL SIMILARITY FORMULA =====
# Same hierarchical formula as before
SEMANTIC_MIN_THRESHOLD = 0.25
USE_SEMANTIC_POWER = True
SEMANTIC_POWER = 1.2

OPTIMAL_EXPERTISE_GAP = 2.0
EXPERTISE_GAP_TOLERANCE = 1.5
EXPERTISE_MULTIPLIER_MAX = 1.40
EXPERTISE_MULTIPLIER_MIN = 0.65
EXPERTISE_MULTIPLIER_NEUTRAL = 1.0
MENTOR_LOWER_PENALTY = 0.70

STREAM_MATCH_BONUS = 0.08
FINAL_SIMILARITY_THRESHOLD = 0.30

# ===== ASPIRATION MATCHING (NEW!) =====
# Match mentee aspirations with mentor's work/experience

# Aspiration similarity threshold
ASPIRATION_MIN_THRESHOLD = 0.20  # Lower than skill threshold

# 🔥 FINAL SCORE COMPOSITION
SKILL_WEIGHT = 0.80  # 80% from skill matching
ASPIRATION_WEIGHT = 0.20  # 20% from aspiration matching

# ===== EXPERTISE NORMALIZATION =====
EXPERTISE_MIN, EXPERTISE_MAX = 1, 5

# ===== CAPACITY CONSTRAINTS =====
MAX_MENTEES_PER_MENTOR = 4
DEFAULT_MENTOR_CAPACITY = 2

# ===== OUTPUT SETTINGS =====
TOP_N_MATCHES = 5
SAVE_ALL_SCORES = True
