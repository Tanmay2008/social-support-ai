# 6_frontend/streamlit_app.py
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Social Support AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<div class="main-header">🤖 AI-Powered Social Support Assistant</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Go to", ["Application Submission", "Chat Assistant", "Application Status", "Admin Dashboard"])
        
        st.header("System Info")
        st.info("""
        **AI Workflow Features:**
        - Multi-modal data processing
        - Automated eligibility assessment
        - Economic support recommendations
        - Real-time chat assistance
        """)
    
    # Main content based on selected page
    if page == "Application Submission":
        show_application_submission()
    elif page == "Chat Assistant":
        show_chat_assistant()
    elif page == "Application Status":
        show_application_status()
    elif page == "Admin Dashboard":
        show_admin_dashboard()

def show_application_submission():
    st.header("📋 Social Support Application")
    
    with st.form("application_form"):
        st.subheader("Personal Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name*")
            email = st.text_input("Email Address*")
            phone = st.text_input("Phone Number*")
            date_of_birth = st.date_input("Date of Birth*", min_value=datetime(1900, 1, 1))
            
        with col2:
            nationality = st.text_input("Nationality*")
            marital_status = st.selectbox("Marital Status*", ["Single", "Married", "Divorced", "Widowed"])
            family_size = st.number_input("Family Size*", min_value=1, max_value=20, value=1)
            dependents = st.number_input("Number of Dependents*", min_value=0, max_value=10, value=0)
        
        st.subheader("Financial Information")
        
        col3, col4 = st.columns(2)
        
        with col3:
            employment_status = st.selectbox("Employment Status*", 
                ["Employed", "Unemployed", "Self-Employed", "Student", "Retired"])
            monthly_income = st.number_input("Monthly Income (AED)*", min_value=0, value=0)
            income_source = st.text_input("Income Source*")
            
        with col4:
            housing_type = st.selectbox("Housing Type*", 
                ["Rented", "Owned", "Living with Family", "Government Housing"])
            monthly_rent = st.number_input("Monthly Rent (AED)", min_value=0, value=0)
            education_level = st.selectbox("Education Level*",
                ["No Formal Education", "Primary", "Secondary", "Diploma", "Bachelor", "Master", "PhD"])
        
        st.subheader("Supporting Documents")
        
        doc_col1, doc_col2 = st.columns(2)
        
        with doc_col1:
            application_form = st.file_uploader("Application Form (PDF)*", type=['pdf'])
            bank_statement = st.file_uploader("Bank Statement (PDF)*", type=['pdf'])
            emirates_id = st.file_uploader("Emirates ID (Image/PDF)*", type=['jpg', 'png', 'pdf'])
            
        with doc_col2:
            resume = st.file_uploader("Resume/CV (PDF)*", type=['pdf'])
            assets_file = st.file_uploader("Assets & Liabilities (Excel)*", type=['xlsx', 'csv'])
            credit_report = st.file_uploader("Credit Report (PDF)*", type=['pdf'])
        
        submitted = st.form_submit_button("Submit Application")
        
        if submitted:
            if not all([full_name, email, phone, employment_status, monthly_income]):
                st.error("Please fill in all required fields (*)")
            else:
                with st.spinner("🤖 AI Agents are processing your application... This may take 2-3 minutes."):
                    # Prepare application data
                    application_data = {
                        'personal_info': {
                            'full_name': full_name,
                            'email': email,
                            'phone': phone,
                            'date_of_birth': date_of_birth.isoformat(),
                            'nationality': nationality
                        },
                        'family_info': {
                            'marital_status': marital_status,
                            'family_size': family_size,
                            'dependents': dependents
                        },
                        'financial_info': {
                            'employment_status': employment_status,
                            'monthly_income': monthly_income,
                            'income_source': income_source,
                            'housing_type': housing_type,
                            'monthly_rent': monthly_rent
                        },
                        'education_info': {
                            'education_level': education_level
                        }
                    }
                    
                    # Simulate API call (replace with actual API call)
                    time.sleep(2)  # Simulate processing time
                    
                    # Mock response for demo
                    mock_response = {
                        'success': True,
                        'processing_time_seconds': 123.45,
                        'eligibility_score': 0.78,
                        'decision': 'APPROVE for Partial Financial Support',
                        'economic_recommendations': [
                            'Job matching with local retail employers',
                            'Digital skills training program',
                            'Career counseling sessions',
                            'Financial literacy workshop'
                        ],
                        'validation_results': {
                            'address_consistency': {'consistent': True, 'score': 1.0},
                            'income_consistency': {'consistent': True, 'score': 0.9},
                            'overall_consistent': True
                        }
                    }
                    
                    display_application_results(mock_response)

def display_application_results(results):
    """Display application processing results"""
    st.success("🎉 Application Processing Complete!")
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Eligibility Score", f"{results['eligibility_score']:.0%}")
    
    with col2:
        decision_color = "green" if "approve" in results['decision'].lower() else "red"
        st.markdown(f"**Decision:** :{decision_color}[{results['decision']}]")
    
    with col3:
        st.metric("Processing Time", f"{results['processing_time_seconds']:.1f} seconds")
    
    # Validation results
    st.subheader("📊 Data Validation Results")
    validation_df = pd.DataFrame([
        {"Check": "Address Consistency", "Status": "✅ Consistent" if results['validation_results']['address_consistency']['consistent'] else "❌ Inconsistent", "Score": results['validation_results']['address_consistency']['score']},
        {"Check": "Income Consistency", "Status": "✅ Consistent" if results['validation_results']['income_consistency']['consistent'] else "❌ Inconsistent", "Score": results['validation_results']['income_consistency']['score']},
        {"Check": "Overall Consistency", "Status": "✅ Pass" if results['validation_results']['overall_consistent'] else "❌ Fail", "Score": "N/A"}
    ])
    st.dataframe(validation_df, use_container_width=True)
    
    # Economic recommendations
    st.subheader("💡 Economic Support Recommendations")
    for i, recommendation in enumerate(results['economic_recommendations'], 1):
        st.markdown(f"{i}. **{recommendation}**")
    
    # Next steps
    st.info("""
    **Next Steps:**
    - Our team will contact you within 24 hours
    - You can track your application status in the 'Application Status' section
    - Chat with our AI assistant for any questions
    """)

