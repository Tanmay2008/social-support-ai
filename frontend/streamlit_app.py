# 6_frontend/streamlit_app.py
import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import os
from typing import Dict, List, Any

# Page configuration
st.set_page_config(
    page_title="Social Support AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2e86ab;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .success-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 10px 0;
    }
    .warning-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        margin: 10px 0;
    }
    .error-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 10px 0;
    }
    .info-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 10px 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .agent-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .chat-message {
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        max-width: 80%;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: auto;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: auto;
    }
</style>
""", unsafe_allow_html=True)

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def init_session_state():
    """Initialize session state variables"""
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'current_application_id' not in st.session_state:
        st.session_state.current_application_id = None
    if 'application_results' not in st.session_state:
        st.session_state.application_results = {}
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False

def call_api(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Make API calls with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error {response.status_code}: {response.text}"}
            
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to API server. Please make sure the server is running."}
    except Exception as e:
        return {"error": f"API call failed: {str(e)}"}

def main():
    """Main application function"""
    init_session_state()
    
    # Header
    st.markdown('<div class="main-header">🤖 AI-Powered Social Support Assistant</div>', unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/1f77b4/ffffff?text=GovAI", use_column_width=True)
        
        st.markdown("### Navigation")
        page = st.radio(
            "Go to",
            ["Application Submission", "Chat Assistant", "Application Status", "Admin Dashboard"],
            key="navigation"
        )
        
        st.markdown("---")
        st.markdown("### System Info")
        
        # System status
        status = call_api("/health")
        if "error" not in status:
            st.success("🟢 System Operational")
            st.caption(f"Version: {status.get('version', 'Unknown')}")
        else:
            st.error("🔴 System Offline")
            st.caption("API server not available")
        
        st.markdown("---")
        st.markdown("### Quick Actions")
        
        if st.button("🔄 Check System Status"):
            status = call_api("/status")
            if "error" not in status:
                st.success("System is healthy")
            else:
                st.error("System check failed")
        
        if st.button("📊 View Statistics"):
            st.session_state.navigation = "Admin Dashboard"
        
        st.markdown("---")
        st.markdown("#### About")
        st.caption("""
        This AI-powered system automates social support applications 
        using multi-modal data processing and machine learning.
        
        **Features:**
        • Automated document processing
        • AI-powered eligibility assessment
        • Economic support recommendations
        • Real-time chat assistance
        """)

    # Page routing
    if page == "Application Submission":
        show_application_submission()
    elif page == "Chat Assistant":
        show_chat_assistant()
    elif page == "Application Status":
        show_application_status()
    elif page == "Admin Dashboard":
        show_admin_dashboard()

def show_application_submission():
    """Show application submission form"""
    st.markdown('<div class="sub-header">📋 Social Support Application</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ Application Guidelines", expanded=True):
        st.markdown("""
        **Before you apply, please ensure you have:**
        - Valid Emirates ID
        - Recent bank statements (last 3 months)
        - Proof of income documents
        - Resume/CV (for employment assessment)
        - Assets and liabilities statement
        
        **Processing Time:** 2-3 minutes using AI automation
        **Support Types:** Financial aid, housing support, training programs, job matching
        """)
    
    # Application form
    with st.form("application_form", clear_on_submit=True):
        st.markdown("### Personal Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name*", placeholder="Enter your full name")
            email = st.text_input("Email Address*", placeholder="your.email@example.com")
            phone = st.text_input("Phone Number*", placeholder="+971 XX XXX XXXX")
            date_of_birth = st.date_input("Date of Birth*", min_value=datetime(1900, 1, 1))
            
        with col2:
            nationality = st.text_input("Nationality*", placeholder="Your nationality")
            marital_status = st.selectbox("Marital Status*", ["", "Single", "Married", "Divorced", "Widowed"])
            family_size = st.number_input("Family Size*", min_value=1, max_value=20, value=1, help="Total family members living together")
            dependents = st.number_input("Number of Dependents*", min_value=0, max_value=10, value=0, help="Children or other dependents")
        
        st.markdown("### Financial Information")
        
        col3, col4 = st.columns(2)
        
        with col3:
            employment_status = st.selectbox("Employment Status*", 
                ["", "Employed", "Unemployed", "Self-Employed", "Student", "Retired"])
            monthly_income = st.number_input("Monthly Income (AED)*", min_value=0, value=0, step=500, 
                                           help="Total monthly income from all sources")
            income_source = st.text_input("Income Source*", placeholder="Salary, Business, Investments, etc.")
            
        with col4:
            housing_type = st.selectbox("Housing Type*", 
                ["", "Rented", "Owned", "Living with Family", "Government Housing"])
            monthly_rent = st.number_input("Monthly Rent (AED)", min_value=0, value=0, step=100,
                                         help="Leave as 0 if not applicable")
            education_level = st.selectbox("Education Level*",
                ["", "No Formal Education", "Primary", "Secondary", "Diploma", "Bachelor", "Master", "PhD"])
        
        st.markdown("### Supporting Documents")
        st.caption("Upload digital copies of your documents. Supported formats: PDF, JPG, PNG, Excel")
        
        doc_col1, doc_col2 = st.columns(2)
        
        with doc_col1:
            application_form = st.file_uploader("Application Form (PDF)*", type=['pdf'], 
                                              help="Download template from our website")
            bank_statement = st.file_uploader("Bank Statement (PDF)*", type=['pdf'],
                                            help="Last 3 months of statements")
            emirates_id = st.file_uploader("Emirates ID (Image/PDF)*", type=['jpg', 'jpeg', 'png', 'pdf'])
            
        with doc_col2:
            resume = st.file_uploader("Resume/CV (PDF)*", type=['pdf'],
                                    help="For employment and skills assessment")
            assets_file = st.file_uploader("Assets & Liabilities (Excel)*", type=['xlsx', 'xls', 'csv'],
                                         help="Download template from our website")
            credit_report = st.file_uploader("Credit Report (PDF)", type=['pdf'],
                                           help="Optional but recommended")
        
        st.markdown("### Additional Information")
        emergency_contact = st.text_input("Emergency Contact Name", placeholder="Name of emergency contact")
        emergency_phone = st.text_input("Emergency Contact Phone", placeholder="Emergency contact phone number")
        
        support_type = st.selectbox("Primary Support Requested",
            ["Financial Aid", "Housing Support", "Education Support", "Healthcare Support", "Employment Support"])
        
        # Terms and conditions
        st.markdown("---")
        agree_terms = st.checkbox("I hereby declare that the information provided is true and accurate to the best of my knowledge.*")
        agree_privacy = st.checkbox("I agree to the processing of my personal data for the purpose of social support assessment.*")
        
        submitted = st.form_submit_button("🚀 Submit Application", use_container_width=True)
        
        if submitted:
            if not all([full_name, email, phone, employment_status, monthly_income, agree_terms, agree_privacy]):
                st.error("Please fill in all required fields (*) and accept the terms and conditions.")
            else:
                # Prepare application data
                application_data = {
                    'full_name': full_name,
                    'email': email,
                    'phone': phone,
                    'date_of_birth': date_of_birth.isoformat(),
                    'nationality': nationality,
                    'marital_status': marital_status,
                    'family_size': family_size,
                    'dependents': dependents,
                    'employment_status': employment_status,
                    'monthly_income': monthly_income,
                    'income_source': income_source,
                    'housing_type': housing_type,
                    'monthly_rent': monthly_rent,
                    'education_level': education_level,
                    'emergency_contact': emergency_contact,
                    'emergency_phone': emergency_phone,
                    'support_type_requested': support_type
                }
                
                # Show processing
                with st.spinner("🤖 AI Agents are processing your application... This may take 2-3 minutes."):
                    # Simulate API call (replace with actual API call)
                    time.sleep(2)
                    
                    # Generate mock response for demo
                    mock_response = _generate_mock_application_response(application_data)
                    
                    # Store results
                    app_id = mock_response['application_id']
                    st.session_state.current_application_id = app_id
                    st.session_state.application_results[app_id] = mock_response
                    
                    # Display results
                    display_application_results(mock_response)

def display_application_results(results: Dict):
    """Display application processing results"""
    st.markdown("---")
    st.markdown("## 🎉 Application Processing Complete!")
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score = results['eligibility_score']
        st.markdown(f'<div class="metric-card"><h3>Eligibility Score</h3><h2 style="color: #1f77b4;">{score:.0%}</h2></div>', 
                   unsafe_allow_html=True)
    
    with col2:
        decision = results['decision']['decision']
        color = "green" if "APPROVE" in decision else "orange" if "PENDING" in decision else "red"
        st.markdown(f'<div class="metric-card"><h3>Decision</h3><h2 style="color: {color};">{decision}</h2></div>', 
                   unsafe_allow_html=True)
    
    with col3:
        processing_time = results['processing_time_seconds']
        st.markdown(f'<div class="metric-card"><h3>Processing Time</h3><h2 style="color: #2e86ab;">{processing_time:.1f}s</h2></div>', 
                   unsafe_allow_html=True)
    
    with col4:
        confidence = results['decision']['confidence']
        st.markdown(f'<div class="metric-card"><h3>Confidence</h3><h2 style="color: #ff7f0e;">{confidence}</h2></div>', 
                   unsafe_allow_html=True)
    
    # Decision details
    st.markdown("### 📊 Assessment Details")
    
    col5, col6 = st.columns(2)
    
    with col5:
        st.markdown("#### Validation Results")
        validation_df = pd.DataFrame([
            {"Check": "Identity Verification", "Status": "✅ Pass", "Score": 0.95},
            {"Check": "Income Consistency", "Status": "✅ Pass", "Score": 0.88},
            {"Check": "Document Completeness", "Status": "✅ Pass", "Score": 0.92},
            {"Check": "Data Quality", "Status": "✅ Pass", "Score": 0.90}
        ])
        st.dataframe(validation_df, use_container_width=True, hide_index=True)
    
    with col6:
        st.markdown("#### Eligibility Factors")
        factors_df = pd.DataFrame([
            {"Factor": "Income Level", "Score": 0.85, "Impact": "High"},
            {"Factor": "Family Situation", "Score": 0.78, "Impact": "High"},
            {"Factor": "Employment Status", "Score": 0.65, "Impact": "Medium"},
            {"Factor": "Assets & Liabilities", "Score": 0.72, "Impact": "Medium"}
        ])
        st.dataframe(factors_df, use_container_width=True, hide_index=True)
    
    # Economic recommendations
    st.markdown("### 💡 Economic Support Recommendations")
    
    recommendations = results.get('economic_recommendations', [])
    for i, rec in enumerate(recommendations[:5], 1):
        with st.container():
            col7, col8 = st.columns([3, 1])
            with col7:
                st.markdown(f"**{i}. {rec.get('title', 'Recommendation')}**")
                st.caption(rec.get('description', ''))
            with col8:
                st.metric("Priority", rec.get('priority_score', 'N/A'))
    
    # Next steps
    st.markdown("### 📝 Next Steps")
    
    if "APPROVE" in results['decision']['decision']:
        st.success("""
        **Your application has been approved! Next steps:**
        1. Our team will contact you within 24 hours to discuss your support package
        2. Complete the orientation session
        3. Meet with your assigned case manager
        4. Begin receiving support services
        """)
    elif "PENDING" in results['decision']['decision']:
        st.warning("""
        **Your application requires additional review:**
        1. Our team will contact you for additional information
        2. You may need to provide supplementary documents
        3. A case officer will conduct a follow-up interview
        4. Final decision will be communicated within 3-5 business days
        """)
    else:
        st.info("""
        **Next steps for declined applications:**
        1. Review the decision details and eligibility criteria
        2. Consider submitting an appeal with additional information
        3. Explore alternative support programs
        4. Contact our support team for guidance
        """)
    
    # Action buttons
    col9, col10, col11 = st.columns(3)
    
    with col9:
        if st.button("💬 Chat about Results", use_container_width=True):
            st.session_state.navigation = "Chat Assistant"
            st.session_state.chat_context = {
                'application_id': results['application_id'],
                'decision': results['decision']
            }
    
    with col10:
        if st.button("📋 View Detailed Report", use_container_width=True):
            st.session_state.navigation = "Application Status"
    
    with col11:
        if st.button("🔄 Submit Another Application", use_container_width=True):
            st.session_state.current_application_id = None

def show_chat_assistant():
    """Show AI chat assistant interface"""
    st.markdown('<div class="sub-header">💬 AI Assistant Chat</div>', unsafe_allow_html=True)
    
    # Chat configuration
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### Ask me anything about social support applications")
    
    with col2:
        if st.button("🔄 Clear Chat", use_container_width=True):
            st.session_state.chat_messages = []
    
    # Application context
    if st.session_state.current_application_id:
        st.info(f"💡 Chat context: Application {st.session_state.current_application_id}")
    
    # Chat container
    chat_container = st.container()
    
    # Display chat messages
    with chat_container:
        for message in st.session_state.chat_messages:
            if message['type'] == 'user':
                st.markdown(
                    f'<div class="chat-message user-message">'
                    f'<strong>You:</strong><br>{message["content"]}'
                    f'</div>', 
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="chat-message assistant-message">'
                    f'<strong>AI Assistant:</strong><br>{message["content"]}'
                    f'</div>', 
                    unsafe_allow_html=True
                )
                
                # Show suggestions if available
                if message.get('suggestions'):
                    st.markdown("**Suggested questions:**")
                    cols = st.columns(2)
                    for i, suggestion in enumerate(message['suggestions'][:4]):
                        with cols[i % 2]:
                            if st.button(suggestion, key=f"sugg_{i}", use_container_width=True):
                                # Add suggestion as user message
                                st.session_state.chat_messages.append({
                                    'type': 'user',
                                    'content': suggestion,
                                    'timestamp': datetime.now().isoformat()
                                })
                                st.rerun()
    
    # Chat input
    st.markdown("---")
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message
        st.session_state.chat_messages.append({
            'type': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })
        
        # Generate AI response
        with st.spinner("🤖 AI Assistant is thinking..."):
            # Simulate API call (replace with actual API call)
            time.sleep(1)
            
            # Generate mock response
            ai_response = _generate_mock_chat_response(user_input)
            
            # Add AI response
            st.session_state.chat_messages.append({
                'type': 'assistant',
                'content': ai_response['response'],
                'suggestions': ai_response.get('suggestions', []),
                'timestamp': datetime.now().isoformat()
            })
            
            st.rerun()

def show_application_status():
    """Show application status tracking"""
    st.markdown('<div class="sub-header">📊 Application Status Tracker</div>', unsafe_allow_html=True)
    
    # Search section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        application_id = st.text_input("Enter Application ID", 
                                      placeholder="e.g., APP123456789",
                                      value=st.session_state.current_application_id or "")
    
    with col2:
        st.markdown("")
        st.markdown("")
        search_clicked = st.button("🔍 Search Application", use_container_width=True)
    
    if search_clicked and application_id:
        with st.spinner("Searching for application..."):
            # Simulate API call
            time.sleep(1)
            
            # Check if we have mock data for this ID
            if application_id in st.session_state.application_results:
                results = st.session_state.application_results[application_id]
                display_application_status_details(application_id, results)
            else:
                # Generate mock status
                mock_status = _generate_mock_application_status(application_id)
                display_application_status_details(application_id, mock_status)
    
    elif st.session_state.current_application_id:
        # Show current application status
        app_id = st.session_state.current_application_id
        results = st.session_state.application_results[app_id]
        display_application_status_details(app_id, results)
    
    else:
        # Show recent applications (mock data)
        st.markdown("### Recent Applications")
        recent_apps = _generate_mock_recent_applications()
        
        for app in recent_apps:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{app['application_id']}**")
                    st.caption(f"Submitted: {app['submission_date']}")
                
                with col2:
                    score_color = "green" if app['eligibility_score'] > 0.7 else "orange" if app['eligibility_score'] > 0.4 else "red"
                    st.markdown(f"<span style='color: {score_color}; font-weight: bold;'>{app['eligibility_score']:.0%}</span>", 
                               unsafe_allow_html=True)
                
                with col3:
                    st.write(app['status'])
                
                with col4:
                    if st.button("View", key=app['application_id']):
                        st.session_state.current_application_id = app['application_id']
                        st.rerun()
                
                st.markdown("---")

def display_application_status_details(application_id: str, results: Dict):
    """Display detailed application status"""
    st.markdown(f"### Application: `{application_id}`")
    
    # Status overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = results.get('status', 'processed')
        status_color = "green" if status == 'processed' else "blue" if status == 'processing' else "red"
        st.metric("Current Status", status.title(), delta=None)
    
    with col2:
        st.metric("Eligibility Score", f"{results.get('eligibility_score', 0):.0%}")
    
    with col3:
        processing_time = results.get('processing_time_seconds', 0)
        st.metric("Processing Time", f"{processing_time:.1f}s")
    
    # Timeline
    st.markdown("#### 📅 Processing Timeline")
    
    timeline_data = [
        {"stage": "Application Submitted", "status": "completed", "timestamp": "2024-01-15 10:30:00"},
        {"stage": "Document Processing", "status": "completed", "timestamp": "2024-01-15 10:31:15"},
        {"stage": "Data Validation", "status": "completed", "timestamp": "2024-01-15 10:32:45"},
        {"stage": "Eligibility Assessment", "status": "completed", "timestamp": "2024-01-15 10:33:30"},
        {"stage": "Decision Recommendation", "status": "completed", "timestamp": "2024-01-15 10:34:10"},
        {"stage": "Final Review", "status": "current", "timestamp": "2024-01-15 10:34:50"}
    ]
    
    for step in timeline_data:
        icon = "✅" if step['status'] == 'completed' else "🟡" if step['status'] == 'current' else "⏳"
        st.write(f"{icon} **{step['stage']}** - {step['timestamp']}")
    
    # Agent performance
    st.markdown("#### 🤖 AI Agent Performance")
    
    agent_data = [
        {"agent": "Data Extraction", "status": "completed", "confidence": 0.95, "duration": "12.3s"},
        {"agent": "Data Validation", "status": "completed", "confidence": 0.88, "duration": "8.7s"},
        {"agent": "Eligibility Assessment", "status": "completed", "confidence": 0.92, "duration": "15.2s"},
        {"agent": "Decision Recommendation", "status": "completed", "confidence": 0.85, "duration": "10.1s"}
    ]
    
    for agent in agent_data:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.write(f"**{agent['agent']}**")
        with col2:
            st.write(agent['status'].title())
        with col3:
            st.write(f"{agent['confidence']:.0%}")
        with col4:
            st.write(agent['duration'])
    
    # Action buttons
    st.markdown("---")
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("💬 Chat about Application", use_container_width=True):
            st.session_state.navigation = "Chat Assistant"
    
    with col5:
        if st.button("📄 Download Report", use_container_width=True):
            st.success("Report download started...")
    
    with col6:
        if st.button("🔄 Check for Updates", use_container_width=True):
            st.rerun()

def show_admin_dashboard():
    """Show admin dashboard"""
    st.markdown('<div class="sub-header">👨‍💼 Admin Dashboard</div>', unsafe_allow_html=True)
    
    # Admin authentication
    if not st.session_state.admin_authenticated:
        st.warning("🔒 Admin authentication required")
        
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username", placeholder="Enter admin username")
        with col2:
            password = st.text_input("Password", type="password", placeholder="Enter admin password")
        
        if st.button("Login", use_container_width=True):
            if username == "admin" and password == "admin123":
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Invalid credentials")
        return
    
    # Admin dashboard content
    st.success("🔓 Admin access granted")
    
    # Quick stats
    st.markdown("### 📈 Quick Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Applications", "1,247", "12%")
    with col2:
        st.metric("Approval Rate", "68%", "5%")
    with col3:
        st.metric("Avg Processing Time", "2.3 min", "-0.5 min")
    with col4:
        st.metric("System Uptime", "99.8%", "0.2%")
    
    # Charts
    col5, col6 = st.columns(2)
    
    with col5:
        st.markdown("#### Applications by Status")
        status_data = pd.DataFrame({
            'Status': ['Approved', 'Processing', 'Rejected', 'Pending Review'],
            'Count': [450, 287, 210, 300]
        })
        fig = px.pie(status_data, values='Count', names='Status')
        st.plotly_chart(fig, use_container_width=True)
    
    with col6:
        st.markdown("#### Processing Time Distribution")
        time_data = pd.DataFrame({
            'Time Range': ['<1 min', '1-2 min', '2-3 min', '3-5 min', '>5 min'],
            'Count': [320, 450, 280, 150, 47]
        })
        fig = px.bar(time_data, x='Time Range', y='Count')
        st.plotly_chart(fig, use_container_width=True)
    
    # AI Agent Performance
    st.markdown("### 🤖 AI Agent Performance")
    
    agent_performance = pd.DataFrame({
        'Agent': ['Data Extraction', 'Data Validation', 'Eligibility Assessment', 'Decision Recommendation', 'Economic Support'],
        'Success Rate': [96.2, 94.8, 92.1, 89.7, 95.3],
        'Avg Processing Time (s)': [12.3, 8.7, 15.2, 10.1, 7.8]
    })
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Success Rate %', x=agent_performance['Agent'], y=agent_performance['Success Rate']))
    fig.add_trace(go.Scatter(name='Processing Time (s)', x=agent_performance['Agent'], y=agent_performance['Avg Processing Time (s)'], 
                           yaxis='y2', mode='lines+markers', line=dict(color='red')))
    
    fig.update_layout(
        yaxis=dict(title='Success Rate %'),
        yaxis2=dict(title='Processing Time (s)', overlaying='y', side='right'),
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # System management
    st.markdown("### ⚙️ System Management")
    
    col7, col8, col9 = st.columns(3)
    
    with col7:
        if st.button("🔄 Retrain ML Models", use_container_width=True):
            st.info("Model retraining started...")
    
    with col8:
        if st.button("🧹 Run Maintenance", use_container_width=True):
            st.info("System maintenance tasks executed")
    
    with col9:
        if st.button("📊 Generate Reports", use_container_width=True):
            st.info("Reports generation in progress...")
    
    # Logout
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.rerun()

# Mock data generators
def _generate_mock_application_response(application_data: Dict) -> Dict:
    """Generate mock application response for demo"""
    return {
        'success': True,
        'application_id': f"APP{int(datetime.now().timestamp())}",
        'processing_time_seconds': 143.2,
        'eligibility_score': 0.78,
        'decision': {
            'decision': 'APPROVE - Partial Support',
            'support_level': 'Partial',
            'confidence': 'High',
            'justifications': [
                'Moderate income level indicates need for support',
                'Family situation suggests appropriate support level',
                'Employment status considered in assessment'
            ]
        },
        'economic_recommendations': [
            {
                'title': 'Job Matching Program',
                'description': 'Connect with employers based on your skills profile',
                'priority_score': 9,
                'category': 'Employment'
            },
            {
                'title': 'Digital Skills Training',
                'description': 'Enhance computer and internet skills for modern workplaces',
                'priority_score': 8,
                'category': 'Training'
            },
            {
                'title': 'Financial Literacy Workshop',
                'description': 'Learn budgeting and financial management strategies',
                'priority_score': 7,
                'category': 'Education'
            }
        ],
        'validation_results': {
            'overall_consistency_score': 0.92,
            'document_checks': {
                'completeness_score': 0.95
            }
        },
        'extraction_summary': {
            'documents_processed': 6,
            'extraction_methods': ['direct_mapping', 'text_parsing', 'ocr_parsing']
        }
    }

def _generate_mock_chat_response(message: str) -> Dict:
    """Generate mock chat response for demo"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['status', 'progress']):
        return {
            'response': "I can help you check your application status. Please provide your application ID, or if you've already submitted an application, I can check the current processing stage for you.",
            'suggestions': [
                "How do I find my application ID?",
                "What's the typical processing time?",
                "What documents are required?"
            ]
        }
    elif any(word in message_lower for word in ['eligibility', 'qualify']):
        return {
            'response': "Eligibility is based on multiple factors including income level, family size, employment status, and financial situation. Our AI system assesses all these factors automatically. The main criteria include monthly income below 5000 AED per family member, UAE residency, and demonstrated financial need.",
            'suggestions': [
                "What income level qualifies?",
                "How does family size affect eligibility?",
                "What documents prove eligibility?"
            ]
        }
    else:
        return {
            'response': "I'm here to help you with social support applications and economic enablement programs. I can assist with application status, eligibility criteria, document requirements, and support services information. What would you like to know?",
            'suggestions': [
                "How long does the application process take?",
                "What types of support are available?",
                "How do I upload documents?",
                "Can I appeal a decision?"
            ]
        }

def _generate_mock_application_status(application_id: str) -> Dict:
    """Generate mock application status for demo"""
    return {
        'application_id': application_id,
        'status': 'processed',
        'eligibility_score': 0.65,
        'processing_time_seconds': 156.8,
        'decision': {
            'decision': 'SOFT DECLINE - Conditional Approval Possible',
            'confidence': 'Medium'
        }
    }

def _generate_mock_recent_applications() -> List[Dict]:
    """Generate mock recent applications for demo"""
    return [
        {
            'application_id': 'APP1705412300',
            'submission_date': '2024-01-15 10:30:00',
            'eligibility_score': 0.78,
            'status': 'Approved'
        },
        {
            'application_id': 'APP1705411500', 
            'submission_date': '2024-01-15 10:25:00',
            'eligibility_score': 0.45,
            'status': 'Pending Review'
        },
        {
            'application_id': 'APP1705410900',
            'submission_date': '2024-01-15 10:15:00',
            'eligibility_score': 0.92,
            'status': 'Approved'
        }
    ]

if __name__ == "__main__":
    main()