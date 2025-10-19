# 7_observability/monitoring_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests
import json
from typing import Dict, List, Any
import time

class MonitoringDashboard:
    """Real-time monitoring dashboard for AI system observability"""
    
    def __init__(self, langfuse_manager):
        self.langfuse_manager = langfuse_manager
        self.setup_dashboard()
    
    def setup_dashboard(self):
        """Setup dashboard configuration"""
        st.set_page_config(
            page_title="AI System Monitoring",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def show_dashboard(self):
        """Display the main monitoring dashboard"""
        st.title("🤖 AI System Monitoring Dashboard")
        st.markdown("Real-time observability and performance metrics for Social Support AI Assistant")
        
        # Quick status overview
        self._show_system_overview()
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self._show_throughput_metrics()
        
        with col2:
            self._show_performance_metrics()
        
        with col3:
            self._show_error_metrics()
        
        with col4:
            self._show_llm_metrics()
        
        # Detailed charts
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Agent Performance", 
            "🔍 Request Analytics", 
            "⚡ System Health",
            "📊 LLM Usage"
        ])
        
        with tab1:
            self._show_agent_performance()
        
        with tab2:
            self._show_request_analytics()
        
        with tab3:
            self._show_system_health()
        
        with tab4:
            self._show_llm_usage()
        
        # Real-time updates
        if st.button("🔄 Refresh Metrics"):
            st.rerun()
        
        # Auto-refresh
        st.markdown("---")
        auto_refresh = st.checkbox("Auto-refresh every 30 seconds", value=False)
        if auto_refresh:
            time.sleep(30)
            st.rerun()
    
    def _show_system_overview(self):
        """Show system overview status"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("System Status", "🟢 Operational", "Stable")
        
        with col2:
            st.metric("Active Processes", "8", "+2")
        
        with col3:
            st.metric("Uptime", "99.8%", "0.1%")
        
        st.markdown("---")
    
    def _show_throughput_metrics(self):
        """Show throughput metrics"""
        metrics = self._get_throughput_metrics()
        
        st.metric(
            "Applications/Hour", 
            f"{metrics['applications_per_hour']}",
            f"{metrics['throughput_change']}%"
        )
        st.caption(f"Peak: {metrics['peak_throughput']}/hour")
    
    def _show_performance_metrics(self):
        """Show performance metrics"""
        metrics = self._get_performance_metrics()
        
        st.metric(
            "Avg Processing Time", 
            f"{metrics['avg_processing_time']:.1f}s",
            f"{metrics['processing_time_change']:.1f}s"
        )
        st.caption(f"P95: {metrics['p95_processing_time']:.1f}s")
    
    def _show_error_metrics(self):
        """Show error metrics"""
        metrics = self._get_error_metrics()
        
        st.metric(
            "Error Rate", 
            f"{metrics['error_rate']:.1f}%",
            f"{metrics['error_rate_change']:.1f}%",
            delta_color="inverse"
        )
        st.caption(f"Total Errors: {metrics['total_errors']}")
    
    def _show_llm_metrics(self):
        """Show LLM usage metrics"""
        metrics = self._get_llm_metrics()
        
        st.metric(
            "LLM Tokens/Hour", 
            f"{metrics['tokens_per_hour']:,}",
            f"{metrics['token_change']}%"
        )
        st.caption(f"Avg Response: {metrics['avg_response_time']:.1f}s")
    
    def _show_agent_performance(self):
        """Show detailed agent performance charts"""
        st.subheader("AI Agent Performance Metrics")
        
        # Get agent performance data
        agent_data = self._get_agent_performance_data()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Success rates chart
            fig1 = px.bar(
                agent_data, 
                x='agent', 
                y='success_rate',
                title="Agent Success Rates",
                color='success_rate',
                color_continuous_scale='RdYlGn'
            )
            fig1.update_layout(yaxis_title="Success Rate (%)", xaxis_title="Agent")
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Processing time chart
            fig2 = px.bar(
                agent_data,
                x='agent',
                y='avg_duration',
                title="Average Processing Time",
                color='avg_duration',
                color_continuous_scale='Blues'
            )
            fig2.update_layout(yaxis_title="Time (seconds)", xaxis_title="Agent")
            st.plotly_chart(fig2, use_container_width=True)
        
        # Throughput over time
        st.subheader("Agent Throughput Over Time")
        throughput_data = self._get_agent_throughput_data()
        
        fig3 = px.line(
            throughput_data,
            x='timestamp',
            y='throughput',
            color='agent',
            title="Agent Throughput (Last 24 Hours)",
            markers=True
        )
        fig3.update_layout(
            xaxis_title="Time",
            yaxis_title="Requests per Hour",
            hovermode='x unified'
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    def _show_request_analytics(self):
        """Show request analytics and patterns"""
        st.subheader("Request Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Request distribution by hour
            hourly_data = self._get_hourly_request_data()
            fig1 = px.area(
                hourly_data,
                x='hour',
                y='requests',
                title="Request Distribution by Hour",
                color_discrete_sequence=['#1f77b4']
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Request types breakdown
            type_data = self._get_request_type_data()
            fig2 = px.pie(
                type_data,
                values='count',
                names='type',
                title="Request Type Distribution"
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Error patterns
        st.subheader("Error Analysis")
        error_data = self._get_error_pattern_data()
        
        fig3 = px.sunburst(
            error_data,
            path=['category', 'type'],
            values='count',
            title="Error Pattern Analysis"
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    def _show_system_health(self):
        """Show system health metrics"""
        st.subheader("System Health Monitoring")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Resource usage
            resource_data = self._get_resource_usage_data()
            
            fig1 = go.Figure()
            fig1.add_trace(go.Indicator(
                mode = "gauge+number",
                value = resource_data['cpu_usage'],
                title = {'text': "CPU Usage"},
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"}],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90}}
            ))
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Memory usage
            memory_data = self._get_memory_usage_data()
            
            fig2 = go.Figure()
            fig2.add_trace(go.Indicator(
                mode = "gauge+number",
                value = memory_data['memory_usage'],
                title = {'text': "Memory Usage"},
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgray"},
                        {'range': [60, 85], 'color': "gray"}],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90}}
            ))
            st.plotly_chart(fig2, use_container_width=True)
        
        # Latency trends
        st.subheader("Latency Trends")
        latency_data = self._get_latency_trend_data()
        
        fig3 = px.line(
            latency_data,
            x='timestamp',
            y='latency',
            title="API Response Latency (Last 6 Hours)",
            color_discrete_sequence=['#ff7f0e']
        )
        fig3.update_layout(
            xaxis_title="Time",
            yaxis_title="Latency (ms)",
            showlegend=False
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    def _show_llm_usage(self):
        """Show LLM usage analytics"""
        st.subheader("LLM Usage Analytics")
        
        llm_data = self._get_llm_usage_data()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Token usage by model
            fig1 = px.bar(
                llm_data['models'],
                x='model',
                y='tokens',
                title="Token Usage by Model",
                color='tokens',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Cost analysis
            fig2 = px.pie(
                llm_data['costs'],
                values='cost',
                names='model',
                title="Cost Distribution by Model"
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Usage trends
        st.subheader("LLM Usage Trends")
        usage_trends = self._get_llm_usage_trends()
        
        fig3 = px.line(
            usage_trends,
            x='hour',
            y='tokens',
            color='model',
            title="Token Usage Trends (Last 24 Hours)",
            markers=True
        )
        fig3.update_layout(
            xaxis_title="Hour of Day",
            yaxis_title="Tokens (Thousands)",
            hovermode='x unified'
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    # Data generation methods (would connect to real observability backend)
    def _get_throughput_metrics(self) -> Dict:
        """Get throughput metrics"""
        return {
            'applications_per_hour': 52,
            'throughput_change': 12,
            'peak_throughput': 68
        }
    
    def _get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        return {
            'avg_processing_time': 143.2,
            'processing_time_change': -5.3,
            'p95_processing_time': 287.6
        }
    
    def _get_error_metrics(self) -> Dict:
        """Get error metrics"""
        return {
            'error_rate': 2.3,
            'error_rate_change': -0.5,
            'total_errors': 28
        }
    
    def _get_llm_metrics(self) -> Dict:
        """Get LLM metrics"""
        return {
            'tokens_per_hour': 12500,
            'token_change': 8,
            'avg_response_time': 2.1
        }
    
    def _get_agent_performance_data(self) -> pd.DataFrame:
        """Get agent performance data"""
        return pd.DataFrame({
            'agent': ['Data Extraction', 'Data Validation', 'Eligibility Assessment', 
                     'Decision Recommendation', 'Economic Support'],
            'success_rate': [96.2, 94.8, 92.1, 89.7, 95.3],
            'avg_duration': [12.3, 8.7, 15.2, 10.1, 7.8],
            'throughput': [45, 42, 38, 40, 43]
        })
    
    def _get_agent_throughput_data(self) -> pd.DataFrame:
        """Get agent throughput over time"""
        # Generate mock time series data
        agents = ['Data Extraction', 'Data Validation', 'Eligibility Assessment']
        data = []
        
        for hour in range(24):
            for agent in agents:
                base_throughput = 40 if agent == 'Data Extraction' else 35 if agent == 'Data Validation' else 30
                # Add some variation
                throughput = base_throughput + (hour % 6) * 5
                data.append({
                    'timestamp': f"{hour:02d}:00",
                    'agent': agent,
                    'throughput': throughput
                })
        
        return pd.DataFrame(data)
    
    def _get_hourly_request_data(self) -> pd.DataFrame:
        """Get hourly request distribution"""
        hours = list(range(24))
        requests = [20, 15, 10, 8, 5, 10, 25, 45, 60, 55, 50, 48, 
                   52, 55, 50, 48, 45, 50, 55, 52, 45, 35, 25, 20]
        
        return pd.DataFrame({'hour': hours, 'requests': requests})
    
    def _get_request_type_data(self) -> pd.DataFrame:
        """Get request type distribution"""
        return pd.DataFrame({
            'type': ['Application Submit', 'Status Check', 'Chat Message', 'Document Upload', 'Admin API'],
            'count': [45, 120, 85, 30, 15]
        })
    
    def _get_error_pattern_data(self) -> pd.DataFrame:
        """Get error pattern data"""
        return pd.DataFrame({
            'category': ['Data Quality', 'Data Quality', 'Processing', 'Processing', 'System', 'System'],
            'type': ['Document Parse', 'Validation Failed', 'Timeout', 'Resource Limit', 'Database', 'API'],
            'count': [25, 20, 12, 8, 5, 3]
        })
    
    def _get_resource_usage_data(self) -> Dict:
        """Get resource usage data"""
        return {
            'cpu_usage': 45.2,
            'memory_usage': 67.8,
            'disk_usage': 23.4
        }
    
    def _get_memory_usage_data(self) -> Dict:
        """Get memory usage data"""
        return {
            'memory_usage': 67.8,
            'available_memory': 32.2
        }
    
    def _get_latency_trend_data(self) -> pd.DataFrame:
        """Get latency trend data"""
        timestamps = []
        latencies = []
        
        base_time = datetime.now() - timedelta(hours=6)
        
        for i in range(12):  # Every 30 minutes for 6 hours
            timestamp = base_time + timedelta(minutes=30 * i)
            # Simulate some latency variation
            latency = 120 + (i % 4) * 20
            timestamps.append(timestamp.strftime("%H:%M"))
            latencies.append(latency)
        
        return pd.DataFrame({'timestamp': timestamps, 'latency': latencies})
    
    def _get_llm_usage_data(self) -> Dict:
        """Get LLM usage data"""
        return {
            'models': pd.DataFrame({
                'model': ['Llama2-7B', 'Mistral-7B', 'CodeLlama', 'Embedding Model'],
                'tokens': [45000, 32000, 15000, 8000],
                'cost': [12.5, 8.7, 4.2, 2.1]
            }),
            'costs': pd.DataFrame({
                'model': ['Llama2-7B', 'Mistral-7B', 'CodeLlama', 'Embedding Model'],
                'cost': [12.5, 8.7, 4.2, 2.1]
            })
        }
    
    def _get_llm_usage_trends(self) -> pd.DataFrame:
        """Get LLM usage trends"""
        models = ['Llama2-7B', 'Mistral-7B', 'Embedding Model']
        data = []
        
        for hour in range(24):
            for model in models:
                base_tokens = 2000 if model == 'Llama2-7B' else 1500 if model == 'Mistral-7B' else 800
                # Add usage patterns
                tokens = base_tokens + (hour % 8) * 300
                data.append({
                    'hour': hour,
                    'model': model,
                    'tokens': tokens / 1000  # Convert to thousands
                })
        
        return pd.DataFrame(data)

# Standalone monitoring app
def run_monitoring_dashboard():
    """Run the monitoring dashboard as a standalone app"""
    from observability.langfuse_config import LangfuseManager
    
    manager = LangfuseManager()
    dashboard = MonitoringDashboard(manager)
    dashboard.show_dashboard()

if __name__ == "__main__":
    run_monitoring_dashboard()