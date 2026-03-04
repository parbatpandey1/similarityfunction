"""
🔮 Stage 2: Embedding Generation - v6.0
✅ Separate embeddings for skills and aspirations
"""
import pandas as pd
import numpy as np
from embedder_functions import *
from utils import *
from config import *

def generate_skill_entities_with_embeddings(df, areas, role, col_mapping):
    """Generate skill embeddings"""
    print(f"\n🔮 Generating {role} skill entities...")
    
    model = initialize_embedding_model(EMBEDDING_MODEL)
    
    entities = extract_skill_entities(df, areas, role, col_mapping)
    print(f"  ✓ Extracted {len(entities)} skill entities")
    
    prompts = [e['prompt'] for e in entities]
    
    embeddings = generate_embeddings_batch(model, prompts, EMBEDDING_BATCH_SIZE)
    
    metadata = create_metadata_dataframe(entities)
    
    assert len(embeddings) == len(metadata), "Embedding-metadata mismatch!"
    
    print(f"  ✅ Created {len(metadata)} {role} skill entities (dim: {embeddings.shape[1]})")
    return embeddings, metadata, model

def main():
    """Main embedding generation pipeline"""
    print("\n" + "="*80)
    print("STAGE 2: EMBEDDING GENERATION v6.0")
    print("  ✅ Skills: main_interest + additional_interest")
    print("  ✅ Aspirations: future goals ↔ mentor work/experience")
    print("="*80)
    
    try:
        print("\n[1/5] Loading preprocessed data...")
        mentors_df = load_from_output('mentors_processed.pkl')
        mentees_df = load_from_output('mentees_processed.pkl')
        
        print("\n[2/5] Generating mentor skill embeddings...")
        mentor_embs, mentor_meta, model = generate_skill_entities_with_embeddings(
            mentors_df, MENTOR_AREAS, 'mentor', MENTOR_COLS
        )
        
        print("\n[3/5] Generating mentee skill embeddings...")
        mentee_embs, mentee_meta, _ = generate_skill_entities_with_embeddings(
            mentees_df, MENTEE_AREAS, 'mentee', MENTEE_COLS
        )
        
        print("\n[4/5] Generating aspiration embeddings...")
        mentee_aspirations, mentor_contexts = extract_aspiration_entities(mentees_df, mentors_df)
        
        if len(mentee_aspirations) > 0 and len(mentor_contexts) > 0:
            mentee_asp_prompts = [a['prompt'] for a in mentee_aspirations]
            mentor_ctx_prompts = [c['prompt'] for c in mentor_contexts]
            
            mentee_asp_embs = generate_embeddings_batch(model, mentee_asp_prompts, EMBEDDING_BATCH_SIZE)
            mentor_ctx_embs = generate_embeddings_batch(model, mentor_ctx_prompts, EMBEDDING_BATCH_SIZE)
            
            mentee_asp_meta = create_metadata_dataframe(mentee_aspirations)
            mentor_ctx_meta = create_metadata_dataframe(mentor_contexts)
            
            print(f"  ✅ Aspiration embeddings: {len(mentee_asp_embs)} mentee × {len(mentor_ctx_embs)} mentor")
        else:
            print("  ⚠️  No aspiration data found")
            mentee_asp_embs = np.array([])
            mentor_ctx_embs = np.array([])
            mentee_asp_meta = pd.DataFrame()
            mentor_ctx_meta = pd.DataFrame()
        
        print("\n[5/5] Saving all embeddings...")
        # Skill embeddings
        save_numpy(mentor_embs, 'mentor_embeddings.npy')
        save_numpy(mentee_embs, 'mentee_embeddings.npy')
        save_dataframe(mentor_meta, 'mentor_metadata.pkl')
        save_dataframe(mentee_meta, 'mentee_metadata.pkl')
        
        # Aspiration embeddings
        if len(mentee_asp_embs) > 0:
            save_numpy(mentee_asp_embs, 'mentee_aspiration_embeddings.npy')
            save_numpy(mentor_ctx_embs, 'mentor_context_embeddings.npy')
            save_dataframe(mentee_asp_meta, 'mentee_aspiration_metadata.pkl')
            save_dataframe(mentor_ctx_meta, 'mentor_context_metadata.pkl')
        
        print(f"\n📊 EMBEDDING SUMMARY:")
        print(f"  Skill matching:")
        print(f"    Mentor entities: {len(mentor_embs)} (2 per mentor)")
        print(f"    Mentee entities: {len(mentee_embs)} (2 per mentee)")
        print(f"    Total skill pairs: {len(mentee_embs) * len(mentor_embs):,}")
        
        if len(mentee_asp_embs) > 0:
            print(f"  Aspiration matching:")
            print(f"    Mentee aspirations: {len(mentee_asp_embs)}")
            print(f"    Mentor contexts: {len(mentor_ctx_embs)}")
            print(f"    Total aspiration pairs: {len(mentee_asp_embs) * len(mentor_ctx_embs):,}")
        
        print("\n✅ EMBEDDINGS COMPLETE")
        
    except Exception as e:
        print(f"\n❌ EMBEDDING STAGE FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
