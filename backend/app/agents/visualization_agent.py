from .base_agent import BaseAgent
from typing import Dict, List, Any
import logging
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import json

logger = logging.getLogger(__name__)

class VisualizationAgent(BaseAgent):
    def __init__(self):
        super().__init__("VisualizationAgent")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visualizations based on analyzed data"""
        data = input_data.get("data", {})
        analysis = input_data.get("analysis", {})
        query_type = input_data.get("query_type", "general")
        
        try:
            visualizations = []
            
            if query_type == "comparison":
                visualizations.extend(await self._create_comparison_charts(data, analysis))
            elif query_type == "trend_analysis":
                visualizations.extend(await self._create_trend_charts(data, analysis))
            elif query_type == "district_comparison":
                visualizations.extend(await self._create_district_charts(data, analysis))
            elif query_type == "policy_recommendation":
                visualizations.extend(await self._create_policy_charts(data, analysis))
            else:
                visualizations.extend(await self._create_general_charts(data, analysis))
            
            result = {
                "agent": self.name,
                "status": "success",
                "visualizations": visualizations
            }
            
            logger.info(f"Generated {len(visualizations)} visualizations")
            return result
            
        except Exception as e:
            logger.error(f"Error in visualization: {e}")
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "visualizations": []
            }
    
    async def _create_comparison_charts(self, data: Dict, analysis: Dict) -> List[Dict]:
        """Create charts for comparison queries"""
        charts = []
        
        # Rainfall comparison chart
        if "rainfall" in data and data["rainfall"]:
            rainfall_df = pd.DataFrame(data["rainfall"])
            
            fig = px.bar(
                rainfall_df, 
                x='year', 
                y='avg_rainfall',
                color='district',
                title="Average Annual Rainfall by District and Year",
                labels={'avg_rainfall': 'Average Rainfall (mm)', 'year': 'Year'}
            )
            fig.update_layout(height=500)
            
            charts.append({
                "type": "rainfall_comparison",
                "title": "Rainfall Comparison",
                "chart": fig.to_json(),
                "description": "Comparison of average annual rainfall across districts and years"
            })
        
        # Crop production comparison chart
        if "crops" in data and data["crops"]:
            crops_df = pd.DataFrame(data["crops"])
            
            fig = px.bar(
                crops_df,
                x='crop',
                y='total_production',
                color='crop_year',
                title="Crop Production Comparison",
                labels={'total_production': 'Total Production (tonnes)', 'crop': 'Crop'}
            )
            fig.update_layout(height=500, xaxis_tickangle=45)
            
            charts.append({
                "type": "crop_comparison",
                "title": "Crop Production Comparison",
                "chart": fig.to_json(),
                "description": "Comparison of crop production across different crops and years"
            })
        
        return charts
    
    async def _create_trend_charts(self, data: Dict, analysis: Dict) -> List[Dict]:
        """Create charts for trend analysis"""
        charts = []
        
        # Crop production trends
        if "crop_trends" in data and data["crop_trends"]:
            crop_trends_df = pd.DataFrame(data["crop_trends"])
            
            fig = px.line(
                crop_trends_df,
                x='crop_year',
                y='total_production',
                color='crop',
                title="Crop Production Trends Over Time",
                labels={'total_production': 'Total Production (tonnes)', 'crop_year': 'Year'}
            )
            fig.update_layout(height=500)
            
            charts.append({
                "type": "crop_trends",
                "title": "Crop Production Trends",
                "chart": fig.to_json(),
                "description": "Trend analysis of crop production over time"
            })
        
        # Rainfall trends
        if "rainfall_trends" in data and data["rainfall_trends"]:
            rainfall_trends_df = pd.DataFrame(data["rainfall_trends"])
            
            fig = px.line(
                rainfall_trends_df,
                x='year',
                y='avg_rainfall',
                color='district',
                title="Rainfall Trends Over Time",
                labels={'avg_rainfall': 'Average Rainfall (mm)', 'year': 'Year'}
            )
            fig.update_layout(height=500)
            
            charts.append({
                "type": "rainfall_trends",
                "title": "Rainfall Trends",
                "chart": fig.to_json(),
                "description": "Trend analysis of rainfall patterns over time"
            })
        
        # Correlation chart
        if "correlations" in analysis and analysis["correlations"]:
            correlations = analysis["correlations"]
            crops = list(correlations.keys())
            corr_values = [correlations[crop]["correlation"] for crop in crops]
            
            fig = go.Figure(data=[
                go.Bar(x=crops, y=corr_values, 
                      marker_color=['green' if val > 0 else 'red' for val in corr_values])
            ])
            fig.update_layout(
                title="Crop Production vs Rainfall Correlation",
                xaxis_title="Crop",
                yaxis_title="Correlation Coefficient",
                height=500
            )
            
            charts.append({
                "type": "correlation",
                "title": "Crop-Rainfall Correlation",
                "chart": fig.to_json(),
                "description": "Correlation between crop production and rainfall patterns"
            })
        
        return charts
    
    async def _create_district_charts(self, data: Dict, analysis: Dict) -> List[Dict]:
        """Create charts for district comparison"""
        charts = []
        
        if "district_production" in data and data["district_production"]:
            district_df = pd.DataFrame(data["district_production"])
            
            # District production ranking
            latest_year = district_df['crop_year'].max()
            latest_data = district_df[district_df['crop_year'] == latest_year]
            
            if not latest_data.empty:
                district_production = latest_data.groupby('district')['total_production'].sum().sort_values(ascending=True)
                
                fig = px.bar(
                    x=district_production.values,
                    y=district_production.index,
                    orientation='h',
                    title=f"District-wise Crop Production ({latest_year})",
                    labels={'x': 'Total Production (tonnes)', 'y': 'District'}
                )
                fig.update_layout(height=600)
                
                charts.append({
                    "type": "district_ranking",
                    "title": "District Production Ranking",
                    "chart": fig.to_json(),
                    "description": f"Ranking of districts by total crop production in {latest_year}"
                })
        
        return charts
    
    async def _create_policy_charts(self, data: Dict, analysis: Dict) -> List[Dict]:
        """Create charts for policy recommendations"""
        charts = []
        
        # Crop performance comparison
        if "crop_performance" in analysis and analysis["crop_performance"]:
            crop_perf = analysis["crop_performance"]
            crops = list(crop_perf.keys())
            yields = [crop_perf[crop]["yield_per_hectare"] for crop in crops]
            stability = [crop_perf[crop]["production_stability"] for crop in crops]
            
            # Create subplot with yield and stability
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Yield per Hectare', 'Production Stability'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            fig.add_trace(
                go.Bar(x=crops, y=yields, name="Yield (tonnes/hectare)"),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Bar(x=crops, y=stability, name="Stability Index"),
                row=1, col=2
            )
            
            fig.update_layout(
                title="Crop Performance Analysis",
                height=500,
                showlegend=False
            )
            
            charts.append({
                "type": "crop_performance",
                "title": "Crop Performance Analysis",
                "chart": fig.to_json(),
                "description": "Analysis of crop yield and production stability for policy recommendations"
            })
        
        # Rainfall patterns
        if "rainfall_patterns" in analysis and analysis["rainfall_patterns"]:
            rainfall_patterns = analysis["rainfall_patterns"]
            
            months = list(range(1, 13))
            monthly_rainfall = [rainfall_patterns.get("wettest_months", {}).get(str(m), 0) for m in months]
            
            fig = px.bar(
                x=months,
                y=monthly_rainfall,
                title="Average Monthly Rainfall Pattern",
                labels={'x': 'Month', 'y': 'Average Rainfall (mm)'}
            )
            fig.update_layout(height=400)
            
            charts.append({
                "type": "rainfall_patterns",
                "title": "Monthly Rainfall Patterns",
                "chart": fig.to_json(),
                "description": "Monthly rainfall patterns to inform crop selection policies"
            })
        
        return charts
    
    async def _create_general_charts(self, data: Dict, analysis: Dict) -> List[Dict]:
        """Create general charts"""
        charts = []
        
        # Top crops chart
        if "crop_summary" in analysis and "top_crops" in analysis["crop_summary"]:
            top_crops = analysis["crop_summary"]["top_crops"]
            
            fig = px.pie(
                values=list(top_crops.values()),
                names=list(top_crops.keys()),
                title="Top Crops by Total Production"
            )
            fig.update_layout(height=500)
            
            charts.append({
                "type": "top_crops",
                "title": "Top Crops Distribution",
                "chart": fig.to_json(),
                "description": "Distribution of top crops by total production"
            })
        
        return charts
