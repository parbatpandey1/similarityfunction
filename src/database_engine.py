"""
🗄️ Stage 5: SQLite Database v6.0
"""
import sqlite3
import pandas as pd
from utils import *
from config import *

def create_database_connection():
    """Create SQLite database"""
    db_path = OUTPUT_DIR / 'mentorship_matches_v6.db'
    conn = sqlite3.connect(db_path)
    print(f"🗄️  Database: {db_path}")
    return conn

def create_all_tables(conn, dedup_df, assignments_df, recommendations_df):
    """Create all database tables"""
    print("\n📊 Creating tables...")
    
    # Table 1: All matches (deduplicated)
    dedup_df.to_sql('all_matches', conn, if_exists='replace', index=False)
    print("  ✓ 'all_matches' table")
    
    # Table 2: Final assignments
    assignments_df.to_sql('assignments', conn, if_exists='replace', index=False)
    print("  ✓ 'assignments' table")
    
    # Table 3: Top N recommendations
    recommendations_df.to_sql('recommendations', conn, if_exists='replace', index=False)
    print("  ✓ 'recommendations' table")

def create_indexes(conn):
    """Create performance indexes"""
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_mentee ON all_matches(mentee_person_id)',
        'CREATE INDEX IF NOT EXISTS idx_mentor ON all_matches(mentor_person_id)',
        'CREATE INDEX IF NOT EXISTS idx_final_score ON all_matches(final_similarity_score DESC)',
        'CREATE INDEX IF NOT EXISTS idx_skill_score ON all_matches(skill_score DESC)',
        'CREATE INDEX IF NOT EXISTS idx_asp_score ON all_matches(aspiration_score DESC)',
        'CREATE INDEX IF NOT EXISTS idx_assign ON assignments(mentee_person_id)',
        'CREATE INDEX IF NOT EXISTS idx_rec_rank ON recommendations(recommendation_rank)'
    ]
    
    for idx in indexes:
        conn.execute(idx)
    
    print("  ✓ Created 7 indexes")

def generate_sql_queries():
    """Generate useful SQL queries"""
    queries = {
        'top5_per_mentee': """
-- 🏆 TOP 5 RECOMMENDATIONS PER MENTEE (v6.0 with aspiration scores)
SELECT 
    recommendation_rank as rank,
    mentee_name,
    mentee_skill_text,
    mentor_name,
    mentor_skill_text,
    ROUND(skill_score, 4) as skill,
    ROUND(aspiration_score, 4) as aspiration,
    ROUND(final_similarity_score, 4) as final_score,
    ROUND(expertise_gap, 2) as gap
FROM recommendations
WHERE recommendation_rank <= 5
ORDER BY mentee_name, recommendation_rank;
""",
        
        'final_assignments': """
-- ✅ FINAL ASSIGNMENTS (Capacity-Constrained)
SELECT 
    mentee_name,
    mentee_skill_text,
    mentor_name,
    mentor_skill_text,
    ROUND(skill_score, 4) as skill,
    ROUND(aspiration_score, 4) as aspiration,
    ROUND(final_similarity_score, 4) as final_score,
    ROUND(expertise_gap, 2) as gap
FROM assignments
ORDER BY final_similarity_score DESC;
""",
        
        'best_100': """
-- 🔥 BEST 100 MATCHES (v6.0)
SELECT 
    mentee_name,
    mentee_skill_text,
    mentor_name,
    mentor_skill_text,
    ROUND(final_similarity_score, 4) as final_score,
    ROUND(skill_score, 4) as skill,
    ROUND(aspiration_score, 4) as aspiration,
    ROUND(semantic_similarity, 4) as semantic,
    ROUND(expertise_gap, 2) as gap
FROM all_matches
ORDER BY final_similarity_score DESC
LIMIT 100;
""",
        
        'mentor_workload': """
-- 👥 MENTOR WORKLOAD
SELECT 
    mentor_name,
    mentor_capacity,
    COUNT(*) as assigned,
    ROUND(AVG(final_similarity_score), 4) as avg_score,
    ROUND(AVG(skill_score), 4) as avg_skill,
    ROUND(AVG(aspiration_score), 4) as avg_aspiration
FROM assignments
GROUP BY mentor_name, mentor_capacity
ORDER BY assigned DESC;
""",

        'aspiration_analysis': """
-- 🎯 ASPIRATION MATCHING ANALYSIS (NEW!)
SELECT 
    CASE 
        WHEN aspiration_score >= 0.7 THEN 'Excellent (≥0.7)'
        WHEN aspiration_score >= 0.5 THEN 'Good (≥0.5)'
        WHEN aspiration_score >= 0.3 THEN 'Fair (≥0.3)'
        WHEN aspiration_score > 0 THEN 'Poor (>0)'
        ELSE 'No Match'
    END as aspiration_match_quality,
    COUNT(*) as count,
    ROUND(AVG(final_similarity_score), 4) as avg_final_score
FROM all_matches
WHERE final_similarity_score > 0
GROUP BY aspiration_match_quality
ORDER BY MIN(aspiration_score) DESC;
""",

        'skill_vs_aspiration': """
-- 📊 SKILL VS ASPIRATION CONTRIBUTION
SELECT 
    mentee_name,
    mentor_name,
    ROUND(skill_score, 4) as skill,
    ROUND(aspiration_score, 4) as aspiration,
    ROUND(final_similarity_score, 4) as final,
    CASE 
        WHEN skill_score > aspiration_score THEN 'Skill-driven'
        WHEN aspiration_score > skill_score THEN 'Aspiration-driven'
        ELSE 'Balanced'
    END as match_type
FROM assignments
ORDER BY final_similarity_score DESC
LIMIT 20;
"""
    }
    
    return queries

def save_sql_file(queries):
    """Save queries to file"""
    sql_file = OUTPUT_DIR / 'mentorship_queries_v6.sql'
    
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write("-- MENTORSHIP MATCHING SYSTEM v6.0 - SQL QUERIES\n")
        f.write("-- NEW: Includes aspiration matching analysis\n\n")
        
        for name, query in queries.items():
            f.write(f"-- {name.upper()}\n")
            f.write(query)
            f.write("\n\n" + "="*80 + "\n\n")
    
    print(f"  ✓ Saved: {sql_file.name}")

def main():
    """Main database engine"""
    print("\n" + "="*80)
    print("STAGE 5: SQL DATABASE v6.0")
    print("="*80)
    
    try:
        print("\n[1/4] Loading data...")
        dedup_df = load_from_output('deduplicated_matches.csv')
        assignments_df = load_from_output('final_assignments.csv')
        recommendations_df = load_from_output('top_n_recommendations.csv')
        
        print("\n[2/4] Creating database...")
        conn = create_database_connection()
        
        create_all_tables(conn, dedup_df, assignments_df, recommendations_df)
        create_indexes(conn)
        
        print("\n[3/4] Generating queries...")
        queries = generate_sql_queries()
        save_sql_file(queries)
        
        print("\n[4/4] Preview...")
        preview = pd.read_sql_query("""
            SELECT mentee_name, mentor_name, 
                   ROUND(skill_score, 3) as skill,
                   ROUND(aspiration_score, 3) as aspiration,
                   ROUND(final_similarity_score, 3) as final
            FROM assignments 
            ORDER BY final_similarity_score DESC 
            LIMIT 5
        """, conn)
        
        print("\n🎯 TOP 5 ASSIGNMENTS:")
        print(preview.to_string(index=False))
        
        conn.close()
        
        print("\n✅ DATABASE ENGINE COMPLETE")
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
