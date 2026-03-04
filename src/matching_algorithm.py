"""
🎯 Stage 4: Capacity-Constrained Matching v6.0
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
    
    # Group by person pair and keep row with highest final_similarity_score
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
    
    # Sort pairs by final_similarity_score (best first)
    sorted_pairs = dedup_df.sort_values('final_similarity_score', ascending=False).copy()
    
    # Initialize capacity tracking
    mentor_capacity = {}
    mentor_assigned = {}
    mentee_assigned = set()
    
    # Load mentor capacities
    for _, row in dedup_df[['mentor_person_id', 'mentor_capacity']].drop_duplicates().iterrows():
        mid = row['mentor_person_id']
        mentor_capacity[mid] = int(row['mentor_capacity'])
        mentor_assigned[mid] = 0
    
    assignments = []
    
    # Greedy assignment
    for _, pair in sorted_pairs.iterrows():
        mentee_id = pair['mentee_person_id']
        mentor_id = pair['mentor_person_id']
        
        # Skip if mentee already assigned
        if mentee_id in mentee_assigned:
            continue
        
        # Skip if mentor at capacity
        if mentor_assigned[mentor_id] >= mentor_capacity[mentor_id]:
            continue
        
        # Assign!
        assignments.append(pair.to_dict())
        mentor_assigned[mentor_id] += 1
        mentee_assigned.add(mentee_id)
        
        # Early exit if all mentees assigned
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
    """Get top N recommendations per mentee"""
    print(f"\n🏆 Generating top {n} recommendations...")
    
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
    
    return pd.DataFrame(recommendations)

def main():
    """Main matching pipeline"""
    print("\n" + "="*80)
    print("STAGE 4: CAPACITY-CONSTRAINED MATCHING v6.0")
    print("="*80)
    
    try:
        print("\n[1/3] Loading similarity results...")
        results_df = load_from_output('detailed_similarity_scores.pkl')
        
        print(f"  ✓ Loaded {len(results_df):,} pairs")
        print(f"  ✓ Non-zero scores: {(results_df['final_similarity_score'] > 0).sum():,}")
        
        print("\n[2/3] Deduplicating...")
        dedup_df = deduplicate_by_person(results_df)
        
        print("\n[3/3] Running matching...")
        assignments_df, mentor_usage = greedy_capacity_matching(dedup_df)
        recommendations_df = get_top_n_recommendations(dedup_df, TOP_N_MATCHES)
        
        print("\n💾 Saving...")
        save_dataframe(dedup_df, 'deduplicated_matches.csv')
        save_dataframe(assignments_df, 'final_assignments.csv')
        save_dataframe(recommendations_df, 'top_n_recommendations.csv')
        
        # Mentor utilization
        utilization_data = []
        for mid, count in mentor_usage.items():
            mentor_row = dedup_df[dedup_df['mentor_person_id']==mid].iloc[0]
            utilization_data.append({
                'mentor_id': mid,
                'mentor_name': mentor_row['mentor_name'],
                'capacity': int(mentor_row['mentor_capacity']),
                'assigned': count,
                'utilization_pct': round(100 * count / mentor_row['mentor_capacity'], 1)
            })
        
        utilization_df = pd.DataFrame(utilization_data)
        save_dataframe(utilization_df, 'mentor_utilization.csv')
        
        print(f"\n🎯 TOP 5 ASSIGNMENTS:")
        for _, row in assignments_df.head(5).iterrows():
            print(f"  {row['mentee_name'][:20]:20} ↔ {row['mentor_name'][:20]:20} (score: {row['final_similarity_score']:.4f})")
        
        print("\n✅ MATCHING COMPLETE")
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
