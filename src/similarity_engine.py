"""
⚡ Stage 3: Similarity Engine v6.0
✅ Skill matching + Aspiration matching
✅ Final score = 80% skill + 20% aspiration
"""
import pandas as pd
import numpy as np
from similarity_functions import *
from utils import *
from config import *

def compute_all_similarities(mentee_embs, mentor_embs, mentee_meta, mentor_meta):
    """Compute skill similarity components"""
    print("\n⚡ Computing skill similarity...")
    print(f"   Formula: skill_score = (semantic^{SEMANTIC_POWER} * expertise_mult) + stream_bonus")
    
    assert mentee_embs.shape[0] == len(mentee_meta)
    assert mentor_embs.shape[0] == len(mentor_meta)
    
    print("\n  [1/4] Semantic similarity...")
    semantic = compute_cosine_similarity(mentee_embs, mentor_embs)
    print(f"    ✓ Range: [{semantic.min():.4f}, {semantic.max():.4f}]")
    
    print("\n  [2/4] Expertise gap multiplier...")
    expertise_mult = compute_expertise_gap_multiplier(mentee_meta, mentor_meta)
    print(f"    ✓ Range: [{expertise_mult.min():.4f}, {expertise_mult.max():.4f}]")
    
    print("\n  [3/4] Stream bonus...")
    stream_bonus = compute_stream_bonus(mentee_meta, mentor_meta)
    print(f"    ✓ Same stream: {(stream_bonus > 0).sum():,} pairs")
    
    print("\n  [4/4] Skill score calculation...")
    skill_score = compute_skill_similarity(semantic, expertise_mult, stream_bonus)
    print(f"    ✓ Non-zero: {(skill_score > 0).sum():,} pairs")
    
    return {
        'skill_score': skill_score,
        'semantic': semantic,
        'expertise_multiplier': expertise_mult,
        'stream_bonus': stream_bonus
    }

def compute_aspiration_similarities(mentee_asp_embs, mentor_ctx_embs, 
                                   mentee_asp_meta, mentor_ctx_meta):
    """
    🔥 NEW: Compute aspiration similarity
    """
    print("\n🎯 Computing aspiration similarity...")
    print(f"   Matching: mentee aspirations ↔ mentor work/experience")
    
    asp_semantic = compute_cosine_similarity(mentee_asp_embs, mentor_ctx_embs)
    print(f"    ✓ Semantic range: [{asp_semantic.min():.4f}, {asp_semantic.max():.4f}]")
    
    asp_score = compute_aspiration_similarity(asp_semantic)
    print(f"    ✓ Non-zero: {(asp_score > 0).sum():,} pairs")
    
    return asp_score, asp_semantic

def main():
    """Main similarity pipeline"""
    print("\n" + "="*80)
    print("STAGE 3: SIMILARITY COMPUTATION v6.0")
    print("  ✅ Skill matching (80%): main + additional interests")
    print("  ✅ Aspiration matching (20%): future goals ↔ work/experience")
    print("="*80)
    
    try:
        print("\n[1/4] Loading skill embeddings...")
        mentee_embs = load_from_output('mentee_embeddings.npy')
        mentor_embs = load_from_output('mentor_embeddings.npy')
        mentee_meta = load_from_output('mentee_metadata.pkl')
        mentor_meta = load_from_output('mentor_metadata.pkl')
        
        print(f"  ✓ {len(mentee_embs)} mentee × {len(mentor_embs)} mentor skill entities")
        
        print("\n[2/4] Computing skill similarities...")
        skill_matrices = compute_all_similarities(mentee_embs, mentor_embs, mentee_meta, mentor_meta)
        
        print("\n[3/4] Loading aspiration embeddings...")
        try:
            mentee_asp_embs = load_from_output('mentee_aspiration_embeddings.npy')
            mentor_ctx_embs = load_from_output('mentor_context_embeddings.npy')
            mentee_asp_meta = load_from_output('mentee_aspiration_metadata.pkl')
            mentor_ctx_meta = load_from_output('mentor_context_metadata.pkl')
            
            print(f"  ✓ {len(mentee_asp_embs)} mentee × {len(mentor_ctx_embs)} mentor aspiration entities")
            
            aspiration_scores, asp_semantic = compute_aspiration_similarities(
                mentee_asp_embs, mentor_ctx_embs, mentee_asp_meta, mentor_ctx_meta
            )
            
            has_aspirations = True
            
        except FileNotFoundError:
            print("  ⚠️  No aspiration embeddings found, using skill-only matching")
            aspiration_scores = None
            mentee_asp_meta = None
            mentor_ctx_meta = None
            has_aspirations = False
        
        print("\n[4/4] Creating detailed results...")
        results_df = create_similarity_dataframe(
            skill_matrices, mentee_meta, mentor_meta,
            mentee_asp_meta, mentor_ctx_meta, aspiration_scores
        )
        
        print("\n💾 Saving...")
        save_numpy(skill_matrices['skill_score'], 'skill_similarity_matrix.npy')
        save_numpy(skill_matrices['semantic'], 'semantic_similarity.npy')
        save_numpy(skill_matrices['expertise_multiplier'], 'expertise_multiplier.npy')
        save_numpy(skill_matrices['stream_bonus'], 'stream_bonus.npy')
        
        if has_aspirations:
            save_numpy(aspiration_scores, 'aspiration_similarity_matrix.npy')
        
        save_dataframe(results_df, 'detailed_similarity_scores.csv')
        save_dataframe(results_df, 'detailed_similarity_scores.pkl')
        
        print_similarity_statistics(results_df)
        
        print(f"\n🏆 TOP 5 MATCHES:")
        top5 = results_df.nlargest(5, 'final_similarity_score')
        print(top5[['mentee_name', 'mentee_skill_text', 'mentor_name', 'mentor_skill_text',
                    'skill_score', 'aspiration_score', 'final_similarity_score']])
        
        print("\n✅ SIMILARITY COMPUTATION COMPLETE")
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
