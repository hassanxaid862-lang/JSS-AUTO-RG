"""
JSS Pro Suite - Multi-User Edition
Academic Assessment Management System with Cloud Database
Features: User authentication, per-user data isolation, cloud storage
"""

import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
from PIL import Image
import plotly.express as px
import os
import datetime
from auth import is_user_logged_in, show_auth_page, logout_user, get_current_user
from cloud_db import (
    get_firebase_db, init_user_database, get_learners, save_to_cloud_db,
    update_learner_marks, delete_learner, get_user_settings, 
    update_user_settings, get_grades, export_grade_data
)

# ==========================================
# CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="JSS Pro Suite - Multi-User",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styling
st.markdown("""
    <style>
    .main-header { color: #003366; font-weight: bold; }
    .success-box { background-color: #d4edda; padding: 10px; border-radius: 5px; }
    .warning-box { background-color: #fff3cd; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = is_user_logged_in()

# ==========================================
# PDF REPORT GENERATOR
# ==========================================

class CBC_Report_PDF(FPDF):
    """Enhanced CBC Report PDF Generator with multi-user support"""
    
    def header(self):
        logo_bytes = st.session_state.get('school_logo_bytes')
        school = st.session_state.get('school_name', 'My School')
        motto = st.session_state.get('school_motto', 'Excellence in Education')
        addr = st.session_state.get('school_address', 'School Address')
        term = st.session_state.get('term_info', 'Term 1, 2026')
        
        # Draw Logo and Watermark
        if logo_bytes:
            if not hasattr(self, 'logo_path'):
                import tempfile
                img = Image.open(io.BytesIO(logo_bytes))
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    img.save(tmp, format='PNG')
                    self.logo_path = tmp.name
            self.image(self.logo_path, 10, 8, 22)
            self.set_alpha(0.05)
            self.image(self.logo_path, 50, 110, 110)
            self.set_alpha(1)
            self.set_x(35)
        
        # School Details
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, school.upper(), 0, 1, 'L' if logo_bytes else 'C')
        self.set_font('helvetica', 'I', 8)
        if logo_bytes: self.set_x(35)
        self.cell(0, 5, motto, 0, 1, 'L' if logo_bytes else 'C')
        self.set_font('helvetica', '', 8)
        if logo_bytes: self.set_x(35)
        self.cell(0, 5, addr, 0, 1, 'L' if logo_bytes else 'C')
        
        self.ln(4)
        self.set_draw_color(0, 51, 102)
        self.line(10, 36, 200, 36)
        
        self.set_font('helvetica', 'B', 11)
        self.cell(0, 10, f"ACADEMIC ASSESSMENT REPORT: {term}", 0, 1, 'C')
    
    def footer(self):
        self.set_font('helvetica', 'I', 8)
        self.set_y(-15)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, 'C')

def get_grading_logic(score):
    """CBC grading criteria"""
    if score >= 80: return "Exceeding Expectations", "Exceptional performance."
    if score >= 60: return "Meeting Expectations", "Good work, maintain pace."
    if score >= 40: return "Approaching Expectations", "Room for improvement."
    return "Below Expectations", "Urgent intervention required."

# ==========================================
# AUTHENTICATION GATE
# ==========================================

if not st.session_state.logged_in:
    show_auth_page()
else:
    # User is logged in - show main app
    current_user = get_current_user()
    user_id = current_user['user_id']
    user_email = current_user['email']
    
    # Initialize user database
    init_user_database(user_id)
    
    # Get or load user settings
    if 'user_settings' not in st.session_state:
        st.session_state.user_settings = get_user_settings(user_id)
    
    # Standard Subjects
    subjects = [
        "Mathematics", "English", "Kiswahili", "Integrated Science", 
        "Social Studies", "Agriculture", "Pre-technical", 
        "Religious Education", "Creative Arts & Sports"
    ]
    
    # ==========================================
    # SIDEBAR CONFIGURATION
    # ==========================================
    
    with st.sidebar:
        st.markdown("### 📚 JSS Pro Suite")
        st.caption(f"👤 Logged in as: {user_email}")
        
        # Grade selection
        grades = get_grades(user_id)
        if grades:
            active_grade = st.selectbox("Active Grade Database", grades)
        else:
            active_grade = st.selectbox("Active Grade Database", 
                                        ["Grade 6", "Grade 7", "Grade 8", "Grade 9"])
        
        if st.button("+ Create New Grade", use_container_width=True):
            st.info("Upload data for a new grade using the Data Entry tab")
        
        st.divider()
        
        # Logout
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚪 Logout", use_container_width=True):
                logout_user()
        with col2:
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state.show_settings = True
        
        st.divider()
        st.header("🎨 School Branding")
        
        # Logo upload
        uploaded_logo = st.file_uploader("Upload School Logo", type=['png', 'jpg', 'jpeg'])
        if uploaded_logo:
            st.session_state.school_logo_bytes = uploaded_logo.read()
            st.session_state.user_settings['has_logo'] = True
            st.success("Logo uploaded!")
        
        # School info
        st.session_state.school_name = st.text_input(
            "School Name",
            value=st.session_state.user_settings.get('school_name', 'My School')
        )
        st.session_state.school_motto = st.text_input(
            "School Motto",
            value=st.session_state.user_settings.get('school_motto', 'Excellence in Education')
        )
        st.session_state.school_address = st.text_area(
            "School Address",
            value=st.session_state.user_settings.get('school_address', 'Your Address')
        )
        
        st.header("🗓️ Academic Dates")
        st.session_state.term_info = st.text_input(
            "Term",
            value=st.session_state.user_settings.get('term_info', 'Term 1, 2026')
        )
        st.session_state.closing_date = st.text_input(
            "Closing Date",
            value=st.session_state.user_settings.get('closing_date', '')
        )
        st.session_state.opening_date = st.text_input(
            "Opening Date",
            value=st.session_state.user_settings.get('opening_date', '')
        )
        
        # Save settings button
        if st.button("💾 Save Settings", use_container_width=True):
            settings = {
                'school_name': st.session_state.school_name,
                'school_motto': st.session_state.school_motto,
                'school_address': st.session_state.school_address,
                'term_info': st.session_state.term_info,
                'closing_date': st.session_state.closing_date,
                'opening_date': st.session_state.opening_date
            }
            success, msg = update_user_settings(user_id, settings)
            if success:
                st.success("Settings saved!")
                st.session_state.user_settings = settings
            else:
                st.error(msg)
        
        st.divider()
        with st.expander("ℹ️ About This System"):
            st.write("**JSS Pro Suite v2.0**")
            st.write("Multi-user Academic Assessment System")
            st.write("---")
            st.write("**Developer:** Hassan Xaidi")
            st.write("**Email:** hassanxaidi862@gmail.com")
            st.write("**Phone:** +254794551087")
            st.caption("Cloud-based education management platform")
    
    # ==========================================
    # MAIN CONTENT AREA
    # ==========================================
    
    st.markdown(f"# 📊 Academic Assessment - {active_grade}")
    
    # Get learners data
    learners = get_learners(user_id, active_grade)
    
    # Create tabs
    t1, t2, t3, t4, t5 = st.tabs([
        "📝 DATA ENTRY",
        "📋 MANAGER",
        "📊 ANALYTICS",
        "📄 REPORTS",
        "🧹 CLEANUP"
    ])
    
    # ===== TAB 1: DATA ENTRY =====
    with t1:
        st.subheader("Data Ingestion Methods")
        
        col1, col2 = st.columns([1, 1])
        
        # Bulk Excel Upload
        with col1:
            st.markdown("### 📤 Bulk Excel Upload")
            up_file = st.file_uploader(
                "Upload CBC spreadsheet",
                type=['xlsx', 'csv'],
                key="bulk_upload"
            )
            if up_file and st.button("Save to Cloud DB", key="bulk_save"):
                with st.spinner("Uploading and processing..."):
                    df_entry = pd.read_excel(up_file) if "xlsx" in up_file.name else pd.read_csv(up_file)
                    success, message = save_to_cloud_db(df_entry, active_grade, user_id)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        # Manual Entry
        with col2:
            st.markdown("### ✏️ Manual Score Entry")
            with st.form("manual_entry_form"):
                m_name = st.text_input("Learner Name")
                m_no = st.text_input("Assessment Number")
                
                cols = st.columns(3)
                m_marks = {}
                for idx, sub in enumerate(subjects):
                    m_marks[sub] = cols[idx % 3].number_input(
                        sub,
                        min_value=0.0,
                        max_value=100.0,
                        step=0.5
                    )
                
                if st.form_submit_button("Save Entry", use_container_width=True):
                    if m_name and m_no:
                        df_entry = pd.DataFrame([{
                            "Learner's Name": m_name,
                            "Grade": active_grade,
                            "Assessment Number": m_no,
                            **m_marks
                        }])
                        success, message = save_to_cloud_db(df_entry, active_grade, user_id)
                        if success:
                            st.success("Entry saved!")
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please enter learner name and assessment number")
    
    # ===== TAB 2: DATA MANAGER =====
    with t2:
        st.subheader(f"Learners in {active_grade}")
        
        if learners:
            # Convert to DataFrame for display
            display_data = []
            for learner in learners:
                row = {
                    "Name": learner['name'],
                    "Assessment No.": learner['assmt_no'],
                    "Grade": learner['grade']
                }
                row.update(learner['marks'])
                display_data.append(row)
            
            df_display = pd.DataFrame(display_data)
            st.dataframe(df_display, use_container_width=True)
            
            # Edit/Delete options
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Edit Learner Marks")
                selected_learner = st.selectbox(
                    "Select learner",
                    [f"{l['name']} ({l['assmt_no']})" for l in learners]
                )
                
                if selected_learner:
                    learner_name = selected_learner.split(' (')[0]
                    selected = next((l for l in learners if l['name'] == learner_name), None)
                    
                    if selected:
                        with st.form("edit_marks_form"):
                            new_marks = {}
                            for subject in subjects:
                                new_marks[subject] = st.number_input(
                                    subject,
                                    value=float(selected['marks'].get(subject, 0)),
                                    min_value=0.0,
                                    max_value=100.0
                                )
                            
                            if st.form_submit_button("Update Marks"):
                                learner_id = f"{selected['assmt_no']}_{selected['grade']}"
                                success, msg = update_learner_marks(user_id, learner_id, new_marks)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
            
            with col2:
                st.subheader("Delete Learner")
                delete_learner_name = st.selectbox(
                    "Select learner to delete",
                    [f"{l['name']} ({l['assmt_no']})" for l in learners],
                    key="delete_select"
                )
                
                with st.form("delete_learner_form"):
                    st.warning("⚠️ This action cannot be undone!")
                    delete_confirm = st.checkbox("Yes, I want to delete this learner")
                    delete_btn = st.form_submit_button("🗑️ Delete Learner", use_container_width=True)
                
                if delete_btn:
                    if delete_confirm:
                        learner_name = delete_learner_name.split(' (')[0]
                        selected = next((l for l in learners if l['name'] == learner_name), None)
                        
                        if selected:
                            learner_id = f"{selected['assmt_no']}_{selected['grade']}"
                            success, msg = delete_learner(user_id, learner_id)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.error("Please confirm deletion before proceeding")
        else:
            st.info("No learners in this grade yet. Upload data in the Data Entry tab.")
    
    # ===== TAB 3: ANALYTICS =====
    with t3:
        if learners:
            st.subheader(f"Performance Analytics - {active_grade}")
            
            # Calculate subject averages
            all_marks = {}
            for learner in learners:
                for subject, score in learner['marks'].items():
                    if subject not in all_marks:
                        all_marks[subject] = []
                    all_marks[subject].append(float(score))
            
            subject_avgs = {
                subject: sum(scores) / len(scores)
                for subject, scores in all_marks.items()
            }
            
            # Charts
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Bar chart
                df_chart = pd.DataFrame([
                    {"Subject": k, "Average Score": v}
                    for k, v in subject_avgs.items()
                ])
                fig = px.bar(
                    df_chart,
                    x="Subject",
                    y="Average Score",
                    color="Average Score",
                    title=f"Subject Averages - {active_grade}",
                    color_continuous_scale="RdYlGn"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.metric("Total Learners", len(learners))
                st.metric("Average Score", f"{sum(subject_avgs.values()) / len(subject_avgs):.1f}%")
                st.metric("Highest Average", f"{max(subject_avgs.values()):.1f}%")
        else:
            st.info("No data to analyze yet")
    
    # ===== TAB 4: REPORTS =====
    with t4:
        if learners:
            st.subheader(f"Report Generation - {active_grade}")
            
            # Prepare data
            stats = []
            for idx, learner in enumerate(learners, 1):
                mean_score = sum(learner['marks'].values()) / len(learner['marks']) if learner['marks'] else 0
                stats.append({
                    'name': learner['name'],
                    'assmt_no': learner['assmt_no'],
                    'grade': learner['grade'],
                    'score': mean_score,
                    'learner_data': learner
                })
            
            # Rank learners
            stats.sort(key=lambda x: x['score'], reverse=True)
            for idx, stat in enumerate(stats, 1):
                stat['rank'] = idx
            
            total_students = len(stats)
            
            # Generate PDF on button click
            if st.button("📄 Generate PDF Reports", use_container_width=True):
                with st.spinner("Generating PDF reports..."):
                    pdf_bundle = CBC_Report_PDF()
                    
                    for student_stat in stats:
                        pdf_bundle.add_page()
                        
                        # Student header
                        pdf_bundle.set_fill_color(0, 51, 102)
                        pdf_bundle.set_text_color(255, 255, 255)
                        pdf_bundle.set_font('helvetica', 'B', 10)
                        pdf_bundle.cell(95, 10, f" NAME: {student_stat['name'].upper()}", 1, 0, 'L', True)
                        pdf_bundle.cell(45, 10, f" GRADE: {student_stat['grade']}", 1, 0, 'L', True)
                        pdf_bundle.cell(50, 10, f" NO: {student_stat['assmt_no']}", 1, 1, 'L', True)
                        
                        # Performance table
                        pdf_bundle.set_text_color(0, 0, 0)
                        pdf_bundle.ln(4)
                        pdf_bundle.set_font('helvetica', 'B', 8)
                        pdf_bundle.cell(60, 7, " LEARNING AREA", 1)
                        pdf_bundle.cell(15, 7, "SCORE", 1, 0, 'C')
                        pdf_bundle.cell(55, 7, " PERFORMANCE LEVEL", 1)
                        pdf_bundle.cell(60, 7, " REMARKS", 1, 1)
                        
                        # Subject rows
                        pdf_bundle.set_font('helvetica', '', 8)
                        for subject, score in student_stat['learner_data']['marks'].items():
                            level, remark = get_grading_logic(score)
                            pdf_bundle.cell(60, 7, f" {subject}", 1)
                            pdf_bundle.cell(15, 7, str(int(score)), 1, 0, 'C')
                            pdf_bundle.cell(55, 7, f" {level}", 1)
                            pdf_bundle.cell(60, 7, f" {remark}", 1, 1)
                        
                        # Summary
                        pdf_bundle.ln(5)
                        pdf_bundle.set_font('helvetica', 'B', 10)
                        pdf_bundle.cell(
                            0, 10,
                            f"MEAN SCORE: {student_stat['score']:.2f}%  |  RANK: {student_stat['rank']} OUT OF {total_students}",
                            0, 1
                        )
                        
                        # Signatures
                        pdf_bundle.ln(8)
                        pdf_bundle.set_font('helvetica', 'B', 9)
                        pdf_bundle.cell(0, 6, "CLASS TEACHER'S REMARKS:", 0, 1)
                        pdf_bundle.set_font('helvetica', '', 9)
                        pdf_bundle.cell(0, 8, "." * 115, 0, 1)
                        pdf_bundle.cell(100, 10, "Signature: .......................................", 0, 0)
                        pdf_bundle.cell(0, 10, "Date: .........................", 0, 1)
                        
                        pdf_bundle.ln(4)
                        pdf_bundle.set_font('helvetica', 'B', 9)
                        pdf_bundle.cell(0, 6, "PRINCIPAL'S REMARKS:", 0, 1)
                        pdf_bundle.set_font('helvetica', '', 9)
                        pdf_bundle.cell(0, 8, "." * 115, 0, 1)
                        pdf_bundle.cell(100, 10, "Signature & Stamp: ............................", 0, 0)
                        pdf_bundle.cell(0, 10, "Date: .........................", 0, 1)
                    
                    # Download button
                    pdf_bytes = pdf_bundle.output(dest='S').encode('latin1')
                    st.download_button(
                        "⬇️ Download Reports",
                        pdf_bytes,
                        f"CBC_Reports_{active_grade}_{st.session_state.term_info.replace(', ', '_')}.pdf",
                        "application/pdf",
                        use_container_width=True
                    )
                    
                    if hasattr(pdf_bundle, 'logo_path'):
                        os.unlink(pdf_bundle.logo_path)
        else:
            st.info("No data to generate reports")
    
    # ===== TAB 5: CLEANUP =====
    with t5:
        st.subheader("Database Maintenance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Delete Single Learner")
            if learners:
                delete_option = st.selectbox(
                    "Select learner to delete",
                    [f"{l['name']} ({l['assmt_no']})" for l in learners],
                    key="cleanup_delete"
                )
                
                if st.button("🗑️ Delete", key="cleanup_btn", use_container_width=True):
                    learner_name = delete_option.split(' (')[0]
                    selected = next((l for l in learners if l['name'] == learner_name), None)
                    
                    if selected:
                        learner_id = f"{selected['assmt_no']}_{selected['grade']}"
                        success, msg = delete_learner(user_id, learner_id)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            else:
                st.info("No learners to delete")
        
        with col2:
            st.markdown("#### Export Grade Data")
            if st.button("📥 Export as CSV", use_container_width=True):
                df_export = export_grade_data(user_id, active_grade)
                if not df_export.empty:
                    csv = df_export.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        f"{active_grade}_data.csv",
                        "text/csv"
                    )
                else:
                    st.warning("No data to export")
        
        st.divider()
        st.warning("⚠️ Dangerous Operations")
        
        with st.form("clear_grade_form"):
            st.error(f"This will permanently delete all learners in {active_grade}")
            clear_confirm = st.checkbox(f"Yes, I understand. Delete all data for {active_grade}.")
            clear_btn = st.form_submit_button("🔥 Clear All Data", use_container_width=True)
        
        if clear_btn:
            if clear_confirm:
                learners_to_delete = get_learners(user_id, active_grade)
                for learner in learners_to_delete:
                    learner_id = f"{learner['assmt_no']}_{learner['grade']}"
                    delete_learner(user_id, learner_id)
                
                st.success(f"All data for {active_grade} has been deleted")
                st.rerun()
            else:
                st.error("Please confirm before clearing all data")

# ==========================================
# HELPER COMPONENTS
# ==========================================

st.sidebar.divider()
st.sidebar.markdown("🔒 Data is encrypted and securely stored in the cloud")
