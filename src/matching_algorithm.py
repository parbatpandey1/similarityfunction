"""
🎯 Stage 4: Capacity-Constrained Matching v6.0
✅ Reciprocal Top 5: mentee-centric + mentor-centric views
✅ Rich matched dataset for personalized email generation
"""
import pandas as pd
import numpy as np
from utils import *
from config import *


def deduplicate_by_person(results_df):
    """
    Deduplicate matches by person IDs
    Keep best skill match per person pair
    """
    print("\n🔄 Deduplicating by person IDs...")

    before = len(results_df)

    dedup = results_df.loc[
        results_df.groupby(['mentee_person_id', 'mentor_person_id'])['final_similarity_score'].idxmax()
    ].copy()

    after = len(dedup)

    print(f"  ✓ Before: {before:,} | After: {after:,} | Removed: {before - after:,}")

    return dedup


def greedy_capacity_matching(dedup_df):
    """
    Greedy capacity-constrained matching
    Assigns each mentee to exactly 1 mentor respecting capacity limits
    """
    print("\n🎯 Running capacity-constrained matching...")

    sorted_pairs = dedup_df.sort_values('final_similarity_score', ascending=False).copy()

    mentor_capacity = {}
    mentor_assigned = {}
    mentee_assigned = set()

    for _, row in dedup_df[['mentor_person_id', 'mentor_capacity']].drop_duplicates().iterrows():
        mid = row['mentor_person_id']
        mentor_capacity[mid] = int(row['mentor_capacity'])
        mentor_assigned[mid] = 0

    assignments = []

    for _, pair in sorted_pairs.iterrows():
        mentee_id = pair['mentee_person_id']
        mentor_id = pair['mentor_person_id']

        if mentee_id in mentee_assigned:
            continue

        if mentor_assigned[mentor_id] >= mentor_capacity[mentor_id]:
            continue

        assignments.append(pair.to_dict())
        mentor_assigned[mentor_id] += 1
        mentee_assigned.add(mentee_id)

        if len(mentee_assigned) == dedup_df['mentee_person_id'].nunique():
            break

    assignments_df = pd.DataFrame(assignments)

    total_mentees = dedup_df['mentee_person_id'].nunique()
    assigned = len(assignments_df)

    print(f"\n📊 MATCHING RESULTS:")
    print(f"  ✅ Assigned: {assigned}/{total_mentees} ({100*assigned/total_mentees:.1f}%)")
    print(f"  👥 Active mentors: {sum(1 for c in mentor_assigned.values() if c > 0)}/{len(mentor_capacity)}")
    print(f"  📊 Capacity used: {sum(mentor_assigned.values())}/{sum(mentor_capacity.values())}")

    return assignments_df, mentor_assigned


def get_top_n_recommendations(dedup_df, n=TOP_N_MATCHES):
    """Get top N mentor recommendations per mentee (mentee-centric view)"""
    print(f"\n🏆 Generating top {n} mentors per mentee...")

    recommendations = []

    for mentee_id in dedup_df['mentee_person_id'].unique():
        mentee_matches = dedup_df[dedup_df['mentee_person_id'] == mentee_id].sort_values(
            'final_similarity_score', ascending=False
        ).head(n)

        for rank, (_, match) in enumerate(mentee_matches.iterrows(), 1):
            recommendations.append({
                **match.to_dict(),
                'recommendation_rank': rank
            })

    print(f"  ✓ {len(recommendations)} mentee-centric recommendations")
    return pd.DataFrame(recommendations)


def get_top_n_per_mentor(dedup_df, n=TOP_N_MATCHES):
    """Get top N mentee recommendations per mentor (mentor-centric view)"""
    print(f"\n🏆 Generating top {n} mentees per mentor...")

    recommendations = []

    for mentor_id in dedup_df['mentor_person_id'].unique():
        mentor_matches = dedup_df[dedup_df['mentor_person_id'] == mentor_id].sort_values(
            'final_similarity_score', ascending=False
        ).head(n)

        for rank, (_, match) in enumerate(mentor_matches.iterrows(), 1):
            recommendations.append({
                **match.to_dict(),
                'recommendation_rank': rank
            })

    print(f"  ✓ {len(recommendations)} mentor-centric recommendations")
    return pd.DataFrame(recommendations)


