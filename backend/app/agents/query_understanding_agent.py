from .base_agent import BaseAgent
from typing import Dict, List, Any
import json
import logging

logger = logging.getLogger(__name__)

class QueryUnderstandingAgent(BaseAgent):
    def __init__(self):
        super().__init__("QueryUnderstandingAgent")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse user question and extract entities"""
        user_question = input_data.get("question", "")
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "extract_query_entities",
                    "description": "Extract entities and parameters from agricultural/climate questions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query_type": {
                                "type": "string",
                                "enum": ["comparison", "trend_analysis", "district_comparison", "policy_recommendation", "general"],
                                "description": "Type of query being asked"
                            },
                            "states": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "States mentioned in the question"
                            },
                            "districts": {
                                "type": "array", 
                                "items": {"type": "string"},
                                "description": "Districts mentioned in the question"
                            },
                            "crops": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Crops mentioned in the question"
                            },
                            "crop_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Crop types/categories mentioned"
                            },
                            "years": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "Years mentioned in the question"
                            },
                            "time_period": {
                                "type": "string",
                                "description": "Time period mentioned (e.g., 'last 5 years', 'decade')"
                            },
                            "metrics": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Metrics to analyze (production, rainfall, area, etc.)"
                            },
                            "analysis_type": {
                                "type": "string",
                                "description": "Type of analysis requested (correlation, comparison, trend, etc.)"
                            },
                            "geographic_region": {
                                "type": "string",
                                "description": "Geographic region mentioned"
                            }
                        },
                        "required": ["query_type"]
                    }
                }
            }
        ]
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert at understanding agricultural and climate data questions. 
                Extract entities and parameters from user questions about crop production, rainfall, and agricultural analysis.
                Focus on Uttar Pradesh data unless other states are specifically mentioned.
                
                Common crop types in UP: Rice, Wheat, Sugarcane, Maize, Bajra, Arhar/Tur, Moong, Groundnut, etc.
                Common districts in UP: Agra, Lucknow, Kanpur, Varanasi, Allahabad, Meerut, etc.
                Common metrics: production (tonnes), area (hectares), rainfall (mm), yield
                Common analysis types: comparison, correlation, trend analysis, ranking, policy recommendation"""
            },
            {
                "role": "user", 
                "content": f"Extract entities from this question: {user_question}"
            }
        ]
        
        try:
            response = await self.call_llm(messages, tools)
            
            # Parse the response to extract structured data
            # For now, we'll do basic parsing - in production, use proper tool calling
            entities = self._parse_entities_from_response(user_question, response)
            
            result = {
                "original_question": user_question,
                "extracted_entities": entities,
                "agent": self.name,
                "status": "success"
            }
            
            logger.info(f"Query understanding completed: {entities}")
            return result
            
        except Exception as e:
            logger.error(f"Error in query understanding: {e}")
            return {
                "original_question": user_question,
                "extracted_entities": {},
                "agent": self.name,
                "status": "error",
                "error": str(e)
            }
    
    def _parse_entities_from_response(self, question: str, response: str) -> Dict[str, Any]:
        """Parse entities from LLM response"""
        # Basic entity extraction - in production, use proper tool calling
        entities = {
            "query_type": "general",
            "states": [],
            "districts": [],
            "crops": [],
            "crop_types": [],
            "years": [],
            "time_period": "",
            "metrics": [],
            "analysis_type": "",
            "geographic_region": ""
        }
        
        question_lower = question.lower()
        
        # Determine query type
        if any(word in question_lower for word in ["compare", "comparison", "vs", "versus"]):
            entities["query_type"] = "comparison"
        elif any(word in question_lower for word in ["trend", "over time", "decade", "years"]):
            entities["query_type"] = "trend_analysis"
        elif any(word in question_lower for word in ["district", "highest", "lowest"]):
            entities["query_type"] = "district_comparison"
        elif any(word in question_lower for word in ["policy", "recommend", "scheme"]):
            entities["query_type"] = "policy_recommendation"
        
        # Extract states (default to UP if not specified)
        if "uttar pradesh" in question_lower or "up" in question_lower:
            entities["states"] = ["Uttar Pradesh"]
        else:
            entities["states"] = ["Uttar Pradesh"]  # Default to UP
        
        # Extract crops
        crop_keywords = ["rice", "wheat", "sugarcane", "maize", "bajra", "arhar", "tur", "moong", "groundnut", "onion"]
        for crop in crop_keywords:
            if crop in question_lower:
                entities["crops"].append(crop.title())
        
        # Extract districts
        district_keywords = ["agra", "lucknow", "kanpur", "varanasi", "allahabad", "meerut"]
        for district in district_keywords:
            if district in question_lower:
                entities["districts"].append(district.title())
        
        # Extract years
        import re
        years = re.findall(r'\b(19|20)\d{2}\b', question)
        entities["years"] = [int(year) for year in years]
        
        # Extract metrics
        if "production" in question_lower:
            entities["metrics"].append("production")
        if "rainfall" in question_lower:
            entities["metrics"].append("rainfall")
        if "area" in question_lower:
            entities["metrics"].append("area")
        
        return entities
