import streamlit as st
import requests
import json
import plotly
from typing import Dict, List, Any
import time

# Configure page
st.set_page_config(
    page_title="Project Samarth - Agricultural Q&A",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Sample questions
SAMPLE_QUESTIONS = [
    "Compare the average annual rainfall in Agra and Lucknow for the last 5 available years. In parallel, list the top 3 most produced crops by volume in each of those districts during the same period.",
    "Identify the district in Uttar Pradesh with the highest production of Rice in the most recent year available and compare that with the district with the lowest production of Rice.",
    "Analyze the production trend of Wheat in Uttar Pradesh over the last decade. Correlate this trend with the corresponding climate data for the same period.",
    "A policy advisor is proposing a scheme to promote drought-resistant crops over water-intensive crops in Uttar Pradesh. Based on historical data from the last 5 years, what are the three most compelling data-backed arguments to support this policy?"
]

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except:
        return False, None

def process_query(question: str) -> Dict[str, Any]:
    """Send query to the API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/query",
            json={"question": question},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "status": "error",
                "error": f"API Error: {response.status_code}",
                "details": response.text
            }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error": "Request timeout",
            "details": "The query took too long to process. Please try a simpler question."
        }
    except Exception as e:
        return {
            "status": "error",
            "error": "Connection error",
            "details": str(e)
        }

def display_citations(citations: List[Dict[str, str]]):
    """Display citations in a formatted way"""
    if not citations:
        return
    
    st.subheader("📚 Data Sources & Citations")
    
    for citation in citations:
        with st.expander(f"{citation['id']} {citation['description']}"):
            st.write(f"**Source:** {citation['description']}")
            st.write(f"**URL:** [{citation['url']}]({citation['url']})")
            st.write(f"**Accessed:** {citation['access_date']}")

def display_visualizations(visualizations: List[Dict[str, Any]]):
    """Display visualizations"""
    if not visualizations:
        return
    
    st.subheader("📊 Visualizations")
    
    for viz in visualizations:
        st.write(f"**{viz['title']}**")
        st.write(viz['description'])
        
        try:
            chart_data = json.loads(viz['chart'])
            fig = plotly.io.from_json(json.dumps(chart_data))
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error displaying chart: {e}")
        
        st.divider()

def display_raw_data(raw_data: Dict[str, Any]):
    """Display raw data in expandable sections"""
    if not raw_data:
        return
    
    st.subheader("📋 Raw Data")
    
    for data_type, data_list in raw_data.items():
        if data_list:
            with st.expander(f"View {data_type.replace('_', ' ').title()} Data"):
                if isinstance(data_list, list) and len(data_list) > 0:
                    st.dataframe(data_list, use_container_width=True)
                else:
                    st.write("No data available")

def main():
    """Main Streamlit application"""
    
    # Header
    st.title("🌾 Project Samarth")
    st.subheader("Intelligent Agricultural Q&A System for Uttar Pradesh")
    
    # Check API health
    api_healthy, health_data = check_api_health()
    
    if not api_healthy:
        st.error("⚠️ API is not running. Please start the FastAPI backend server.")
        st.code("cd backend && python -m uvicorn app.main:app --reload")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Sample Questions")
        st.write("Click on any question below to use it:")
        
        for i, question in enumerate(SAMPLE_QUESTIONS):
            if st.button(f"Q{i+1}: {question[:50]}...", key=f"sample_{i}"):
                st.session_state.selected_question = question
        
        st.divider()
        
        st.header("🔧 System Status")
        if health_data:
            st.success("✅ API Connected")
            st.write(f"**Database:** {health_data.get('database', 'Unknown')}")
            
            agents = health_data.get('agents', {})
            for agent, status in agents.items():
                status_emoji = "✅" if status == "active" else "❌"
                st.write(f"{status_emoji} {agent.replace('_', ' ').title()}")
        
        st.divider()
        
        if st.button("🔄 Refresh Data"):
            with st.spinner("Refreshing data..."):
                try:
                    response = requests.post(f"{API_BASE_URL}/api/data/refresh")
                    if response.status_code == 200:
                        st.success("Data refresh initiated!")
                    else:
                        st.error("Failed to refresh data")
                except:
                    st.error("Could not connect to API")
    
    # Main content area
    st.header("💬 Ask Your Question")
    
    # Question input
    default_question = st.session_state.get('selected_question', '')
    question = st.text_area(
        "Enter your question about agricultural or climate data in Uttar Pradesh:",
        value=default_question,
        height=100,
        placeholder="e.g., Compare rice production between Agra and Lucknow districts..."
    )
    
    # Clear the selected question after using it
    if 'selected_question' in st.session_state:
        del st.session_state.selected_question
    
    # Process button
    if st.button("🔍 Analyze", type="primary"):
        if not question.strip():
            st.warning("Please enter a question.")
            return
        
        # Process the query
        with st.spinner("Processing your question..."):
            result = process_query(question)
        
        if result["status"] == "success":
            # Display response
            st.subheader("🤖 Analysis Results")
            
            # Confidence score
            confidence = result.get("confidence_score", 0)
            confidence_color = "green" if confidence > 0.7 else "orange" if confidence > 0.4 else "red"
            st.markdown(f"**Confidence Score:** :{confidence_color}[{confidence:.2f}]")
            
            # Main response
            st.write(result["response"])
            
            # Summary
            if result.get("summary"):
                st.subheader("📝 Summary")
                summary = result["summary"]
                
                if summary.get("key_findings"):
                    st.write("**Key Findings:**")
                    for finding in summary["key_findings"]:
                        st.write(f"• {finding}")
                
                if summary.get("recommendations"):
                    st.write("**Recommendations:**")
                    for rec in summary["recommendations"]:
                        st.write(f"• {rec}")
            
            # Visualizations
            if result.get("visualizations"):
                display_visualizations(result["visualizations"])
            
            # Citations
            if result.get("citations"):
                display_citations(result["citations"])
            
            # Raw data
            if result.get("raw_data"):
                display_raw_data(result["raw_data"])
            
            # Processing steps
            if result.get("processing_steps"):
                with st.expander("🔍 Processing Steps"):
                    steps = result["processing_steps"]
                    for step, status in steps.items():
                        status_emoji = "✅" if status == "success" else "❌"
                        st.write(f"{status_emoji} {step.replace('_', ' ').title()}: {status}")
        
        else:
            # Display error
            st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
            if result.get("details"):
                st.write(f"**Details:** {result['details']}")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>Project Samarth - Agricultural Intelligence System | Powered by FastAPI & Streamlit</p>
        <p>Data Sources: Ministry of Agriculture & Farmers Welfare, India Meteorological Department</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
