from typing import Dict, List, Any
import logging
from sqlalchemy.orm import Session

from .query_understanding_agent import QueryUnderstandingAgent
from .data_retrieval_agent import DataRetrievalAgent
from .analysis_agent import AnalysisAgent
from .visualization_agent import VisualizationAgent
from .response_synthesis_agent import ResponseSynthesisAgent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.query_agent = QueryUnderstandingAgent()
        self.data_agent = DataRetrievalAgent(db)
        self.analysis_agent = AnalysisAgent()
        self.viz_agent = VisualizationAgent()
        self.synthesis_agent = ResponseSynthesisAgent()
    
    async def process_query(self, question: str) -> Dict[str, Any]:
        """Process a user question through the complete agent pipeline"""
        try:
            logger.info(f"Processing query: {question}")
            
            # Step 1: Query Understanding
            logger.info("Step 1: Query Understanding")
            query_result = await self.query_agent.process({"question": question})
            
            if query_result["status"] != "success":
                return {
                    "status": "error",
                    "error": "Failed to understand query",
                    "details": query_result.get("error", "Unknown error")
                }
            
            extracted_entities = query_result["extracted_entities"]
            
            # Step 2: Data Retrieval
            logger.info("Step 2: Data Retrieval")
            data_result = await self.data_agent.process({
                "extracted_entities": extracted_entities,
                "original_question": question
            })
            
            if data_result["status"] != "success":
                return {
                    "status": "error",
                    "error": "Failed to retrieve data",
                    "details": data_result.get("error", "Unknown error")
                }
            
            # Step 3: Analysis
            logger.info("Step 3: Data Analysis")
            analysis_result = await self.analysis_agent.process({
                "data": data_result["data"],
                "extracted_entities": extracted_entities,
                "query_type": data_result.get("query_type", "general")
            })
            
            if analysis_result["status"] != "success":
                return {
                    "status": "error",
                    "error": "Failed to analyze data",
                    "details": analysis_result.get("error", "Unknown error")
                }
            
            # Step 4: Visualization
            logger.info("Step 4: Visualization Generation")
            viz_result = await self.viz_agent.process({
                "data": data_result["data"],
                "analysis": analysis_result["analysis"],
                "query_type": data_result.get("query_type", "general")
            })
            
            if viz_result["status"] != "success":
                logger.warning(f"Visualization failed: {viz_result.get('error', 'Unknown error')}")
                viz_result["visualizations"] = []
            
            # Step 5: Response Synthesis
            logger.info("Step 5: Response Synthesis")
            synthesis_result = await self.synthesis_agent.process({
                "original_question": question,
                "extracted_entities": extracted_entities,
                "data": data_result["data"],
                "analysis": analysis_result["analysis"],
                "visualizations": viz_result.get("visualizations", []),
                "sources": data_result.get("sources", []),
                "query_type": data_result.get("query_type", "general")
            })
            
            if synthesis_result["status"] != "success":
                return {
                    "status": "error",
                    "error": "Failed to synthesize response",
                    "details": synthesis_result.get("error", "Unknown error")
                }
            
            # Compile final result
            final_result = {
                "status": "success",
                "question": question,
                "response": synthesis_result["response"],
                "summary": synthesis_result["summary"],
                "citations": synthesis_result["citations"],
                "visualizations": synthesis_result["visualizations"],
                "raw_data": synthesis_result["raw_data"],
                "confidence_score": synthesis_result["confidence_score"],
                "processing_steps": {
                    "query_understanding": query_result["status"],
                    "data_retrieval": data_result["status"],
                    "analysis": analysis_result["status"],
                    "visualization": viz_result["status"],
                    "synthesis": synthesis_result["status"]
                }
            }
            
            logger.info("Query processing completed successfully")
            return final_result
            
        except Exception as e:
            logger.error(f"Error in agent orchestration: {e}")
            return {
                "status": "error",
                "error": "System error during processing",
                "details": str(e)
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            "query_understanding": "active",
            "data_retrieval": "active",
            "analysis": "active",
            "visualization": "active",
            "synthesis": "active",
            "database_connection": "active" if self.db else "inactive"
        }
