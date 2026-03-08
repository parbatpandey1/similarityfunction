"""
⚡ Similarity computation functions v6.0

FIXES APPLIED:
  1. complex number bug: clip semantic to 0 BEFORE power transform
  2. base_score clipped to 1.0 before storing in CSV
  3. Aspiration fallback: mentors with no context use skill-only formula
  4. Aspiration guard: skill_score=0 → final=0 (aspiration cannot rescue a failed match)
"""
import pandas as pd
import numpy as np
from config import *


def compute_cosine_similarity(embeddings_a, embeddings_b):
    """Cosine similarity via dot product (embeddings must be L2-normalized)."""
    return embeddings_a @ embeddings_b.T


def compute_expertise_gap_multiplier(mentee_meta, mentor_meta):
    """
    Gaussian bell curve rewarding optimal 2-level expertise gap.
    Works on NORMALIZED levels (0–1 scale).
    OPTIMAL_EXPERTISE_GAP = 0.5  (= 2 levels / 4 = 2/(5-1))
    """
    mentee_levels = mentee_meta['expertise_level'].fillna(0.25).values.reshape(-1, 1)
    mentor_levels = mentor_meta['expertise_level'].fillna(0.25).values.reshape(1, -1)

    gap       = mentor_levels - mentee_levels
    deviation = np.abs(gap - OPTIMAL_EXPERTISE_GAP)
    gaussian  = np.exp(-0.5 * (deviation / EXPERTISE_GAP_TOLERANCE) ** 2)

    multiplier = EXPERTISE_MULTIPLIER_NEUTRAL + (
        (EXPERTISE_MULTIPLIER_MAX - EXPERTISE_MULTIPLIER_NEUTRAL) * gaussian
    )

    # Penalty when mentor level is BELOW mentee level
    mentor_lower_mask = gap < 0
    multiplier = np.where(mentor_lower_mask, multiplier * MENTOR_LOWER_PENALTY, multiplier)
    multiplier = np.clip(multiplier, EXPERTISE_MULTIPLIER_MIN, EXPERTISE_MULTIPLIER_MAX)

    return multiplier


def compute_stream_bonus(mentee_meta, mentor_meta):
    """Add stream_bonus for same-department pairs."""
    n_mentees      = len(mentee_meta)
    n_mentors      = len(mentor_meta)
    stream_bonus   = np.zeros((n_mentees, n_mentors))
    mentee_streams = mentee_meta['stream'].astype(str).values
    mentor_streams = mentor_meta['stream'].astype(str).values

    for i, ms in enumerate(mentee_streams):
        for j, ns in enumerate(mentor_streams):
            if (ms == ns
                    and ms != 'unknown'
                    and 'unknown' not in ms
                    and 'invalid' not in ms):
                stream_bonus[i, j] = STREAM_MATCH_BONUS
    return stream_bonus


def compute_skill_similarity(semantic, expertise_multiplier, stream_bonus):
    """
    Final skill score formula:
        1. Clip negative values to 0 (prevents complex numbers in power transform)
        2. Power transform on semantic  (reduces mid-range inflation)
        3. Multiply by expertise multiplier  (rewards optimal gap)
        4. Add stream bonus
        5. Gate 1: semantic_calibrated < threshold → 0
        6. Gate 2: skill_score < final threshold  → 0
    """
    semantic_clipped = np.clip(semantic, 0.0, 1.0)

    if USE_SEMANTIC_POWER and SEMANTIC_POWER != 1.0:
        semantic_cal = semantic_clipped ** SEMANTIC_POWER
    else:
        semantic_cal = semantic_clipped

    semantic_gate = (semantic_cal >= SEMANTIC_MIN_THRESHOLD)

    base        = semantic_cal * expertise_multiplier
    skill_score = base + stream_bonus
    skill_score = np.clip(skill_score, 0.0, 1.0)

    # Gate 1: kill pairs below semantic threshold
    skill_score = np.where(semantic_gate, skill_score, 0.0)

    # Gate 2: kill pairs below final skill threshold
    skill_gate  = (skill_score >= FINAL_SIMILARITY_THRESHOLD)
    skill_score = np.where(skill_gate, skill_score, 0.0)

    return skill_score


