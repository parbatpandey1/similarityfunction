"""
📊 Stage 6: Excel Dashboard v6.0
✅ 10 sheets including reciprocal top5 + email data
"""
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from utils import *
from config import *


def format_excel_header(worksheet, color='4472C4'):
    """Format Excel header"""
    fill = PatternFill(start_color=color, end_color=color, fill_type='solid')
    font = Font(bold=True, color='FFFFFF')

    for cell in worksheet[1]:
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Auto-width columns
    for column in worksheet.columns:
        max_len = 0
        col_letter = column[0].column_letter

        for cell in column:
            try:
                if len(str(cell.value)) > max_len:
                    max_len = len(str(cell.value))
            except:
                pass

        worksheet.column_dimensions[col_letter].width = min(max_len + 2, 50)


def create_dashboard(dedup_df, assignments_df, recommendations_df,
                     mentor_top_df, rich_df, utilization_df):
    """Create Excel dashboard"""
    print("\n📊 Creating Excel dashboard v6.0...")

    excel_path = OUTPUT_DIR / '🏆_MENTORSHIP_DASHBOARD_v6.xlsx'

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:

        # Sheet 1: Final Assignments
        print("  [1/10] Final assignments...")
        assignment_cols = [
            'mentee_name', 'mentee_skill_text', 'mentor_name', 'mentor_skill_text',
            'skill_score', 'aspiration_score', 'final_similarity_score',
            'expertise_gap', 'semantic_similarity'
        ]
        assignment_cols_exist = [c for c in assignment_cols if c in assignments_df.columns]
        assignments_df[assignment_cols_exist].sort_values(
            'final_similarity_score', ascending=False
        ).to_excel(writer, sheet_name='✅_FINAL_ASSIGNMENTS', index=False)

        # Sheet 2: Top 5 per Mentee (mentee-centric)
        print("  [2/10] Top 5 per mentee...")
        rec_cols = [
            'recommendation_rank', 'mentee_name', 'mentee_skill_text',
            'mentor_name', 'mentor_skill_text',
            'skill_score', 'aspiration_score', 'final_similarity_score'
        ]
        rec_cols_exist = [c for c in rec_cols if c in recommendations_df.columns]
        recommendations_df[rec_cols_exist].to_excel(
            writer, sheet_name='🎓_TOP5_PER_MENTEE', index=False
        )

        # Sheet 3: Top 5 per Mentor (mentor-centric / reciprocal)
        print("  [3/10] Top 5 per mentor (reciprocal)...")
        mentor_rec_cols = [
            'recommendation_rank', 'mentor_name', 'mentor_skill_text',
            'mentee_name', 'mentee_skill_text',
            'skill_score', 'aspiration_score', 'final_similarity_score'
        ]
        mentor_rec_exist = [c for c in mentor_rec_cols if c in mentor_top_df.columns]
        mentor_top_df[mentor_rec_exist].to_excel(
            writer, sheet_name='👨‍🏫_TOP5_PER_MENTOR', index=False
        )

        # Sheet 4: Rich Matched Dataset (for emails)
        print("  [4/10] Rich email dataset...")
        rich_cols = [
            'final_similarity_score', 'match_quality', 'skill_score', 'aspiration_score',
            'mentee_name', 'mentee_email', 'mentee_department',
            'mentee_main_interest', 'mentee_main_level',
            'mentee_additional_interest', 'mentee_additional_level',
            'mentee_aspirations',
            'mentor_name', 'mentor_email',
            'mentor_main_expertise', 'mentor_main_level',
            'mentor_additional_expertise', 'mentor_additional_level',
            'mentor_experience', 'mentor_work_affiliation',
            'mentor_hours_per_week', 'mentor_contact_preference'
        ]
        rich_cols_exist = [c for c in rich_cols if c in rich_df.columns]
        rich_df[rich_cols_exist].to_excel(
            writer, sheet_name='📧_EMAIL_DATA', index=False
        )

        # Sheet 5: Capacity
        print("  [5/10] Capacity utilization...")
        utilization_df.sort_values('assigned', ascending=False).to_excel(
            writer, sheet_name='👥_CAPACITY_STATUS', index=False
        )

        # Sheet 6: Best 100
        print("  [6/10] Best 100 matches...")
        best = dedup_df.nlargest(100, 'final_similarity_score')[assignment_cols_exist]
        best.to_excel(writer, sheet_name='🔥_BEST_100_MATCHES', index=False)

        # Sheet 7: Aspiration Analysis
        print("  [7/10] Aspiration analysis...")
        asp_analysis = dedup_df[dedup_df['final_similarity_score'] > 0].groupby(
            pd.cut(
                dedup_df[dedup_df['final_similarity_score'] > 0]['aspiration_score'],
                bins=[0, 0.3, 0.5, 0.7, 1.0],
                labels=['Low (0-0.3)', 'Fair (0.3-0.5)', 'Good (0.5-0.7)', 'Excellent (0.7-1.0)']
            )
        ).agg({
            'final_similarity_score': ['count', 'mean'],
            'skill_score': 'mean',
            'aspiration_score': 'mean'
        }).round(3).reset_index()
        asp_analysis.columns = ['Aspiration Range', 'Count', 'Avg Final', 'Avg Skill', 'Avg Aspiration']
        asp_analysis.to_excel(writer, sheet_name='🎯_ASPIRATION_ANALYSIS', index=False)

        # Sheet 8: Stream Analysis
        print("  [8/10] Stream analysis...")
        stream = dedup_df[dedup_df['final_similarity_score'] > 0].groupby(
            ['mentee_stream', 'mentor_stream']
        ).agg({
            'final_similarity_score': ['count', 'mean', 'max'],
            'skill_score': 'mean',
            'aspiration_score': 'mean'
        }).round(3).reset_index()
        stream.columns = ['Mentee Stream', 'Mentor Stream', 'Count',
                          'Avg Final', 'Max Final', 'Avg Skill', 'Avg Aspiration']
        stream.sort_values('Avg Final', ascending=False).to_excel(
            writer, sheet_name='🌊_STREAM_ANALYSIS', index=False
        )

        # Sheet 9: Skill Areas
        print("  [9/10] Skill area analysis...")
        skills = dedup_df[dedup_df['final_similarity_score'] > 0].groupby(
            ['mentee_skill_area', 'mentor_skill_area']
        ).agg({
            'final_similarity_score': ['count', 'mean', 'max']
        }).round(3).reset_index()
        skills.columns = ['Mentee Skill', 'Mentor Skill', 'Count', 'Avg', 'Max']
        skills.sort_values('Avg', ascending=False).to_excel(
            writer, sheet_name='🎯_SKILL_AREAS', index=False
        )

        # Sheet 10: Summary
        print("  [10/10] Executive summary...")
        total_mentees = dedup_df['mentee_person_id'].nunique()
        assigned = len(assignments_df)

        summary = pd.DataFrame([
            {'Metric': '📊 SYSTEM VERSION',              'Value': 'v6.0 - Skill + Aspiration Matching'},
            {'Metric': '',                                'Value': ''},
            {'Metric': 'Total Mentees',                  'Value': total_mentees},
            {'Metric': 'Assigned Mentees',               'Value': assigned},
            {'Metric': 'Unassigned',                     'Value': total_mentees - assigned},
            {'Metric': 'Assignment Rate',                'Value': f"{100*assigned/total_mentees:.1f}%"},
            {'Metric': '',                                'Value': ''},
            {'Metric': 'Total Mentors',                  'Value': dedup_df['mentor_person_id'].nunique()},
            {'Metric': 'Active Mentors',                 'Value': int((utilization_df['assigned'] > 0).sum())},
            {'Metric': 'Total Capacity',                 'Value': int(utilization_df['capacity'].sum())},
            {'Metric': 'Capacity Used',                  'Value': int(utilization_df['assigned'].sum())},
            {'Metric': '',                                'Value': ''},
            {'Metric': 'Best Final Score',               'Value': f"{dedup_df['final_similarity_score'].max():.4f}"},
            {'Metric': 'Avg Final Score (assigned)',     'Value': f"{assignments_df['final_similarity_score'].mean():.4f}"},
            {'Metric': 'Avg Skill Score (assigned)',     'Value': f"{assignments_df['skill_score'].mean():.4f}"},
            {'Metric': 'Avg Aspiration Score (assigned)','Value': f"{assignments_df['aspiration_score'].mean():.4f}"},
            {'Metric': '',                                'Value': ''},
            {'Metric': 'Excellent Matches (≥0.75)',      'Value': int((rich_df['match_quality'] == 'Excellent').sum())},
            {'Metric': 'Good Matches (≥0.55)',           'Value': int((rich_df['match_quality'] == 'Good').sum())},
            {'Metric': 'Fair Matches (≥0.40)',           'Value': int((rich_df['match_quality'] == 'Fair').sum())},
            {'Metric': 'Weak Matches (<0.40)',           'Value': int((rich_df['match_quality'] == 'Weak').sum())},
            {'Metric': '',                                'Value': ''},
            {'Metric': '🎯 FORMULA',                     'Value': f'Final = {SKILL_WEIGHT:.0%} Skill + {ASPIRATION_WEIGHT:.0%} Aspiration'},
        ])
        summary.to_excel(writer, sheet_name='📈_SUMMARY', index=False)

    # Apply formatting
    print("  🎨 Formatting...")
    workbook = load_workbook(excel_path)
    for sheet in workbook.sheetnames:
        format_excel_header(workbook[sheet])
    workbook.save(excel_path)

    print(f"  ✅ Dashboard: {excel_path.name}")