def build_rich_matched_dataset(assignments_df, mentors_df, mentees_df):
    """
    Build rich dataset joining matched pairs with FULL profile data.
    Every matched pair gets complete mentor + mentee info.
    Used directly for personalized email generation.
    """
    print("\n📋 Building rich matched dataset for email generation...")

    # --- Mentee profile columns to pull ---
    mentee_profile_cols = {
        MENTEE_COLS['name']:                'mentee_name',
        MENTEE_COLS['email']:               'mentee_email',
        MENTEE_COLS['roll']:                'mentee_roll',
        MENTEE_COLS['department']:          'mentee_department',
        MENTEE_COLS['main_interest']:       'mentee_main_interest',
        MENTEE_COLS['main_level']:          'mentee_main_level',
        MENTEE_COLS['additional_interest']: 'mentee_additional_interest',
        MENTEE_COLS['additional_level']:    'mentee_additional_level',
        MENTEE_COLS['aspirations']:         'mentee_aspirations',
    }

    # --- Mentor profile columns to pull ---
    mentor_profile_cols = {
        MENTOR_COLS['name']:                 'mentor_name',
        MENTOR_COLS['email']:                'mentor_email',
        MENTOR_COLS['roll']:                 'mentor_roll',
        MENTOR_COLS['experience']:           'mentor_experience',
        MENTOR_COLS['work']:                 'mentor_work_affiliation',
        MENTOR_COLS['main_expertise']:       'mentor_main_expertise',
        MENTOR_COLS['main_level']:           'mentor_main_level',
        MENTOR_COLS['additional_expertise']: 'mentor_additional_expertise',
        MENTOR_COLS['additional_level']:     'mentor_additional_level',
        MENTOR_COLS['hours']:                'mentor_hours_per_week',
        MENTOR_COLS['contact']:              'mentor_contact_preference',
        MENTOR_COLS['stream']:               'mentor_stream',
    }

    # --- Build mentee profile table ---
    mentee_cols_exist = {k: v for k, v in mentee_profile_cols.items() if k in mentees_df.columns}
    mentee_profile = mentees_df[list(mentee_cols_exist.keys())].copy()
    mentee_profile = mentee_profile.rename(columns=mentee_cols_exist)
    mentee_profile['mentee_person_id'] = mentees_df.index

    # --- Build mentor profile table ---
    mentor_cols_exist = {k: v for k, v in mentor_profile_cols.items() if k in mentors_df.columns}
    mentor_profile = mentors_df[list(mentor_cols_exist.keys())].copy()
    mentor_profile = mentor_profile.rename(columns=mentor_cols_exist)
    mentor_profile['mentor_person_id'] = mentors_df.index

    # --- Score columns to carry from assignments ---
    score_cols = [
        'mentee_person_id', 'mentor_person_id',
        'final_similarity_score', 'skill_score', 'aspiration_score',
        'semantic_similarity', 'expertise_gap', 'stream_bonus',
        'mentee_stream', 'mentor_stream'
    ]
    score_cols_exist = [c for c in score_cols if c in assignments_df.columns]
    scores = assignments_df[score_cols_exist].copy()

    # --- Merge all together ---
    rich_df = scores.merge(mentee_profile, on='mentee_person_id', how='left')
    rich_df = rich_df.merge(mentor_profile, on='mentor_person_id', how='left')

    # --- Match quality label ---
    def quality_label(score):
        if score >= 0.75:   return 'Excellent'
        elif score >= 0.55: return 'Good'
        elif score >= 0.40: return 'Fair'
        else:               return 'Weak'

    rich_df['match_quality'] = rich_df['final_similarity_score'].apply(quality_label)

    # --- Reorder columns for readability ---
    col_order = [
        'final_similarity_score', 'match_quality', 'skill_score',
        'aspiration_score', 'semantic_similarity', 'expertise_gap', 'stream_bonus',
        'mentee_name', 'mentee_email', 'mentee_roll', 'mentee_department',
        'mentee_stream', 'mentee_main_interest', 'mentee_main_level',
        'mentee_additional_interest', 'mentee_additional_level', 'mentee_aspirations',
        'mentor_name', 'mentor_email', 'mentor_roll', 'mentor_stream',
        'mentor_main_expertise', 'mentor_main_level',
        'mentor_additional_expertise', 'mentor_additional_level',
        'mentor_experience', 'mentor_work_affiliation',
        'mentor_hours_per_week', 'mentor_contact_preference',
    ]
    col_order_exist = [c for c in col_order if c in rich_df.columns]
    rich_df = rich_df[col_order_exist]
    rich_df = rich_df.sort_values('final_similarity_score', ascending=False).reset_index(drop=True)

    print(f"  ✅ Rich dataset: {len(rich_df)} matched pairs with full profiles")
    print(f"  ✓ Columns: {list(rich_df.columns)}")
    return rich_df


