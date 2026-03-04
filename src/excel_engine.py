"""
📊 Stage 6: Excel Dashboard v6.0
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

def create_dashboard(dedup_df, assignments_df, recommendations_df, utilization_df):
    """Create Excel dashboard"""
    print("\n📊 Creating Excel dashboard v6.0...")
    
    excel_path = OUTPUT_DIR / '🏆_MENTORSHIP_DASHBOARD_v6.xlsx'
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Sheet 1: Assignments
        print("  [1/8] Final assignments...")
        assignment_cols = ['mentee_name', 'mentee_skill_text', 'mentor_name', 'mentor_skill_text',
                          'skill_score', 'aspiration_score', 'final_similarity_score', 
                          'expertise_gap', 'semantic_similarity']
        assignments_df[assignment_cols].sort_values('final_similarity_score', ascending=False).to_excel(
            writer, sheet_name='✅_FINAL_ASSIGNMENTS', index=False
        )
        
        # Sheet 2: Top 5
        print("  [2/8] Top 5 recommendations...")
        rec_cols = ['recommendation_rank', 'mentee_name', 'mentee_skill_text', 'mentor_name', 
                   'mentor_skill_text', 'skill_score', 'aspiration_score', 'final_similarity_score']
        recommendations_df[rec_cols].to_excel(writer, sheet_name='🏆_TOP_5_PER_MENTEE', index=False)
        
        # Sheet 3: Capacity
        print("  [3/8] Capacity utilization...")
        utilization_df.sort_values('assigned', ascending=False).to_excel(
            writer, sheet_name='👥_CAPACITY_STATUS', index=False
        )
        
        # Sheet 4: Best 100
        print("  [4/8] Best 100 matches...")
        best = dedup_df.nlargest(100, 'final_similarity_score')[assignment_cols]
        best.to_excel(writer, sheet_name='🔥_BEST_100_MATCHES', index=False)
        
        # Sheet 5: Aspiration Analysis (NEW!)
        print("  [5/8] Aspiration analysis...")
        asp_analysis = dedup_df[dedup_df['final_similarity_score'] > 0].groupby(
            pd.cut(dedup_df[dedup_df['final_similarity_score'] > 0]['aspiration_score'], 
                   bins=[0, 0.3, 0.5, 0.7, 1.0], 
                   labels=['Low (0-0.3)', 'Fair (0.3-0.5)', 'Good (0.5-0.7)', 'Excellent (0.7-1.0)'])
        ).agg({
            'final_similarity_score': ['count', 'mean'],
            'skill_score': 'mean',
            'aspiration_score': 'mean'
        }).round(3).reset_index()
        asp_analysis.columns = ['Aspiration Range', 'Count', 'Avg Final', 'Avg Skill', 'Avg Aspiration']
        asp_analysis.to_excel(writer, sheet_name='🎯_ASPIRATION_ANALYSIS', index=False)
        
        # Sheet 6: Stream Analysis
        print("  [6/8] Stream analysis...")
        stream = dedup_df[dedup_df['final_similarity_score'] > 0].groupby(['mentee_stream', 'mentor_stream']).agg({
            'final_similarity_score': ['count', 'mean', 'max'],
            'skill_score': 'mean',
            'aspiration_score': 'mean'
        }).round(3).reset_index()
        stream.columns = ['Mentee Stream', 'Mentor Stream', 'Count', 'Avg Final', 'Max Final', 'Avg Skill', 'Avg Aspiration']
        stream.sort_values('Avg Final', ascending=False).to_excel(
            writer, sheet_name='🌊_STREAM_ANALYSIS', index=False
        )
        
        # Sheet 7: Skill Areas
        print("  [7/8] Skill area analysis...")
        skills = dedup_df[dedup_df['final_similarity_score'] > 0].groupby(['mentee_skill_area', 'mentor_skill_area']).agg({
            'final_similarity_score': ['count', 'mean', 'max']
        }).round(3).reset_index()
        skills.columns = ['Mentee Skill', 'Mentor Skill', 'Count', 'Avg', 'Max']
        skills.sort_values('Avg', ascending=False).to_excel(
            writer, sheet_name='🎯_SKILL_AREAS', index=False
        )
        
        # Sheet 8: Summary
        print("  [8/8] Executive summary...")
        total_mentees = dedup_df['mentee_person_id'].nunique()
        assigned = len(assignments_df)
        
        summary = pd.DataFrame([
            {'Metric': '📊 SYSTEM VERSION', 'Value': 'v6.0 - Skill + Aspiration Matching'},
            {'Metric': '', 'Value': ''},
            {'Metric': 'Total Mentees', 'Value': total_mentees},
            {'Metric': 'Assigned Mentees', 'Value': assigned},
            {'Metric': 'Unassigned', 'Value': total_mentees - assigned},
            {'Metric': 'Assignment Rate', 'Value': f"{100*assigned/total_mentees:.1f}%"},
            {'Metric': '', 'Value': ''},
            {'Metric': 'Total Mentors', 'Value': dedup_df['mentor_person_id'].nunique()},
            {'Metric': 'Active Mentors', 'Value': (utilization_df['assigned'] > 0).sum()},
            {'Metric': 'Total Capacity', 'Value': int(utilization_df['capacity'].sum())},
            {'Metric': 'Capacity Used', 'Value': int(utilization_df['assigned'].sum())},
            {'Metric': '', 'Value': ''},
            {'Metric': 'Best Final Score', 'Value': f"{dedup_df['final_similarity_score'].max():.4f}"},
            {'Metric': 'Avg Final Score (assigned)', 'Value': f"{assignments_df['final_similarity_score'].mean():.4f}"},
            {'Metric': 'Avg Skill Score (assigned)', 'Value': f"{assignments_df['skill_score'].mean():.4f}"},
            {'Metric': 'Avg Aspiration Score (assigned)', 'Value': f"{assignments_df['aspiration_score'].mean():.4f}"},
            {'Metric': '', 'Value': ''},
            {'Metric': '🎯 FORMULA', 'Value': f'Final = {SKILL_WEIGHT:.0%} Skill + {ASPIRATION_WEIGHT:.0%} Aspiration'},
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
        dedup_df = load_from_output('deduplicated_matches.csv')
        assignments_df = load_from_output('final_assignments.csv')
        recommendations_df = load_from_output('top_n_recommendations.csv')
        utilization_df = load_from_output('mentor_utilization.csv')
        
        print("\n[2/2] Creating dashboard...")
        create_dashboard(dedup_df, assignments_df, recommendations_df, utilization_df)
        
        print("\n📊 DASHBOARD COMPLETE")
        print("  8 sheets created:")
        print("  1. ✅_FINAL_ASSIGNMENTS")
        print("  2. 🏆_TOP_5_PER_MENTEE")
        print("  3. 👥_CAPACITY_STATUS")
        print("  4. 🔥_BEST_100_MATCHES")
        print("  5. 🎯_ASPIRATION_ANALYSIS (NEW!)")
        print("  6. 🌊_STREAM_ANALYSIS")
        print("  7. 🎯_SKILL_AREAS")
        print("  8. 📈_SUMMARY")
        
        print("\n✅ EXCEL ENGINE COMPLETE")
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
