# frontend/components.py
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any

def create_eligibility_gauge(score: float) -> go.Figure:
    """Create an eligibility score gauge chart"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Eligibility Score", 'font': {'size': 24}},
        delta = {'reference': 50, 'increasing': {'color': "green"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': 'red'},
                {'range': [40, 70], 'color': 'yellow'},
                {'range': [70, 100], 'color': 'green'}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90}}))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def create_agent_performance_chart(performance_data: Dict) -> go.Figure:
    """Create agent performance comparison chart"""
    agents = list(performance_data.keys())
    success_rates = [data.get('success_rate', 0) for data in performance_data.values()]
    processing_times = [data.get('avg_processing_time', 0) for data in performance_data.values()]
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add success rate bars
    fig.add_trace(
        go.Bar(
            name="Success Rate %", 
            x=agents, 
            y=success_rates,
            marker_color='lightblue'
        ),
        secondary_y=False,
    )
    
    # Add processing time line
    fig.add_trace(
        go.Scatter(
            name="Processing Time (s)", 
            x=agents, 
            y=processing_times,
            line=dict(color='red', width=3),
            marker=dict(size=8)
        ),
        secondary_y=True,
    )
    
    fig.update_layout(
        title="AI Agent Performance",
        xaxis_tickangle=-45,
        height=400
    )
    
    fig.update_yaxes(title_text="Success Rate %", secondary_y=False)
    fig.update_yaxes(title_text="Processing Time (s)", secondary_y=True)
    
    return fig

def create_timeline_chart(timeline_data: List[Dict]) -> go.Figure:
    """Create processing timeline chart"""
    stages = [step['stage'] for step in timeline_data]
    statuses = [step['status'] for step in timeline_data]
    
    # Convert status to numerical values for coloring
    status_values = []
    for status in statuses:
        if status == 'completed':
            status_values.append(2)
        elif status == 'current':
            status_values.append(1)
        else:
            status_values.append(0)
    
    fig = go.Figure(go.Scatter(
        x=stages,
        y=[1] * len(stages),  # Constant y-value for horizontal timeline
        mode='markers+lines+text',
        marker=dict(
            size=20,
            color=status_values,
            colorscale=[[0, 'red'], [0.5, 'yellow'], [1, 'green']],
            showscale=False
        ),
        line=dict(color='gray', width=2),
        text=[f"Stage {i+1}" for i in range(len(stages))],
        textposition="middle right"
    ))
    
    fig.update_layout(
        title="Application Processing Timeline",
        xaxis_title="Processing Stages",
        yaxis=dict(showticklabels=False, showgrid=False),
        height=200,
        showlegend=False
    )
    
    return fig

def create_recommendations_radar(recommendations: List[Dict]) -> go.Figure:
    """Create radar chart for recommendations priority"""
    categories = list(set([rec.get('category', 'General') for rec in recommendations]))
    
    # Calculate average priority by category
    category_priority = {}
    for category in categories:
        cat_recs = [rec for rec in recommendations if rec.get('category') == category]
        if cat_recs:
            category_priority[category] = sum(rec.get('priority_score', 0) for rec in cat_recs) / len(cat_recs)
    
    fig = go.Figure(data=go.Scatterpolar(
        r=list(category_priority.values()),
        theta=list(category_priority.keys()),
        fill='toself',
        line=dict(color='blue'),
        name="Recommendation Priority"
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=False,
        title="Recommendations by Category",
        height=400
    )
    
    return fig

def create_validation_heatmap(validation_results: Dict) -> go.Figure:
    """Create heatmap for validation results"""
    checks = list(validation_results.keys())
    scores = [results.get('score', 0) for results in validation_results.values()]
    statuses = [results.get('status', 'unknown') for results in validation_results.values()]
    
    # Convert status to colors
    colors = []
    for status in statuses:
        if status == 'passed':
            colors.append('green')
        elif status == 'warning':
            colors.append('yellow') 
        else:
            colors.append('red')
    
    fig = go.Figure(data=go.Heatmap(
        z=[scores],
        x=checks,
        y=['Validation Score'],
        colorscale='RdYlGn',
        showscale=True,
        hoverinfo='x+z'
    ))
    
    fig.update_layout(
        title="Data Validation Results",
        height=200,
        xaxis_tickangle=-45
    )
    
    return fig

def create_metrics_dashboard(metrics: Dict) -> st.container:
    """Create a comprehensive metrics dashboard"""
    container = st.container()
    
    with container:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Applications", 
                metrics.get('total_applications', 0),
                delta=metrics.get('application_growth', 0)
            )
        
        with col2:
            st.metric(
                "Approval Rate",
                f"{metrics.get('approval_rate', 0):.1f}%",
                delta=f"{metrics.get('approval_rate_change', 0):.1f}%"
            )
        
        with col3:
            st.metric(
                "Avg Processing Time", 
                f"{metrics.get('avg_processing_time', 0):.1f}s",
                delta=f"{metrics.get('processing_time_change', 0):.1f}s"
            )
        
        with col4:
            st.metric(
                "System Accuracy",
                f"{metrics.get('system_accuracy', 0):.1f}%",
                delta=f"{metrics.get('accuracy_change', 0):.1f}%"
            )
    
    return container

def create_application_card(application: Dict) -> st.container:
    """Create a styled application card"""
    container = st.container()
    
    with container:
        # Card header
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{application.get('application_id', 'Unknown')}**")
            st.caption(f"Submitted: {application.get('submission_date', 'Unknown')}")
        
        with col2:
            score = application.get('eligibility_score', 0)
            score_color = "green" if score > 0.7 else "orange" if score > 0.4 else "red"
            st.markdown(f"**Score:** <span style='color: {score_color};'>{score:.0%}</span>", 
                       unsafe_allow_html=True)
        
        with col3:
            status = application.get('status', 'unknown')
            status_color = "green" if status == 'approved' else "blue" if status == 'processing' else "red"
            st.markdown(f"**Status:** <span style='color: {status_color};'>{status.title()}</span>", 
                       unsafe_allow_html=True)
        
        # Card content
        with st.expander("View Details"):
            col4, col5 = st.columns(2)
            
            with col4:
                st.write("**Applicant:**", application.get('applicant_name', 'Unknown'))
                st.write("**Income:**", f"AED {application.get('monthly_income', 0):,}")
                st.write("**Family Size:**", application.get('family_size', 0))
            
            with col5:
                st.write("**Employment:**", application.get('employment_status', 'Unknown'))
                st.write("**Decision:**", application.get('decision', 'Pending'))
                st.write("**Processing Time:**", f"{application.get('processing_time', 0):.1f}s")
    
    return container

def create_chat_bubble(message: Dict) -> st.container:
    """Create a styled chat bubble"""
    container = st.container()
    
    with container:
        if message['type'] == 'user':
            st.markdown(
                f"""
                <div style='
                    background-color: #e3f2fd;
                    padding: 12px 16px;
                    border-radius: 18px 18px 0 18px;
                    margin: 8px 0;
                    margin-left: 20%;
                    max-width: 80%;
                    float: right;
                    clear: both;
                '>
                    <strong>You:</strong><br>
                    {message['content']}
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style='
                    background-color: #f5f5f5;
                    padding: 12px 16px;
                    border-radius: 18px 18px 18px 0;
                    margin: 8px 0;
                    margin-right: 20%;
                    max-width: 80%;
                    float: left;
                    clear: both;
                '>
                    <strong>AI Assistant:</strong><br>
                    {message['content']}
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    return container