def main():
    """Main Excel engine"""
    print("\n" + "="*80)
    print("STAGE 6: EXCEL DASHBOARD v6.0")
    print("="*80)

    try:
        print("\n[1/2] Loading data...")
        dedup_df          = load_from_output('deduplicated_matches.csv')
        assignments_df    = load_from_output('final_assignments.csv')
        recommendations_df = load_from_output('top_n_recommendations.csv')
        mentor_top_df     = load_from_output('top_n_per_mentor.csv')
        rich_df           = load_from_output('rich_matched_dataset.csv')
        utilization_df    = load_from_output('mentor_utilization.csv')

        print("\n[2/2] Creating dashboard...")
        create_dashboard(dedup_df, assignments_df, recommendations_df,
                         mentor_top_df, rich_df, utilization_df)

        print("\n📊 DASHBOARD COMPLETE")
        print("  10 sheets created:")
        print("  1.  ✅_FINAL_ASSIGNMENTS")
        print("  2.  🎓_TOP5_PER_MENTEE         ← mentee-centric top 5")
        print("  3.  👨‍🏫_TOP5_PER_MENTOR         ← mentor-centric top 5 (reciprocal)")
        print("  4.  📧_EMAIL_DATA              ← full profiles for emails (NEW!)")
        print("  5.  👥_CAPACITY_STATUS")
        print("  6.  🔥_BEST_100_MATCHES")
        print("  7.  🎯_ASPIRATION_ANALYSIS")
        print("  8.  🌊_STREAM_ANALYSIS")
        print("  9.  🎯_SKILL_AREAS")
        print("  10. 📈_SUMMARY")

        print("\n✅ EXCEL ENGINE COMPLETE")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