def compute_aspiration_similarity(asp_semantic):
    """Power transform + gate on aspiration semantic similarity."""
    asp_clipped = np.clip(asp_semantic, 0.0, 1.0)
    asp_cal     = asp_clipped ** 1.1 if USE_SEMANTIC_POWER else asp_clipped
    asp_gate    = (asp_cal >= ASPIRATION_MIN_THRESHOLD)
    asp_score   = np.where(asp_gate, asp_cal, 0.0)
    return asp_score


def create_similarity_dataframe(sim_matrices, mentee_meta, mentor_meta,
                                mentee_asp_meta=None, mentor_ctx_meta=None,
                                aspiration_scores=None):
    """
    Build the full detailed similarity results DataFrame.

    FIX 1 (complex number): clip semantic to 0 BEFORE power transform.
    FIX 2 (base_score > 1.0): clipped to 1.0 before storing.
    FIX 3 (aspiration fallback): skill-only formula when no context data.
    FIX 4 (aspiration guard): if skill_score=0 → final=0.
                              Aspiration cannot rescue a completely failed skill match.
    """
    skill_score    = sim_matrices['skill_score']
    semantic       = sim_matrices['semantic']
    expertise_mult = sim_matrices['expertise_multiplier']
    stream_bonus   = sim_matrices['stream_bonus']
    n_mentees, n_mentors = skill_score.shape

    # Build aspiration lookup: (mentee_person_id, mentor_person_id) → score
    asp_lookup = {}
    if (aspiration_scores is not None
            and mentee_asp_meta is not None
            and mentor_ctx_meta is not None
            and len(mentee_asp_meta) > 0
            and len(mentor_ctx_meta) > 0):
        for i, mentee_pid in enumerate(mentee_asp_meta['person_id']):
            for j, mentor_pid in enumerate(mentor_ctx_meta['person_id']):
                asp_lookup[(int(mentee_pid), int(mentor_pid))] = float(aspiration_scores[i, j])

    # Track which person_ids have aspiration context data
    mentees_with_asp = set(
        int(x) for x in mentee_asp_meta['person_id'].tolist()
    ) if (mentee_asp_meta is not None and len(mentee_asp_meta) > 0) else set()

    mentors_with_ctx = set(
        int(x) for x in mentor_ctx_meta['person_id'].tolist()
    ) if (mentor_ctx_meta is not None and len(mentor_ctx_meta) > 0) else set()

    results = []
    for i in range(n_mentees):
        mentee_level     = mentee_meta.iloc[i]['expertise_level']
        mentee_person_id = int(mentee_meta.iloc[i]['person_id'])

        for j in range(n_mentors):
            mentor_level     = mentor_meta.iloc[j]['expertise_level']
            mentor_person_id = int(mentor_meta.iloc[j]['person_id'])

            # Expertise gap (normalized scale)
            gap = (float(np.real(mentor_level)) - float(np.real(mentee_level))
                   if (pd.notna(mentee_level) and pd.notna(mentor_level))
                   else np.nan)

            # FIX 1: clip to 0 BEFORE power transform — prevents complex numbers
            sem_val = max(0.0, float(np.real(semantic[i, j])))
            sem_cal = (sem_val ** SEMANTIC_POWER if USE_SEMANTIC_POWER else sem_val)

            asp_score      = asp_lookup.get((mentee_person_id, mentor_person_id), 0.0)
            current_skill  = float(skill_score[i, j])

            has_asp_data = (mentee_person_id in mentees_with_asp
                            and mentor_person_id in mentors_with_ctx)

            # FIX 3 + FIX 4:
            #   FIX 3 — no aspiration context → skill-only (no 20% penalty)
            #   FIX 4 — skill=0 → final=0 (aspiration cannot rescue failed matches)
            if has_asp_data and current_skill > 0:
                final_score = SKILL_WEIGHT * current_skill + ASPIRATION_WEIGHT * asp_score
            else:
                final_score = current_skill   # either skill-only OR 0 if skill failed

            final_score = min(max(final_score, 0.0), 1.0)

            # FIX 2: clip base_score to 1.0 before storing
            raw_base    = sem_cal * float(expertise_mult[i, j])
            stored_base = min(raw_base, 1.0)

            results.append({
                'mentee_skill_id':        i,
                'mentor_skill_id':        j,
                'mentee_person_id':       mentee_person_id,
                'mentee_name':            mentee_meta.iloc[i]['person_name'],
                'mentee_roll':            mentee_meta.iloc[i]['roll_number'],
                'mentee_stream':          mentee_meta.iloc[i]['stream'],
                'mentee_skill_area':      mentee_meta.iloc[i]['skill_area'],
                'mentee_skill_text':      mentee_meta.iloc[i]['skill_text'],
                'mentee_expertise_level': mentee_level,
                'mentor_person_id':       mentor_person_id,
                'mentor_name':            mentor_meta.iloc[j]['person_name'],
                'mentor_roll':            mentor_meta.iloc[j]['roll_number'],
                'mentor_stream':          mentor_meta.iloc[j]['stream'],
                'mentor_skill_area':      mentor_meta.iloc[j]['skill_area'],
                'mentor_skill_text':      mentor_meta.iloc[j]['skill_text'],
                'mentor_expertise_level': mentor_level,
                'mentor_capacity':        mentor_meta.iloc[j]['capacity'],
                'expertise_gap':          gap,
                'semantic_similarity':    float(np.real(semantic[i, j])),
                'semantic_calibrated':    sem_cal,
                'expertise_multiplier':   float(expertise_mult[i, j]),
                'base_score':             stored_base,
                'stream_bonus':           float(stream_bonus[i, j]),
                'skill_score':            current_skill,
                'aspiration_score':       asp_score,
                'has_aspiration_data':    has_asp_data,
                'final_similarity_score': final_score,
            })

    return pd.DataFrame(results)


