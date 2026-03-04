"""
⚡ Similarity computation - v6.0 WITH ASPIRATION MATCHING
✅ Skill score (80%) + Aspiration score (20%)
"""
import pandas as pd
import numpy as np
from config import *

def compute_cosine_similarity(embeddings_a, embeddings_b):
    """Cosine similarity = dot product of normalized vectors"""
    return embeddings_a @ embeddings_b.T

def compute_expertise_gap_multiplier(mentee_meta, mentor_meta):
    """Expertise gap multiplier (same as before)"""
    mentee_levels = mentee_meta['expertise_level'].fillna(0.5).values.reshape(-1, 1)
    mentor_levels = mentor_meta['expertise_level'].fillna(0.5).values.reshape(1, -1)
    
    gap = mentor_levels - mentee_levels
    
    deviation = np.abs(gap - OPTIMAL_EXPERTISE_GAP)
    
    gaussian = np.exp(-0.5 * (deviation / EXPERTISE_GAP_TOLERANCE) ** 2)
    
    multiplier = EXPERTISE_MULTIPLIER_NEUTRAL + (
        (EXPERTISE_MULTIPLIER_MAX - EXPERTISE_MULTIPLIER_NEUTRAL) * gaussian
    )
    
    mentor_lower_mask = gap < 0
    multiplier = np.where(
        mentor_lower_mask,
        multiplier * MENTOR_LOWER_PENALTY,
        multiplier
    )
    
    multiplier = np.clip(multiplier, EXPERTISE_MULTIPLIER_MIN, EXPERTISE_MULTIPLIER_MAX)
    
    return multiplier

def compute_stream_bonus(mentee_meta, mentor_meta):
    """Stream bonus (same as before)"""
    n_mentees, n_mentors = len(mentee_meta), len(mentor_meta)
    stream_bonus = np.zeros((n_mentees, n_mentors))
    
    mentee_streams = mentee_meta['stream'].astype(str).values
    mentor_streams = mentor_meta['stream'].astype(str).values
    
    for i, ms in enumerate(mentee_streams):
        for j, ns in enumerate(mentor_streams):
            if (ms == ns and ms != 'unknown' and 
                'unknown' not in ms and 'invalid' not in ms):
                stream_bonus[i, j] = STREAM_MATCH_BONUS
    
    return stream_bonus

def compute_skill_similarity(semantic, expertise_multiplier, stream_bonus):
    """
    Compute skill similarity (hierarchical formula)
    Same as before
    """
    semantic_clipped = np.clip(semantic, 0.0, 1.0)
    
    if USE_SEMANTIC_POWER and SEMANTIC_POWER != 1.0:
        semantic_cal = semantic_clipped ** SEMANTIC_POWER
    else:
        semantic_cal = semantic_clipped
    
    semantic_gate = (semantic_cal >= SEMANTIC_MIN_THRESHOLD)
    
    base = semantic_cal * expertise_multiplier
    skill_score = base + stream_bonus
    
    skill_score = np.clip(skill_score, 0.0, 1.0)
    skill_score = np.where(semantic_gate, skill_score, 0.0)
    
    skill_gate = (skill_score >= FINAL_SIMILARITY_THRESHOLD)
    skill_score = np.where(skill_gate, skill_score, 0.0)
    
    return skill_score

def compute_aspiration_similarity(asp_semantic):
    """
    🔥 NEW: Compute aspiration similarity
    
    Simpler than skill matching (no expertise gap, no stream bonus)
    Just semantic similarity with lower threshold
    """
    asp_semantic_clipped = np.clip(asp_semantic, 0.0, 1.0)
    
    # Optional calibration (less aggressive)
    if USE_SEMANTIC_POWER:
        asp_semantic_cal = asp_semantic_clipped ** 1.1  # Lighter than skill (1.2)
    else:
        asp_semantic_cal = asp_semantic_clipped
    
    # Lower threshold for aspirations
    asp_gate = (asp_semantic_cal >= ASPIRATION_MIN_THRESHOLD)
    
    asp_score = np.where(asp_gate, asp_semantic_cal, 0.0)
    
    return asp_score

def combine_skill_and_aspiration_scores(skill_score, aspiration_score):
    """
    🔥 NEW: Combine skill and aspiration scores
    
    Final = 80% skill + 20% aspiration
    """
    final_score = (SKILL_WEIGHT * skill_score) + (ASPIRATION_WEIGHT * aspiration_score)
    
    final_score = np.clip(final_score, 0.0, 1.0)
    
    return final_score