def show_chat_assistant():
    st.header("💬 AI Assistant Chat")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your application or support options..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Simulate AI response generation
            ai_response = generate_ai_response(prompt)
            
            # Simulate stream of response
            for chunk in ai_response.split():
                full_response += chunk + " "
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.05)
            message_placeholder.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})

def generate_ai_response(prompt: str) -> str:
    """Generate AI response based on user prompt"""
    prompt_lower = prompt.lower()
    
    if "status" in prompt_lower:
        return "I can help you check your application status. Please provide your application ID, or you can visit the 'Application Status' section to track all your submissions."
    
    elif "eligibility" in prompt_lower or "qualify" in prompt_lower:
        return "Eligibility for social support is based on multiple factors including income level, family size, employment status, and financial situation. Our AI system assesses all these factors to determine your eligibility score and appropriate support options."
    
    elif "training" in prompt_lower or "upskilling" in prompt_lower:
        return "We offer various economic enablement programs including digital skills training, vocational courses, career counseling, and job matching services. These are designed to help you gain employment or improve your current situation."
    
    elif "document" in prompt_lower:
        return "For social support applications, you typically need: Application form, Emirates ID, Bank statements, Proof of income, Credit report, and Assets/liabilities statement. Our system can process scanned documents and extract information automatically."
    
    else:
        return "I'm here to help with your social support application. I can provide information about eligibility criteria, application status, required documents, economic support programs, and answer any other questions you might have about the process."

def show_application_status():
    st.header("📊 Application Status Tracker")
    
    # Mock data for demonstration
    applications = [
        {"id": "APP1001", "status": "Approved", "submission_date": "2024-01-15", "decision": "Full Support", "score": 0.85},
        {"id": "APP1002", "status": "Processing", "submission_date": "2024-01-18", "decision": "Pending", "score": "N/A"},
        {"id": "APP1003", "status": "Additional Info Required", "submission_date": "2024-01-10", "decision": "Pending", "score": 0.45},
    ]
    
    application_id = st.text_input("Enter Application ID to search:")
    
    if application_id:
        # Filter applications by ID
        filtered_apps = [app for app in applications if app["id"] == application_id]
        
        if filtered_apps:
            app = filtered_apps[0]
            
            st.subheader(f"Application: {app['id']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                status_color = "green" if app["status"] == "Approved" else "orange" if app["status"] == "Processing" else "red"
                st.metric("Status", app["status"])
            with col2:
                st.metric("Submission Date", app["submission_date"])
            with col3:
                if app["score"] != "N/A":
                    st.metric("Eligibility Score", f"{app['score']:.0%}")
            
            # Status timeline
            st.subheader("Timeline")
            timeline_data = [
                {"date": app["submission_date"], "event": "Application Submitted", "status": "completed"},
                {"date": "2024-01-16", "event": "Initial Review", "status": "completed"},
                {"date": "2024-01-17", "event": "AI Processing", "status": "completed" if app["status"] != "Processing" else "current"},
                {"date": "2024-01-18", "event": "Final Decision", "status": "completed" if app["status"] == "Approved" else "pending"}
            ]
            
            for event in timeline_data:
                status_icon = "✅" if event["status"] == "completed" else "🟡" if event["status"] == "current" else "⏳"
                st.write(f"{status_icon} {event['date']} - {event['event']}")
        
        else:
            st.warning(f"No application found with ID: {application_id}")
    
    else:
        # Show all applications table
        st.subheader("Your Applications")
        df = pd.DataFrame(applications)
        st.dataframe(df, use_container_width=True)

def show_admin_dashboard():
    st.header("👨‍💼 Admin Dashboard")
    
    # Mock analytics data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Applications", "1,247")
    with col2:
        st.metric("Approval Rate", "68%")
    with col3:
        st.metric("Avg Processing Time", "2.3 min")
    with col4:
        st.metric("AI Accuracy", "94%")
    
    # Charts and analytics
    col5, col6 = st.columns(2)
    
    with col5:
        st.subheader("Applications by Status")
        status_data = pd.DataFrame({
            'Status': ['Approved', 'Processing', 'Rejected', 'Additional Info'],
            'Count': [450, 287, 210, 300]
        })
        st.bar_chart(status_data.set_index('Status'))
    
    with col6:
        st.subheader("Processing Time Distribution")
        time_data = pd.DataFrame({
            'Time Range': ['<1 min', '1-2 min', '2-3 min', '3-5 min', '>5 min'],
            'Count': [320, 450, 280, 150, 47]
        })
        st.bar_chart(time_data.set_index('Time Range'))
    
    # System monitoring
    st.subheader("🤖 AI Agent Performance")
    agent_performance = pd.DataFrame({
        'Agent': ['Data Extraction', 'Data Validation', 'Eligibility Assessment', 'Decision Recommendation', 'Economic Support'],
        'Success Rate': [96.2, 94.8, 92.1, 89.7, 95.3],
        'Avg Processing Time (s)': [12.3, 8.7, 15.2, 10.1, 7.8]
    })
    st.dataframe(agent_performance, use_container_width=True)

if __name__ == "__main__":
    main()