def print_similarity_statistics(results_df):
    non_zero = results_df[results_df['final_similarity_score'] > 0]

    print(f"\n📈 SIMILARITY STATISTICS:")
    print(f"  Total pairs:          {len(results_df):,}")
    print(f"  Non-zero:             {len(non_zero):,} ({100*len(non_zero)/len(results_df):.1f}%)")
    print(f"  Best final score:     {results_df['final_similarity_score'].max():.4f}")
    print(f"  Avg final (all):      {results_df['final_similarity_score'].mean():.4f}")

    if len(non_zero) > 0:
        print(f"  Avg final (non-zero): {non_zero['final_similarity_score'].mean():.4f}")
        print(f"  Avg skill score:      {non_zero['skill_score'].mean():.4f}")
        print(f"  Avg aspiration:       {non_zero['aspiration_score'].mean():.4f}")

    # Aspiration guard check
    leaked = results_df[
        (results_df['skill_score'] == 0) &
        (results_df['final_similarity_score'] > 0)
    ]
    if len(leaked) > 0:
        print(f"\n  ⚠️  WARNING: {len(leaked)} pairs have skill=0 but final>0 (aspiration leak!)")
    else:
        print(f"\n  ✅ Aspiration guard working — no skill=0 leaks")

    # Aspiration coverage
    if 'has_aspiration_data' in results_df.columns:
        no_asp = (~results_df['has_aspiration_data']).sum()
        if no_asp > 0:
            print(f"  ℹ️  {no_asp:,} pairs used skill-only formula (no aspiration context)")

    # Multiplier range
    mult_min = results_df['expertise_multiplier'].min()
    mult_max = results_df['expertise_multiplier'].max()
    print(f"\n  Expertise multiplier: {mult_min:.4f} – {mult_max:.4f}")
    if abs(mult_max - mult_min) < 0.001:
        print(f"  ⚠️  WARNING: Multipliers identical → expertise levels still NaN! Re-run Stage 1.")
    else:
        print(f"  ✅ Multiplier varies correctly")

    # Expertise level population check
    valid_mentee = results_df['mentee_expertise_level'].notna().sum()
    valid_mentor = results_df['mentor_expertise_level'].notna().sum()
    total        = len(results_df)
    print(f"\n  Expertise levels: mentee {100*valid_mentee/total:.0f}% | mentor {100*valid_mentor/total:.0f}%")
