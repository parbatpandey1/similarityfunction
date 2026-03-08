"""
⚡ Stage 3: Similarity Engine v6.0
"""
import pandas as pd
import numpy as np
from similarity_functions import *
from utils import *
from config import *


def compute_all_similarities(mentee_embs, mentor_embs, mentee_meta, mentor_meta):
    print("\n⚡ Computing skill similarity matrices...")

    semantic        = compute_cosine_similarity(mentee_embs, mentor_embs)
    expertise_mult  = compute_expertise_gap_multiplier(mentee_meta, mentor_meta)
    stream_bonus    = compute_stream_bonus(mentee_meta, mentor_meta)
    skill_score     = compute_skill_similarity(semantic, expertise_mult, stream_bonus)

    # Diagnostic: verify multiplier varies (will be constant if levels are NaN)
    mult_range = expertise_mult.max() - expertise_mult.min()
    if mult_range < 0.001:
        print(f"  ⚠️  WARNING: expertise_multiplier has no variation ({expertise_mult.mean():.4f})")
        print(f"      Check that 'main_level_norm' column exists in mentor/mentee metadata.")
    else:
        print(f"  ✅ Expertise multiplier: {expertise_mult.min():.3f} – {expertise_mult.max():.3f}")

    return {
        'skill_score':         skill_score,
        'semantic':            semantic,
        'expertise_multiplier':expertise_mult,
        'stream_bonus':        stream_bonus
    }


def compute_aspiration_similarities(mentee_asp_embs, mentor_ctx_embs,
                                    mentee_asp_meta, mentor_ctx_meta):
    print("\n🎯 Computing aspiration similarity...")
    asp_semantic = compute_cosine_similarity(mentee_asp_embs, mentor_ctx_embs)
    asp_score    = compute_aspiration_similarity(asp_semantic)
    non_zero     = (asp_score > 0).sum()
    print(f"    ✓ Non-zero aspiration pairs: {non_zero:,}")
    return asp_score, asp_semantic


def main():
    print("\n" + "="*80)
    print("STAGE 3: SIMILARITY COMPUTATION v6.0")
    print("="*80)

    try:
        print("\n[1/4] Loading skill embeddings...")
        mentee_embs = load_from_output('mentee_embeddings.npy')
        mentor_embs = load_from_output('mentor_embeddings.npy')
        mentee_meta = load_from_output('mentee_metadata.pkl')
        mentor_meta = load_from_output('mentor_metadata.pkl')

        print(f"  ✓ Mentee: {len(mentee_meta)} skill entities")
        print(f"  ✓ Mentor: {len(mentor_meta)} skill entities")

        # Quick sanity check on expertise levels
        valid_mentee = mentee_meta['expertise_level'].notna().sum()
        valid_mentor = mentor_meta['expertise_level'].notna().sum()
        print(f"  ✓ Expertise levels valid: {valid_mentee}/{len(mentee_meta)} mentees, "
              f"{valid_mentor}/{len(mentor_meta)} mentors")
        if valid_mentee == 0 or valid_mentor == 0:
            print(f"  ⚠️  WARNING: expertise levels are all NaN!")
            print(f"      Re-run Stage 1 (preprocessor) to fix.")

        print("\n[2/4] Computing skill similarities...")
        skill_matrices = compute_all_similarities(mentee_embs, mentor_embs,
                                                  mentee_meta, mentor_meta)

        print("\n[3/4] Loading aspiration embeddings...")
        try:
            mentee_asp_embs = load_from_output('mentee_aspiration_embeddings.npy')
            mentor_ctx_embs = load_from_output('mentor_context_embeddings.npy')
            mentee_asp_meta = load_from_output('mentee_aspiration_metadata.pkl')
            mentor_ctx_meta = load_from_output('mentor_context_metadata.pkl')
            aspiration_scores, _ = compute_aspiration_similarities(
                mentee_asp_embs, mentor_ctx_embs, mentee_asp_meta, mentor_ctx_meta
            )
            has_aspirations = True
        except FileNotFoundError:
            print("  ⚠️  No aspiration embeddings found — using skill-only for all pairs")
            aspiration_scores = None
            mentee_asp_meta   = None
            mentor_ctx_meta   = None
            has_aspirations   = False

        print("\n[4/4] Creating detailed results DataFrame...")
        results_df = create_similarity_dataframe(
            skill_matrices, mentee_meta, mentor_meta,
            mentee_asp_meta, mentor_ctx_meta, aspiration_scores
        )

        # Save outputs
        save_numpy(skill_matrices['skill_score'], 'skill_similarity_matrix.npy')
        save_dataframe(results_df, 'detailed_similarity_scores.csv')
        save_dataframe(results_df, 'detailed_similarity_scores.pkl')

        if has_aspirations:
            save_numpy(aspiration_scores, 'aspiration_similarity_matrix.npy')

        print_similarity_statistics(results_df)
        print("\n✅ SIMILARITY COMPUTATION COMPLETE")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
