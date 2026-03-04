"""
🔮 Embedding generation - UPDATED FOR v6.0
✅ Separate embeddings for skills and aspirations
"""
import pandas as pd
import numpy as np
import re
from sentence_transformers import SentenceTransformer
from config import *

def initialize_embedding_model(model_name):
    """Initialize embedding model"""
    print(f"🔮 Loading embedding model: {model_name}...")
    
    try:
        model = SentenceTransformer(model_name)
        dim = model.get_sentence_embedding_dimension()
        print(f"  ✓ Model loaded (dimension: {dim})")
        return model
    except Exception as e:
        print(f"❌ Failed to load {model_name}: {e}")
        print("💡 Trying fallback: all-MiniLM-L6-v2")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("  ✓ Fallback loaded (dimension: 384)")
        return model

def extract_core_skill(text):
    """Extract core skill from aspirational text"""
    text = text.lower().strip()
    
    remove_patterns = [
        r'\bi want to learn\b',
        r'\bi want to become\b',
        r'\bi want to work (in|at|as|with)\b',
        r'\bi want to\b',
        r'\bi would like to\b',
        r'\baiming to\b',
        r'\binterested in\b',
    ]
    
    for pattern in remove_patterns:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    
    remove_fillers = [
        r'\bbasics?\b',
        r'\bfundamentals?\b',
        r'\ban?\s+',
        r'\bthe\s+',
        r'\bat\s+a\b',
    ]
    
    for pattern in remove_fillers:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    
    text = ' '.join(text.split())
    
    return text.strip()

def clean_skill_text(text):
    """Clean and normalize skill text"""
    if pd.isna(text) or text is None:
        return None
    
    text = str(text).strip()
    
    if not text or text.lower() in ['nan', 'none', 'n/a', '']:
        return None
    
    text = extract_core_skill(text)
    
    if not text or len(text) < 2:
        return None
    
    return text

def clean_aspiration_text(text):
    """
    🔥 NEW: Clean aspiration text (keep more context than skills)
    
    "I want to become a software engineer at a top tech company"
    → "software engineer top tech company"
    """
    if pd.isna(text) or text is None:
        return None
    
    text = str(text).strip().lower()
    
    if not text or text in ['nan', 'none', 'n/a', '']:
        return None
    
    # Remove only the most generic phrases
    remove_patterns = [
        r'\bi want to become\b',
        r'\bi want to work (in|at|as)\b',
        r'\bi want to\b',
    ]
    
    for pattern in remove_patterns:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    
    # Keep more context than skill cleaning
    text = ' '.join(text.split())
    
    return text.strip() if text else None

def create_skill_prompt(row, area_name, skill_col, level_col):
    """Create embedding text - clean skill only"""
    skill_text = row.get(skill_col, '')
    
    cleaned = clean_skill_text(skill_text)
    
    if cleaned is None:
        return None
    
    return cleaned

def extract_skill_entities(df, skill_areas, role, col_mapping):
    """Extract skill entities (NOT aspirations)"""
    entities = []
    
    for person_idx, row in df.iterrows():
        for skill_col, level_col, area_name in skill_areas:
            actual_skill_col = col_mapping.get(skill_col, skill_col)
            
            embed_text = create_skill_prompt(row, area_name, actual_skill_col, level_col)
            
            if embed_text:
                name_col = col_mapping.get('name', 'name')
                roll_col = col_mapping.get('roll', 'roll')
                
                entities.append({
                    'person_id': person_idx,
                    'person_name': row.get(name_col, f'{role}_{person_idx}'),
                    'roll_number': row.get(roll_col, ''),
                    'stream': row.get('stream_parsed', 'unknown'),
                    'skill_area': area_name,
                    'skill_text': row.get(actual_skill_col, ''),
                    'expertise_level': row.get(level_col, np.nan),
                    'prompt': embed_text,
                    'capacity': row.get('capacity', 1) if role == 'mentor' else 1
                })
    
    if len(entities) == 0:
        raise ValueError(f"❌ No valid skill entities for {role}s!")
    
    return entities

def extract_aspiration_entities(mentee_df, mentor_df):
    """
    🔥 NEW: Extract aspiration entities for separate matching
    
    Returns:
    - mentee_aspirations: [{person_id, aspiration_text, prompt}, ...]
    - mentor_contexts: [{person_id, context_text, prompt}, ...]
    """
    mentee_aspirations = []
    mentor_contexts = []
    
    # Extract mentee aspirations
    for idx, row in mentee_df.iterrows():
        aspiration = row.get('aspirations', '') if 'aspirations' in mentee_df.columns else row.get(MENTEE_COLS['aspirations'], '')
        
        cleaned = clean_aspiration_text(aspiration)
        
        if cleaned:
            mentee_aspirations.append({
                'person_id': idx,
                'person_name': row.get('name', f'mentee_{idx}') if 'name' in mentee_df.columns else row.get(MENTEE_COLS['name'], f'mentee_{idx}'),
                'aspiration_text': aspiration,
                'prompt': cleaned
            })
    
    # Extract mentor work/experience context
    for idx, row in mentor_df.iterrows():
        context = row.get('aspiration_context', '')
        
        if pd.notna(context) and str(context).strip():
            cleaned = clean_aspiration_text(context)
            
            if cleaned:
                mentor_contexts.append({
                    'person_id': idx,
                    'person_name': row.get('name', f'mentor_{idx}') if 'name' in mentor_df.columns else row.get(MENTOR_COLS['name'], f'mentor_{idx}'),
                    'context_text': context,
                    'prompt': cleaned
                })
    
    print(f"  ✓ Aspiration entities: {len(mentee_aspirations)} mentees, {len(mentor_contexts)} mentors")
    
    return mentee_aspirations, mentor_contexts

def generate_embeddings_batch(model, prompts, batch_size):
    """Generate embeddings with normalization"""
    try:
        embeddings = model.encode(
            prompts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        
        return embeddings
        
    except Exception as e:
        print(f"❌ Error during embedding: {e}")
        raise

def create_metadata_dataframe(entities):
    """Convert entities to metadata DataFrame"""
    metadata = pd.DataFrame(entities)
    if 'skill_id' not in metadata.columns:
        metadata['skill_id'] = range(len(metadata))
    return metadata
