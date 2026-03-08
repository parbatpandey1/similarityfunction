"""
🗄️ Stage 5: SQLite Database v6.0
✅ 6 tables including email_ready_data with matched skill pair
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


def build_email_ready_table(rich_df):
    """
    Focused email-ready table.
    Includes exact matched skill pair + full profiles.
    Direct input for email_generator.py.
    """
    email_cols = [
        # Match metadata
        'final_similarity_score', 'match_quality',
        'skill_score', 'aspiration_score',

        # ✅ Exact matched skill pair
        'mentee_skill_area',    'mentee_skill_text',
        'mentor_skill_area',    'mentor_skill_text',

        # Mentee full profile
        'mentee_name', 'mentee_email', 'mentee_roll',
        'mentee_department', 'mentee_stream',
        'mentee_main_interest',       'mentee_main_level',
        'mentee_additional_interest', 'mentee_additional_level',
        'mentee_aspirations',

        # Mentor full profile
        'mentor_name', 'mentor_email', 'mentor_roll',
        'mentor_stream',
        'mentor_main_expertise',       'mentor_main_level',
        'mentor_additional_expertise', 'mentor_additional_level',
        'mentor_experience', 'mentor_work_affiliation',
        'mentor_hours_per_week', 'mentor_contact_preference',
    ]
    cols_exist = [c for c in email_cols if c in rich_df.columns]
    email_df   = rich_df[cols_exist].copy()
    email_df   = email_df.sort_values(
        'final_similarity_score', ascending=False
    ).reset_index(drop=True)
    return email_df


def create_all_tables(conn, dedup_df, assignments_df,
                      recommendations_df, mentor_top_df,
                      rich_df, email_df):
    """Create all database tables"""
    print("\n📊 Creating tables...")

    dedup_df.to_sql('all_matches', conn, if_exists='replace', index=False)
    print("  ✓ 'all_matches' table")

    assignments_df.to_sql('assignments', conn, if_exists='replace', index=False)
    print("  ✓ 'assignments' table")

    recommendations_df.to_sql('recommendations', conn, if_exists='replace', index=False)
    print("  ✓ 'recommendations' table  (mentee-centric top 5)")

    mentor_top_df.to_sql('recommendations_per_mentor', conn, if_exists='replace', index=False)
    print("  ✓ 'recommendations_per_mentor' table  (mentor-centric top 5)")

    rich_df.to_sql('rich_matched_dataset', conn, if_exists='replace', index=False)
    print("  ✓ 'rich_matched_dataset' table  (full profiles)")

    email_df.to_sql('email_ready_data', conn, if_exists='replace', index=False)
    print("  ✓ 'email_ready_data' table  (focused + matched pair for emails)")


def create_indexes(conn):
    """Create performance indexes"""
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_mentee          ON all_matches(mentee_person_id)',
        'CREATE INDEX IF NOT EXISTS idx_mentor          ON all_matches(mentor_person_id)',
        'CREATE INDEX IF NOT EXISTS idx_final_score     ON all_matches(final_similarity_score DESC)',
        'CREATE INDEX IF NOT EXISTS idx_skill_score     ON all_matches(skill_score DESC)',
        'CREATE INDEX IF NOT EXISTS idx_asp_score       ON all_matches(aspiration_score DESC)',
        'CREATE INDEX IF NOT EXISTS idx_assign          ON assignments(mentee_person_id)',
        'CREATE INDEX IF NOT EXISTS idx_rec_rank        ON recommendations(recommendation_rank)',
        'CREATE INDEX IF NOT EXISTS idx_rec_mentor      ON recommendations_per_mentor(mentor_person_id)',
        'CREATE INDEX IF NOT EXISTS idx_rich_mentee     ON rich_matched_dataset(mentee_email)',
        'CREATE INDEX IF NOT EXISTS idx_rich_mentor     ON rich_matched_dataset(mentor_email)',
        'CREATE INDEX IF NOT EXISTS idx_email_mentee    ON email_ready_data(mentee_email)',
        'CREATE INDEX IF NOT EXISTS idx_email_mentor    ON email_ready_data(mentor_email)',
        'CREATE INDEX IF NOT EXISTS idx_email_quality   ON email_ready_data(match_quality)',
    ]
    for idx in indexes:
        conn.execute(idx)
    print(f"  ✓ Created {len(indexes)} indexes")


def generate_sql_queries():
    """Generate useful SQL queries"""
    queries = {
        'top5_per_mentee': """
-- 🏆 TOP 5 RECOMMENDATIONS PER MENTEE
SELECT
    recommendation_rank                  as rank,
    mentee_name, mentee_skill_text,
    mentor_name, mentor_skill_text,
    ROUND(skill_score, 4)                as skill,
    ROUND(aspiration_score, 4)           as aspiration,
    ROUND(final_similarity_score, 4)     as final_score,
    ROUND(expertise_gap, 2)              as gap
FROM recommendations
WHERE recommendation_rank <= 5
ORDER BY mentee_name, recommendation_rank;
""",
        'top5_per_mentor': """
-- 👨‍🏫 TOP 5 RECOMMENDATIONS PER MENTOR (reciprocal)
SELECT
    recommendation_rank                  as rank,
    mentor_name, mentor_skill_text,
    mentee_name, mentee_skill_text,
    ROUND(skill_score, 4)                as skill,
    ROUND(aspiration_score, 4)           as aspiration,
    ROUND(final_similarity_score, 4)     as final_score
FROM recommendations_per_mentor
WHERE recommendation_rank <= 5
ORDER BY mentor_name, recommendation_rank;
""",
        'email_mentee_view': """