def main():
    """Main matching pipeline"""
    print("\n" + "="*80)
    print("STAGE 4: CAPACITY-CONSTRAINED MATCHING v6.0")
    print("="*80)

    try:
        print("\n[1/4] Loading similarity results...")
        results_df = load_from_output('detailed_similarity_scores.pkl')
        mentors_df = load_from_output('mentors_processed.pkl')
        mentees_df = load_from_output('mentees_processed.pkl')

        print(f"  ✓ Loaded {len(results_df):,} pairs")
        print(f"  ✓ Non-zero scores: {(results_df['final_similarity_score'] > 0).sum():,}")

        print("\n[2/4] Deduplicating...")
        dedup_df = deduplicate_by_person(results_df)

        print("\n[3/4] Running matching...")
        assignments_df, mentor_usage = greedy_capacity_matching(dedup_df)

        # Mentee-centric top 5
        recommendations_df = get_top_n_recommendations(dedup_df, TOP_N_MATCHES)

        # Mentor-centric top 5 (reciprocal)
        mentor_top_df = get_top_n_per_mentor(dedup_df, TOP_N_MATCHES)

        print("\n[4/4] Building rich matched dataset...")
        rich_df = build_rich_matched_dataset(assignments_df, mentors_df, mentees_df)

        print("\n💾 Saving...")
        save_dataframe(dedup_df,          'deduplicated_matches.csv')
        save_dataframe(assignments_df,    'final_assignments.csv')
        save_dataframe(recommendations_df,'top_n_recommendations.csv')
        save_dataframe(mentor_top_df,     'top_n_per_mentor.csv')
        save_dataframe(rich_df,           'rich_matched_dataset.csv')

        # Mentor utilization
        utilization_data = []
        for mid, count in mentor_usage.items():
            mentor_row = dedup_df[dedup_df['mentor_person_id']==mid].iloc[0]
            utilization_data.append({
                'mentor_id':       mid,
                'mentor_name':     mentor_row['mentor_name'],
                'capacity':        int(mentor_row['mentor_capacity']),
                'assigned':        count,
                'utilization_pct': round(100 * count / mentor_row['mentor_capacity'], 1)
            })

        utilization_df = pd.DataFrame(utilization_data)
        save_dataframe(utilization_df, 'mentor_utilization.csv')

        print(f"\n🎯 TOP 5 ASSIGNMENTS:")
        for _, row in assignments_df.head(5).iterrows():
            print(f"  {row['mentee_name'][:20]:20} ↔ {row['mentor_name'][:20]:20} "
                  f"(score: {row['final_similarity_score']:.4f} | quality: "
                  f"{rich_df[rich_df['mentee_name']==row['mentee_name']]['match_quality'].values[0] if len(rich_df[rich_df['mentee_name']==row['mentee_name']]) > 0 else 'N/A'})")

        print("\n✅ MATCHING COMPLETE")
        print("  📄 top_n_recommendations.csv  ← mentee-centric top 5")
        print("  📄 top_n_per_mentor.csv        ← mentor-centric top 5 (reciprocal)")
        print("  📄 rich_matched_dataset.csv    ← full profiles for emails")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