def create_similarity_dataframe(sim_matrices, mentee_meta, mentor_meta, 
                                mentee_asp_meta=None, mentor_ctx_meta=None, 
                                aspiration_scores=None):
    """
    Create detailed DataFrame with all components
    Now includes aspiration scores!
    """
    skill_score = sim_matrices['skill_score']
    semantic = sim_matrices['semantic']
    expertise_mult = sim_matrices['expertise_multiplier']
    stream_bonus = sim_matrices['stream_bonus']
    
    n_mentees, n_mentors = skill_score.shape
    
    # Create person-level aspiration lookup (if available)
    asp_lookup = {}
    if aspiration_scores is not None and mentee_asp_meta is not None and mentor_ctx_meta is not None:
        for i, mentee_person_id in enumerate(mentee_asp_meta['person_id']):
            for j, mentor_person_id in enumerate(mentor_ctx_meta['person_id']):
                asp_lookup[(mentee_person_id, mentor_person_id)] = aspiration_scores[i, j]
    
    results = []
    for i in range(n_mentees):
        mentee_level = mentee_meta.iloc[i]['expertise_level']
        mentee_person_id = mentee_meta.iloc[i]['person_id']
        
        for j in range(n_mentors):
            mentor_level = mentor_meta.iloc[j]['expertise_level']
            mentor_person_id = mentor_meta.iloc[j]['person_id']
            
            gap = mentor_level - mentee_level if (pd.notna(mentee_level) and pd.notna(mentor_level)) else np.nan
            
            sem_cal = semantic[i, j] ** SEMANTIC_POWER if USE_SEMANTIC_POWER else semantic[i, j]
            base_score = sem_cal * expertise_mult[i, j]
            
            # Get aspiration score for this person pair
            asp_score = asp_lookup.get((mentee_person_id, mentor_person_id), 0.0)
            
            # Final score
            final_score = (SKILL_WEIGHT * skill_score[i, j]) + (ASPIRATION_WEIGHT * asp_score)
            final_score = min(max(final_score, 0.0), 1.0)
            
            results.append({
                'mentee_skill_id': i,
                'mentor_skill_id': j,
                'mentee_person_id': mentee_person_id,
                'mentee_name': mentee_meta.iloc[i]['person_name'],
                'mentee_roll': mentee_meta.iloc[i]['roll_number'],
                'mentee_stream': mentee_meta.iloc[i]['stream'],
                'mentee_skill_area': mentee_meta.iloc[i]['skill_area'],
                'mentee_skill_text': mentee_meta.iloc[i]['skill_text'],
                'mentee_expertise_level': mentee_level,
                
                'mentor_person_id': mentor_person_id,
                'mentor_name': mentor_meta.iloc[j]['person_name'],
                'mentor_roll': mentor_meta.iloc[j]['roll_number'],
                'mentor_stream': mentor_meta.iloc[j]['stream'],
                'mentor_skill_area': mentor_meta.iloc[j]['skill_area'],
                'mentor_skill_text': mentor_meta.iloc[j]['skill_text'],
                'mentor_expertise_level': mentor_level,
                'mentor_capacity': mentor_meta.iloc[j]['capacity'],
                
                'expertise_gap': gap,
                'semantic_similarity': semantic[i, j],
                'semantic_calibrated': sem_cal,
                'expertise_multiplier': expertise_mult[i, j],
                'base_score': base_score,
                'stream_bonus': stream_bonus[i, j],
                'skill_score': skill_score[i, j],
                'aspiration_score': asp_score,
                'final_similarity_score': final_score,
            })
    
    return pd.DataFrame(results)

def print_similarity_statistics(results_df):
    """Print comprehensive statistics"""
    non_zero = results_df[results_df['final_similarity_score'] > 0]
    
    print(f"\n📈 FINAL SIMILARITY STATISTICS:")
    print(f"{'='*80}")
    print(f"  Total pairs: {len(results_df):,}")
    print(f"  Non-zero: {len(non_zero):,} ({100*len(non_zero)/len(results_df):.1f}%)")
    print(f"  Zero (rejected): {(results_df['final_similarity_score'] == 0).sum():,}")
    print(f"\n  Best match: {results_df['final_similarity_score'].max():.4f}")
    print(f"  Average (all): {results_df['final_similarity_score'].mean():.4f}")
    if len(non_zero) > 0:
        print(f"  Average (non-zero): {non_zero['final_similarity_score'].mean():.4f}")
        print(f"  Median (non-zero): {non_zero['final_similarity_score'].median():.4f}")
    
    print(f"\n  Excellent (≥0.8): {(results_df['final_similarity_score'] >= 0.8).sum()}")
    print(f"  Good (≥0.7): {(results_df['final_similarity_score'] >= 0.7).sum()}")
    print(f"  Fair (≥0.6): {(results_df['final_similarity_score'] >= 0.6).sum()}")
    print(f"  Acceptable (≥0.5): {(results_df['final_similarity_score'] >= 0.5).sum()}")
    
    if len(non_zero) > 0:
        print(f"\n  📊 Component Averages (non-zero):")
        print(f"    Skill score: {non_zero['skill_score'].mean():.4f}")
        print(f"    Aspiration score: {non_zero['aspiration_score'].mean():.4f}")
        print(f"    Semantic: {non_zero['semantic_similarity'].mean():.4f}")
        print(f"    Expertise multiplier: {non_zero['expertise_multiplier'].mean():.4f}")
        
        if 'expertise_gap' in non_zero.columns:
            print(f"\n  📊 Expertise Gap Distribution:")
            print(f"    Avg gap: {non_zero['expertise_gap'].mean():.2f}")
            print(f"    Optimal (1.5-2.5): {((non_zero['expertise_gap'] >= 1.5) & (non_zero['expertise_gap'] <= 2.5)).sum()}")
    
    print(f"{'='*80}")