-- 📧 EMAIL DATA - MENTEE SIDE
SELECT
    mentee_name, mentee_email,
    mentee_skill_area, mentee_skill_text,
    mentor_skill_area, mentor_skill_text,
    mentee_main_interest, mentee_additional_interest,
    mentee_aspirations, mentee_department,
    mentor_name, mentor_email,
    mentor_main_expertise, mentor_additional_expertise,
    mentor_work_affiliation, mentor_experience,
    mentor_contact_preference, mentor_hours_per_week,
    match_quality,
    ROUND(final_similarity_score, 4)     as match_score
FROM email_ready_data
ORDER BY mentee_name;
""",
        'email_mentor_view': """
-- 📧 EMAIL DATA - MENTOR SIDE
SELECT
    mentor_name, mentor_email,
    mentor_skill_area, mentor_skill_text,
    mentee_skill_area, mentee_skill_text,
    mentor_main_expertise, mentor_additional_expertise,
    mentor_work_affiliation,
    mentee_name, mentee_email,
    mentee_main_interest, mentee_additional_interest,
    mentee_aspirations, mentee_department,
    match_quality,
    ROUND(final_similarity_score, 4)     as match_score
FROM email_ready_data
ORDER BY mentor_name;
""",
        'email_by_quality': """
-- 📧 EXCELLENT + GOOD MATCHES ONLY (safe to send)
SELECT
    match_quality,
    mentee_skill_text, mentor_skill_text,
    mentee_name, mentor_name,
    mentee_email, mentor_email,
    mentee_aspirations, mentor_work_affiliation,
    ROUND(final_similarity_score, 4)     as match_score
FROM email_ready_data
WHERE match_quality IN ('Excellent', 'Good')
ORDER BY final_similarity_score DESC;
""",
        'final_assignments': """
-- ✅ FINAL ASSIGNMENTS
SELECT
    mentee_name, mentor_name, match_quality,
    mentee_skill_text, mentor_skill_text,
    ROUND(skill_score, 4)                as skill,
    ROUND(aspiration_score, 4)           as aspiration,
    ROUND(final_similarity_score, 4)     as final_score
FROM rich_matched_dataset
ORDER BY final_similarity_score DESC;
""",
        'mentor_workload': """
-- 👥 MENTOR WORKLOAD
SELECT
    mentor_name, mentor_main_expertise,
    COUNT(*)                                  as assigned_mentees,
    ROUND(AVG(final_similarity_score), 4)     as avg_score
FROM email_ready_data
GROUP BY mentor_name
ORDER BY assigned_mentees DESC;
""",
        'aspiration_analysis': """
-- 🎯 ASPIRATION MATCHING ANALYSIS
SELECT
    CASE
        WHEN aspiration_score >= 0.7 THEN 'Excellent (>=0.7)'
        WHEN aspiration_score >= 0.5 THEN 'Good (>=0.5)'
        WHEN aspiration_score >= 0.3 THEN 'Fair (>=0.3)'
        WHEN aspiration_score >  0   THEN 'Poor (>0)'
        ELSE 'No Match'
    END                                       as aspiration_quality,
    COUNT(*)                                  as count,
    ROUND(AVG(final_similarity_score), 4)     as avg_final_score
FROM all_matches
WHERE final_similarity_score > 0
GROUP BY aspiration_quality
ORDER BY MIN(aspiration_score) DESC;
""",
        'skill_vs_aspiration': """
-- 📊 SKILL VS ASPIRATION CONTRIBUTION
SELECT
    mentee_name, mentor_name,
    ROUND(skill_score, 4)                as skill,
    ROUND(aspiration_score, 4)           as aspiration,
    ROUND(final_similarity_score, 4)     as final,
    CASE
        WHEN skill_score > aspiration_score THEN 'Skill-driven'
        WHEN aspiration_score > skill_score THEN 'Aspiration-driven'
        ELSE 'Balanced'
    END                                  as match_type
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
        f.write("-- VectorBridge | Includes matched pair + email data\n\n")
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
        dedup_df           = load_from_output('deduplicated_matches.csv')
        assignments_df     = load_from_output('final_assignments.csv')
        recommendations_df = load_from_output('top_n_recommendations.csv')
        mentor_top_df      = load_from_output('top_n_per_mentor.csv')
        rich_df            = load_from_output('rich_matched_dataset.csv')

        email_df = build_email_ready_table(rich_df)
        print(f"  ✓ Email-ready table: {len(email_df)} rows × {len(email_df.columns)} cols")

        print("\n[2/4] Creating database...")
        conn = create_database_connection()
        create_all_tables(conn, dedup_df, assignments_df,
                          recommendations_df, mentor_top_df,
                          rich_df, email_df)
        create_indexes(conn)

        print("\n[3/4] Generating queries...")
        queries = generate_sql_queries()
        save_sql_file(queries)

        print("\n[4/4] Preview...")
        preview = pd.read_sql_query("""
            SELECT mentee_name, mentor_name, match_quality,
                   mentee_skill_text, mentor_skill_text,
                   ROUND(final_similarity_score, 3) as final
            FROM email_ready_data
            ORDER BY final_similarity_score DESC
            LIMIT 5
        """, conn)

        print("\n🎯 TOP 5 MATCHES (email view):")
        print(preview.to_string(index=False))

        conn.close()

        print("\n✅ DATABASE ENGINE COMPLETE")
        print("  6 tables created:")
        print("  1. all_matches")
        print("  2. assignments")
        print("  3. recommendations              ← mentee-centric top 5")
        print("  4. recommendations_per_mentor   ← mentor-centric top 5")
        print("  5. rich_matched_dataset         ← full profiles")
        print("  6. email_ready_data             ← matched pair + profiles for emails ✨")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
