"""
Diagnostic script to find similarity calculation issues
"""
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

print("="*80)
print("🔍 SIMILARITY DIAGNOSTIC TOOL")
print("="*80)

# Test 1: Check raw embedding similarity
print("\n[TEST 1] Raw Embedding Test")
print("-"*80)

model = SentenceTransformer('all-mpnet-base-v2')

test_cases = [
    ("machine learning", "machine learning"),  # Should be ~1.0
    ("machine learning", "deep learning"),     # Should be ~0.85-0.9
    ("machine learning", "python programming"),  # Should be ~0.65-0.75
    ("machine learning", "building design"),   # Should be ~0.2-0.3
]

print(f"{'Text 1':<30} {'Text 2':<30} {'Similarity':>10}")
print("-"*80)

for text1, text2 in test_cases:
    emb1 = model.encode(text1, normalize_embeddings=True)
    emb2 = model.encode(text2, normalize_embeddings=True)
    
    sim = float(np.dot(emb1, emb2))
    
    print(f"{text1:<30} {text2:<30} {sim:>10.4f}")

# Test 2: Check your actual data
print("\n\n[TEST 2] Your Actual Data Test")
print("-"*80)

try:
    results = pd.read_pickle('output/detailed_similarity_scores.pkl')
    
    print(f"Total pairs: {len(results)}")
    print(f"Non-zero pairs: {(results['similarity_score'] > 0).sum()}")
    
    # Find identical text matches
    identical = results[results['mentee_skill_text'].str.lower().str.strip() == 
                       results['mentor_skill_text'].str.lower().str.strip()]
    
    if len(identical) > 0:
        print(f"\n❌ IDENTICAL TEXT MATCHES (should be ~1.0):")
        print(identical[['mentee_skill_text', 'mentor_skill_text', 
                        'semantic_similarity', 'expertise_multiplier', 
                        'similarity_score']].head(10))
    
    # Show best matches
    print(f"\n✅ TOP 10 MATCHES:")
    top10 = results.nlargest(10, 'similarity_score')
    print(top10[['mentee_name', 'mentee_skill_text', 
                 'mentor_name', 'mentor_skill_text',
                 'semantic_similarity', 'expertise_gap', 
                 'expertise_multiplier', 'stream_bonus',
                 'similarity_score']])
    
    # Show worst non-zero matches
    print(f"\n⚠️  WORST NON-ZERO MATCHES:")
    worst = results[results['similarity_score'] > 0].nsmallest(10, 'similarity_score')
    print(worst[['mentee_skill_text', 'mentor_skill_text',
                'semantic_similarity', 'expertise_multiplier',
                'similarity_score']])
    
except Exception as e:
    print(f"❌ Could not load results: {e}")

# Test 3: Check for text preprocessing issues
print("\n\n[TEST 3] Text Preprocessing Check")
print("-"*80)

try:
    mentee_meta = pd.read_pickle('output/mentee_metadata.pkl')
    mentor_meta = pd.read_pickle('output/mentor_metadata.pkl')
    
    print("Sample mentee skill texts:")
    print(mentee_meta[['person_name', 'skill_text', 'prompt']].head(5))
    
    print("\nSample mentor skill texts:")
    print(mentor_meta[['person_name', 'skill_text', 'prompt']].head(5))
    
except Exception as e:
    print(f"❌ Could not load metadata: {e}")

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE")
print("="*80)
