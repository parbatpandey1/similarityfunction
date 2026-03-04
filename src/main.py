"""
🚀 MENTORSHIP MATCHING SYSTEM v6.0 - PRODUCTION LAUNCHER
CORRECTED DATA STRUCTURE:
✅ Mentee: main_interest + additional_interest (both with levels)
✅ Aspirations matched separately with mentor work/experience
✅ Final score = 80% skill + 20% aspiration
✅ Reciprocal Top 5: mentee-centric + mentor-centric views
✅ Rich matched dataset for personalized email generation
"""
import sys
import time
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))


def check_prerequisites():
    """Check input files"""
    from config import MENTOR_FILE, MENTEE_FILE
    
    missing = []
    if not MENTOR_FILE.exists():
        missing.append(str(MENTOR_FILE))
    if not MENTEE_FILE.exists():
        missing.append(str(MENTEE_FILE))
    
    if missing:
        print("❌ MISSING INPUT FILES:")
        for f in missing:
            print(f"  • {f}")
        return False
    
    print("✅ Input files found")
    return True


def run_pipeline():
    """Execute complete pipeline"""
    start = time.time()
    
    print("🚀" + "="*78 + "🚀")
    print("   MENTORSHIP MATCHING SYSTEM v6.0 - CORRECTED STRUCTURE")
    print()
    print("   🔥 MAJOR CHANGES:")
    print("   ✅ Mentee: main_interest + additional_interest (2 skills)")
    print("   ✅ Mentor: main_expertise + additional_expertise (2 skills)")
    print("   ✅ Aspirations: future goals ↔ mentor work/experience")
    print("   ✅ Final score: 80% skill + 20% aspiration")
    print()
    print("   🆕 NEW IN THIS VERSION:")
    print("   ✅ Reciprocal Top 5: mentee-centric + mentor-centric views")
    print("   ✅ Rich matched dataset: full profiles for email generation")
    print()
    print("   📊 ENTITY STRUCTURE:")
    print("   • Skills:      2×2 = 4 entity matches per person pair")
    print("   • Aspirations: 1×1 = 1 aspiration match per person pair")
    print("🚀" + "="*78 + "🚀\n")
    
    if not check_prerequisites():
        return False
    
    stages = [
        ('preprocessor',       '📊 Preprocessing'),
        ('embedder',           '🔮 Embeddings'),
        ('similarity_engine',  '⚡ Similarity'),
        ('matching_algorithm', '🎯 Matching + Reciprocal + Rich Dataset'),
        ('database_engine',    '🗄️  Database'),
        ('excel_engine',       '📊 Excel Dashboard'),
    ]
    
    success = 0
    
    for module_name, stage_name in stages:
        print(f"\n{'='*80}")
        print(f"🎯 STAGE {success + 1}/{len(stages)}: {stage_name}")
        print(f"{'='*80}")
        
        try:
            module = __import__(module_name)
            module.main()
            success += 1
            print(f"✅ {stage_name} SUCCESS")
            
        except ImportError as e:
            print(f"❌ IMPORT ERROR: {e}")
            print(f"💡 Ensure {module_name}.py exists in src/")
            break
            
        except Exception as e:
            print(f"❌ RUNTIME ERROR: {e}")
            import traceback
            traceback.print_exc()
            break
    
    elapsed = time.time() - start
    
    print("\n" + "🎉"*40)
    if success == len(stages):
        print("✅ COMPLETE SUCCESS!")
    else:
        print(f"⚠️  PARTIAL ({success}/{len(stages)} stages)")
    print(f"⏱️  Time: {elapsed:.1f}s")
    print("🎉"*40)
    
    if success >= 4:
        print("\n📁 OUTPUT FILES (./output/):")
        print("   🏆 🏆_MENTORSHIP_DASHBOARD_v6.xlsx   ← MAIN RESULT")
        print("      └─ ✅_FINAL_ASSIGNMENTS")
        print("      └─ 🎓_TOP5_PER_MENTEE             ← mentee-centric top 5")
        print("      └─ 👨‍🏫_TOP5_PER_MENTOR             ← mentor-centric top 5 (reciprocal)")
        print("      └─ 📧_EMAIL_DATA                  ← full profiles for emails")
        print("      └─ 📊_CAPACITY_STATUS")
        print("      └─ 🔬_BEST_100_MATCHES")
        print("      └─ 📋_SUMMARY")
        print()
        print("   📄 final_assignments.csv")
        print("   📄 top5_per_mentee.csv               ← mentee-centric top 5")
        print("   📄 top5_per_mentor.csv               ← mentor-centric top 5")
        print("   📄 rich_matched_dataset.csv          ← USE THIS FOR EMAILS")
        print("   🗄️  mentorship_matches_v6.db")
        print("   📋 mentorship_queries_v6.sql")
        
        print("\n🔥 QUICK START:")
        print("   1. Open 🏆_MENTORSHIP_DASHBOARD_v6.xlsx")
        print("   2. ✅_FINAL_ASSIGNMENTS  → confirmed 1-to-1 matches")
        print("   3. 🎓_TOP5_PER_MENTEE   → each mentee's best 5 mentors")
        print("   4. 👨‍🏫_TOP5_PER_MENTOR   → each mentor's best 5 mentees")
        print("   5. 📧_EMAIL_DATA        → all info needed to write emails")
        
        print("\n📊 SCORING BREAKDOWN:")
        print("   • final_score   = 0.80 × skill_score + 0.20 × aspiration_score")
        print("   • skill_score   = (semantic^1.2 × expertise_multiplier) + stream_bonus")
        print("   • aspiration    = cosine(mentee_aspiration ↔ mentor work/experience)")
        print("   • match_quality : Excellent(≥0.75) | Good(≥0.55) | Fair(≥0.40) | Weak")
    
    return success == len(stages)


if __name__ == "__main__":
    import os
    print(f"📂 Working directory: {os.getcwd()}\n")
    
    success = run_pipeline()
    
    if success:
        print("\n🎊 Production ready!")
    else:
        print("\n💥 Pipeline failed.")
        sys.exit(1)
