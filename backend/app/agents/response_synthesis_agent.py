from .base_agent import BaseAgent
from typing import Dict, List, Any
import logging
import json

logger = logging.getLogger(__name__)

class ResponseSynthesisAgent(BaseAgent):
    def __init__(self):
        super().__init__("ResponseSynthesisAgent")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize final response with citations"""
        original_question = input_data.get("original_question", "")
        extracted_entities = input_data.get("extracted_entities", {})
        data = input_data.get("data", {})
        analysis = input_data.get("analysis", {})
        visualizations = input_data.get("visualizations", [])
        sources = input_data.get("sources", [])
        query_type = input_data.get("query_type", "general")
        
        try:
            # Generate natural language response
            response = await self._generate_response(
                original_question, 
                extracted_entities, 
                analysis, 
                query_type
            )
            
            # Format citations
            citations = self._format_citations(sources)
            
            # Create summary
            summary = self._create_summary(analysis, query_type)
            
            result = {
                "agent": self.name,
                "status": "success",
                "response": response,
                "summary": summary,
                "citations": citations,
                "visualizations": visualizations,
                "raw_data": data,
                "confidence_score": self._calculate_confidence(analysis, data)
            }
            
            logger.info("Response synthesis completed")
            return result
            
        except Exception as e:
            logger.error(f"Error in response synthesis: {e}")
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "response": "I apologize, but I encountered an error while processing your question.",
                "citations": [],
                "visualizations": []
            }
    
    async def _generate_response(self, question: str, entities: Dict, analysis: Dict, query_type: str) -> str:
        """Generate natural language response using LLM"""
        
        # Prepare context for LLM
        context = self._prepare_context(entities, analysis, query_type)
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert agricultural analyst specializing in Uttar Pradesh data. 
                Provide clear, data-driven answers with specific numbers and insights.
                Always cite data sources and be precise about time periods and locations.
                Use professional but accessible language."""
            },
            {
                "role": "user",
                "content": f"""Question: {question}
                
                Context: {context}
                
                Please provide a comprehensive answer based on the data analysis above. 
                Include specific numbers, trends, and insights. Be sure to mention data sources and time periods."""
            }
        ]
        
        response = await self.call_llm(messages)
        return response
    
    def _prepare_context(self, entities: Dict, analysis: Dict, query_type: str) -> str:
        """Prepare context string for LLM"""
        context_parts = []
        
        # Add query type context
        context_parts.append(f"Query Type: {query_type}")
        
        # Add entity information
        if entities.get("states"):
            context_parts.append(f"States: {', '.join(entities['states'])}")
        if entities.get("crops"):
            context_parts.append(f"Crops: {', '.join(entities['crops'])}")
        if entities.get("districts"):
            context_parts.append(f"Districts: {', '.join(entities['districts'])}")
        if entities.get("years"):
            context_parts.append(f"Years: {', '.join(map(str, entities['years']))}")
        
        # Add analysis results
        if query_type == "comparison":
            if "rainfall" in analysis:
                rainfall_analysis = analysis["rainfall"]
                context_parts.append(f"Rainfall Analysis: {rainfall_analysis}")
            if "crops" in analysis:
                crop_analysis = analysis["crops"]
                context_parts.append(f"Crop Analysis: {crop_analysis}")
        
        elif query_type == "trend_analysis":
            if "crop_trends" in analysis:
                context_parts.append(f"Crop Trends: {analysis['crop_trends']}")
            if "rainfall_trends" in analysis:
                context_parts.append(f"Rainfall Trends: {analysis['rainfall_trends']}")
            if "correlations" in analysis:
                context_parts.append(f"Correlations: {analysis['correlations']}")
        
        elif query_type == "district_comparison":
            if "district_ranking" in analysis:
                context_parts.append(f"District Ranking: {analysis['district_ranking']}")
            if "crop_analysis" in analysis:
                context_parts.append(f"Crop Analysis: {analysis['crop_analysis']}")
        
        elif query_type == "policy_recommendation":
            if "crop_performance" in analysis:
                context_parts.append(f"Crop Performance: {analysis['crop_performance']}")
            if "rainfall_patterns" in analysis:
                context_parts.append(f"Rainfall Patterns: {analysis['rainfall_patterns']}")
            if "crop_classification" in analysis:
                context_parts.append(f"Crop Classification: {analysis['crop_classification']}")
        
        return "\n".join(context_parts)
    
    def _format_citations(self, sources: List[str]) -> List[Dict[str, str]]:
        """Format data source citations"""
        citations = []
        
        for i, source in enumerate(sources, 1):
            citation = {
                "id": f"[{i}]",
                "url": source,
                "description": self._get_source_description(source),
                "access_date": "2024-01-01"  # In production, use actual access date
            }
            citations.append(citation)
        
        return citations
    
    def _get_source_description(self, source_url: str) -> str:
        """Get description for data source"""
        if "crop-production" in source_url:
            return "Ministry of Agriculture & Farmers Welfare - Crop Production Data"
        elif "rainfall" in source_url:
            return "India Meteorological Department - Rainfall Data"
        else:
            return "Government of India - Open Data Portal"
    
    def _create_summary(self, analysis: Dict, query_type: str) -> Dict[str, Any]:
        """Create summary of key findings"""
        summary = {
            "query_type": query_type,
            "key_findings": [],
            "data_quality": "good",
            "recommendations": []
        }
        
        if query_type == "comparison":
            if "rainfall" in analysis:
                rainfall = analysis["rainfall"]
                summary["key_findings"].append(f"Analyzed rainfall data for {rainfall.get('total_districts', 0)} districts")
                summary["key_findings"].append(f"Year range: {rainfall.get('year_range', {}).get('min', 'N/A')} - {rainfall.get('year_range', {}).get('max', 'N/A')}")
            
            if "crops" in analysis:
                crops = analysis["crops"]
                summary["key_findings"].append(f"Analyzed {crops.get('total_crops', 0)} different crops")
        
        elif query_type == "trend_analysis":
            if "crop_trends" in analysis:
                trends = analysis["crop_trends"]
                summary["key_findings"].append(f"Analyzed trends for {len(trends)} crops")
            
            if "correlations" in analysis:
                correlations = analysis["correlations"]
                strong_correlations = [crop for crop, data in correlations.items() if abs(data["correlation"]) > 0.7]
                if strong_correlations:
                    summary["key_findings"].append(f"Strong correlations found for: {', '.join(strong_correlations)}")
        
        elif query_type == "district_comparison":
            if "district_ranking" in analysis:
                ranking = analysis["district_ranking"]
                summary["key_findings"].append(f"Highest producing district: {ranking.get('highest_production', {}).get('district', 'N/A')}")
                summary["key_findings"].append(f"Lowest producing district: {ranking.get('lowest_production', {}).get('district', 'N/A')}")
        
        elif query_type == "policy_recommendation":
            if "crop_classification" in analysis:
                classification = analysis["crop_classification"]
                drought_resistant = classification.get("drought_resistant", [])
                water_intensive = classification.get("water_intensive", [])
                
                if drought_resistant:
                    summary["recommendations"].append(f"Consider promoting drought-resistant crops: {', '.join(drought_resistant)}")
                if water_intensive:
                    summary["recommendations"].append(f"Monitor water-intensive crops: {', '.join(water_intensive)}")
        
        return summary
    
    def _calculate_confidence(self, analysis: Dict, data: Dict) -> float:
        """Calculate confidence score for the analysis"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on data availability
        if data:
            confidence += 0.2
        
        # Increase confidence based on analysis completeness
        if analysis:
            confidence += 0.2
        
        # Increase confidence if we have multiple data sources
        if len(data) > 1:
            confidence += 0.1
        
        return min(confidence, 1.0)
