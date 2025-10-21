from .base_agent import BaseAgent
from typing import Dict, List, Any
import logging
import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

class AnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__("AnalysisAgent")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform data analysis based on retrieved data"""
        data = input_data.get("data", {})
        query_type = input_data.get("query_type", "general")
        entities = input_data.get("extracted_entities", {})
        
        try:
            if query_type == "comparison":
                result = await self._analyze_comparison(data, entities)
            elif query_type == "trend_analysis":
                result = await self._analyze_trends(data, entities)
            elif query_type == "district_comparison":
                result = await self._analyze_districts(data, entities)
            elif query_type == "policy_recommendation":
                result = await self._analyze_policy(data, entities)
            else:
                result = await self._analyze_general(data, entities)
            
            result["agent"] = self.name
            result["status"] = "success"
            return result
            
        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "analysis": {}
            }
    
    async def _analyze_comparison(self, data: Dict, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze comparison data (rainfall + crops)"""
        rainfall_data = pd.DataFrame(data.get("rainfall", []))
        crop_data = pd.DataFrame(data.get("crops", []))
        
        analysis = {}
        
        if not rainfall_data.empty:
            # Rainfall analysis
            rainfall_analysis = {
                "avg_rainfall_by_year": rainfall_data.groupby('year')['avg_rainfall'].mean().to_dict(),
                "avg_rainfall_by_district": rainfall_data.groupby('district')['avg_rainfall'].mean().to_dict(),
                "total_districts": rainfall_data['district'].nunique(),
                "year_range": {
                    "min": int(rainfall_data['year'].min()),
                    "max": int(rainfall_data['year'].max())
                }
            }
            analysis["rainfall"] = rainfall_analysis
        
        if not crop_data.empty:
            # Crop analysis
            crop_analysis = {
                "top_crops_by_production": crop_data.nlargest(10, 'total_production')[['crop', 'total_production']].to_dict('records'),
                "crop_production_by_year": crop_data.groupby(['crop_year', 'crop'])['total_production'].sum().to_dict(),
                "total_crops": crop_data['crop'].nunique(),
                "year_range": {
                    "min": int(crop_data['crop_year'].min()),
                    "max": int(crop_data['crop_year'].max())
                }
            }
            analysis["crops"] = crop_analysis
        
        return {"analysis": analysis}
    
    async def _analyze_trends(self, data: Dict, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trend data"""
        crop_trends = pd.DataFrame(data.get("crop_trends", []))
        rainfall_trends = pd.DataFrame(data.get("rainfall_trends", []))
        
        analysis = {}
        
        if not crop_trends.empty:
            # Calculate production trends
            crop_trend_analysis = {}
            for crop in crop_trends['crop'].unique():
                crop_data = crop_trends[crop_trends['crop'] == crop]
                if len(crop_data) > 1:
                    years = crop_data['crop_year'].values
                    production = crop_data['total_production'].values
                    
                    # Calculate trend slope
                    slope, intercept, r_value, p_value, std_err = stats.linregress(years, production)
                    
                    crop_trend_analysis[crop] = {
                        "trend_slope": float(slope),
                        "correlation": float(r_value),
                        "p_value": float(p_value),
                        "trend_direction": "increasing" if slope > 0 else "decreasing",
                        "year_range": {"min": int(min(years)), "max": int(max(years))},
                        "production_range": {"min": float(min(production)), "max": float(max(production))}
                    }
            
            analysis["crop_trends"] = crop_trend_analysis
        
        if not rainfall_trends.empty:
            # Calculate rainfall trends
            rainfall_trend_analysis = {}
            for district in rainfall_trends['district'].unique():
                district_data = rainfall_trends[rainfall_trends['district'] == district]
                if len(district_data) > 1:
                    years = district_data['year'].values
                    rainfall = district_data['avg_rainfall'].values
                    
                    slope, intercept, r_value, p_value, std_err = stats.linregress(years, rainfall)
                    
                    rainfall_trend_analysis[district] = {
                        "trend_slope": float(slope),
                        "correlation": float(r_value),
                        "p_value": float(p_value),
                        "trend_direction": "increasing" if slope > 0 else "decreasing",
                        "year_range": {"min": int(min(years)), "max": int(max(years))},
                        "rainfall_range": {"min": float(min(rainfall)), "max": float(max(rainfall))}
                    }
            
            analysis["rainfall_trends"] = rainfall_trend_analysis
        
        # Correlation analysis between crops and rainfall
        if not crop_trends.empty and not rainfall_trends.empty:
            correlation_analysis = await self._calculate_crop_rainfall_correlation(crop_trends, rainfall_trends)
            analysis["correlations"] = correlation_analysis
        
        return {"analysis": analysis}
    
    async def _analyze_districts(self, data: Dict, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze district-level data"""
        district_data = pd.DataFrame(data.get("district_production", []))
        
        analysis = {}
        
        if not district_data.empty:
            # Find highest and lowest producing districts
            latest_year = district_data['crop_year'].max()
            latest_data = district_data[district_data['crop_year'] == latest_year]
            
            if not latest_data.empty:
                district_production = latest_data.groupby('district')['total_production'].sum().sort_values(ascending=False)
                
                analysis["district_ranking"] = {
                    "highest_production": {
                        "district": district_production.index[0],
                        "production": float(district_production.iloc[0])
                    },
                    "lowest_production": {
                        "district": district_production.index[-1],
                        "production": float(district_production.iloc[-1])
                    },
                    "top_5_districts": district_production.head(5).to_dict(),
                    "year": int(latest_year)
                }
            
            # Crop-wise analysis
            crop_analysis = {}
            for crop in district_data['crop'].unique():
                crop_data = district_data[district_data['crop'] == crop]
                if not crop_data.empty:
                    latest_crop_data = crop_data[crop_data['crop_year'] == latest_year]
                    if not latest_crop_data.empty:
                        district_ranking = latest_crop_data.groupby('district')['total_production'].sum().sort_values(ascending=False)
                        
                        crop_analysis[crop] = {
                            "top_district": {
                                "name": district_ranking.index[0],
                                "production": float(district_ranking.iloc[0])
                            },
                            "bottom_district": {
                                "name": district_ranking.index[-1],
                                "production": float(district_ranking.iloc[-1])
                            }
                        }
            
            analysis["crop_analysis"] = crop_analysis
        
        return {"analysis": analysis}
    
    async def _analyze_policy(self, data: Dict, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data for policy recommendations"""
        crop_data = pd.DataFrame(data.get("crop_data", []))
        rainfall_data = pd.DataFrame(data.get("rainfall_data", []))
        
        analysis = {}
        
        if not crop_data.empty:
            # Analyze crop performance
            crop_performance = {}
            for crop in crop_data['crop'].unique():
                crop_info = crop_data[crop_data['crop'] == crop]
                
                # Calculate average production and area
                avg_production = crop_info['total_production'].mean()
                avg_area = crop_info['total_area'].mean()
                yield_per_hectare = avg_production / avg_area if avg_area > 0 else 0
                
                # Calculate production stability (coefficient of variation)
                production_cv = crop_info['total_production'].std() / avg_production if avg_production > 0 else 0
                
                crop_performance[crop] = {
                    "avg_production": float(avg_production),
                    "avg_area": float(avg_area),
                    "yield_per_hectare": float(yield_per_hectare),
                    "production_stability": float(1 - production_cv),  # Higher is more stable
                    "total_records": len(crop_info)
                }
            
            analysis["crop_performance"] = crop_performance
            
            # Identify drought-resistant vs water-intensive crops
            # This is a simplified classification - in reality, this would be based on agronomic data
            drought_resistant_crops = ["Bajra", "Jowar", "Arhar/Tur", "Moong"]
            water_intensive_crops = ["Rice", "Sugarcane"]
            
            analysis["crop_classification"] = {
                "drought_resistant": [crop for crop in drought_resistant_crops if crop in crop_performance],
                "water_intensive": [crop for crop in water_intensive_crops if crop in crop_performance]
            }
        
        if not rainfall_data.empty:
            # Analyze rainfall patterns
            rainfall_analysis = {
                "avg_annual_rainfall": float(rainfall_data['avg_rainfall'].mean()),
                "rainfall_variability": float(rainfall_data['avg_rainfall'].std()),
                "driest_months": rainfall_data.groupby('month')['avg_rainfall'].mean().nsmallest(3).to_dict(),
                "wettest_months": rainfall_data.groupby('month')['avg_rainfall'].mean().nlargest(3).to_dict()
            }
            analysis["rainfall_patterns"] = rainfall_analysis
        
        return {"analysis": analysis}
    
    async def _analyze_general(self, data: Dict, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze general data"""
        crop_data = pd.DataFrame(data.get("crop_data", []))
        rainfall_data = pd.DataFrame(data.get("rainfall_data", []))
        
        analysis = {}
        
        if not crop_data.empty:
            analysis["crop_summary"] = {
                "total_crops": crop_data['crop'].nunique(),
                "total_districts": crop_data['district'].nunique(),
                "year_range": {
                    "min": int(crop_data['crop_year'].min()),
                    "max": int(crop_data['crop_year'].max())
                },
                "top_crops": crop_data.groupby('crop')['total_production'].sum().nlargest(5).to_dict()
            }
        
        if not rainfall_data.empty:
            analysis["rainfall_summary"] = {
                "total_districts": rainfall_data['district'].nunique(),
                "year_range": {
                    "min": int(rainfall_data['year'].min()),
                    "max": int(rainfall_data['year'].max())
                },
                "avg_rainfall": float(rainfall_data['avg_rainfall'].mean())
            }
        
        return {"analysis": analysis}
    
    async def _calculate_crop_rainfall_correlation(self, crop_data: pd.DataFrame, rainfall_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate correlation between crop production and rainfall"""
        correlations = {}
        
        # Group data by year for correlation analysis
        crop_yearly = crop_data.groupby(['crop_year', 'crop'])['total_production'].sum().reset_index()
        rainfall_yearly = rainfall_data.groupby('year')['avg_rainfall'].mean().reset_index()
        
        # Merge datasets
        merged_data = pd.merge(
            crop_yearly, 
            rainfall_yearly, 
            left_on='crop_year', 
            right_on='year', 
            how='inner'
        )
        
        if not merged_data.empty:
            for crop in merged_data['crop'].unique():
                crop_data_subset = merged_data[merged_data['crop'] == crop]
                if len(crop_data_subset) > 2:  # Need at least 3 points for correlation
                    correlation, p_value = stats.pearsonr(
                        crop_data_subset['total_production'], 
                        crop_data_subset['avg_rainfall']
                    )
                    
                    correlations[crop] = {
                        "correlation": float(correlation),
                        "p_value": float(p_value),
                        "strength": "strong" if abs(correlation) > 0.7 else "moderate" if abs(correlation) > 0.3 else "weak",
                        "direction": "positive" if correlation > 0 else "negative"
                    }
        
        return correlations
