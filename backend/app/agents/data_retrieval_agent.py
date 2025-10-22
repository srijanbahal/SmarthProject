# from .base_agent import BaseAgent
# from sqlalchemy.orm import Session
# from sqlalchemy import text
# from typing import Dict, List, Any
# import logging
# import pandas as pd

# logger = logging.getLogger(__name__)

# class DataRetrievalAgent(BaseAgent):
#     def __init__(self, db: Session):
#         super().__init__("DataRetrievalAgent")
#         self.db = db
    
#     async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
#         """Generate SQL queries and retrieve data based on extracted entities"""
#         entities = input_data.get("extracted_entities", {})
#         query_type = entities.get("query_type", "general")
        
#         try:
#             if query_type == "comparison":
#                 result = await self._handle_comparison_query(entities)
#             elif query_type == "trend_analysis":
#                 result = await self._handle_trend_query(entities)
#             elif query_type == "district_comparison":
#                 result = await self._handle_district_query(entities)
#             elif query_type == "policy_recommendation":
#                 result = await self._handle_policy_query(entities)
#             else:
#                 result = await self._handle_general_query(entities)
            
#             result["agent"] = self.name
#             result["status"] = "success"
#             return result
            
#         except Exception as e:
#             logger.error(f"Error in data retrieval: {e}")
#             return {
#                 "agent": self.name,
#                 "status": "error",
#                 "error": str(e),
#                 "data": [],
#                 "sources": []
#             }
    
#     async def _handle_comparison_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
#         """Handle comparison queries (rainfall + crops)"""
#         states = entities.get("states", ["Uttar Pradesh"])
#         crops = entities.get("crops", [])
#         years = entities.get("years", [])
        
#         # # Get rainfall data
#         # rainfall_query = """
#         # SELECT state, district, year, AVG(avg_rainfall) as avg_rainfall, 
#         #        source_url, COUNT(*) as record_count
#         # FROM rainfall 
#         # WHERE state IN :states
#         # """
#         # params = {"states": tuple(states)}
#         placeholders = ", ".join(["?"] * len(states))
#         rainfall_query = f"""
#         SELECT state, district, year, AVG(avg_rainfall) as avg_rainfall, 
#             source_url, COUNT(*) as record_count
#         FROM rainfall 
#         WHERE state IN ({placeholders})
#         """
#         params = states
        
#         if years:
#             rainfall_query += " AND year IN :years"
#             params["years"] = tuple(years)
        
#         rainfall_query += " GROUP BY state, district, year ORDER BY year DESC"
        
#         # rainfall_data = pd.read_sql(rainfall_query, self.db.bind, params=(params,))
#         rainfall_data = pd.read_sql(rainfall_query, self.db.bind, params=(params,))

        
#         # Get crop data
#         crop_query = """
#         SELECT state, district, crop_year, season, crop, 
#                SUM(area) as total_area, SUM(production) as total_production,
#                source_url, COUNT(*) as record_count
#         FROM crop_production 
#         WHERE state IN :states
#         """
        
#         if crops:
#             crop_query += " AND crop IN :crops"
#             params["crops"] = tuple(crops)
        
#         if years:
#             crop_query += " AND crop_year IN :years"
        
#         crop_query += " GROUP BY state, district, crop_year, season, crop ORDER BY total_production DESC"
        
#         crop_data = pd.read_sql(crop_query, self.db.bind, params=(params,))
        
#         # Get unique sources
#         sources = list(set(rainfall_data['source_url'].tolist() + crop_data['source_url'].tolist()))
        
#         return {
#             "data": {
#                 "rainfall": rainfall_data.to_dict('records'),
#                 "crops": crop_data.to_dict('records')
#             },
#             "sources": sources,
#             "query_type": "comparison"
#         }
    
#     async def _handle_trend_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
#         """Handle trend analysis queries"""
#         states = entities.get("states", ["Uttar Pradesh"])
#         crops = entities.get("crops", [])
#         districts = entities.get("districts", [])
        
#         # Get crop production trends
#         crop_query = """
#         SELECT state, district, crop_year, crop, 
#                SUM(area) as total_area, SUM(production) as total_production,
#                source_url
#         FROM crop_production 
#         WHERE state IN :states
#         """
#         params = {"states": tuple(states)}
        
#         if crops:
#             crop_query += " AND crop IN :crops"
#             params["crops"] = tuple(crops)
        
#         if districts:
#             crop_query += " AND district IN :districts"
#             params["districts"] = tuple(districts)
        
#         crop_query += " GROUP BY state, district, crop_year, crop ORDER BY crop_year DESC"
        
#         crop_data = pd.read_sql(crop_query, self.db.bind, params=(params,))
        
#         # Get rainfall trends
#         rainfall_query = """
#         SELECT state, district, year, AVG(avg_rainfall) as avg_rainfall,
#                source_url
#         FROM rainfall 
#         WHERE state IN :states
#         """
        
#         if districts:
#             rainfall_query += " AND district IN :districts"
        
#         rainfall_query += " GROUP BY state, district, year ORDER BY year DESC"
        
#         rainfall_data = pd.read_sql(rainfall_query, self.db.bind, params=(params,))
        
#         sources = list(set(rainfall_data['source_url'].tolist() + crop_data['source_url'].tolist()))
        
#         return {
#             "data": {
#                 "crop_trends": crop_data.to_dict('records'),
#                 "rainfall_trends": rainfall_data.to_dict('records')
#             },
#             "sources": sources,
#             "query_type": "trend_analysis"
#         }
    
#     async def _handle_district_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
#         """Handle district-level comparison queries"""
#         states = entities.get("states", ["Uttar Pradesh"])
#         crops = entities.get("crops", [])
        
#         # Get district-wise crop production
#         query = """
#         SELECT state, district, crop_year, crop,
#                SUM(area) as total_area, SUM(production) as total_production,
#                source_url
#         FROM crop_production 
#         WHERE state IN :states
#         """
#         params = {"states": tuple(states)}
        
#         if crops:
#             query += " AND crop IN :crops"
#             params["crops"] = tuple(crops)
        
#         query += " GROUP BY state, district, crop_year, crop ORDER BY total_production DESC"
        
#         data = pd.read_sql(query, self.db.bind, params=(params,))
#         sources = list(set(data['source_url'].tolist()))
        
#         return {
#             "data": {
#                 "district_production": data.to_dict('records')
#             },
#             "sources": sources,
#             "query_type": "district_comparison"
#         }
    
#     async def _handle_policy_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
#         """Handle policy recommendation queries"""
#         # This would typically involve more complex analysis
#         # For now, return comprehensive data for policy analysis
#         states = entities.get("states", ["Uttar Pradesh"])
        
#         # Get comprehensive crop and climate data
#         crop_query = """
#         SELECT state, district, crop_year, season, crop,
#                SUM(area) as total_area, SUM(production) as total_production,
#                source_url
#         FROM crop_production 
#         WHERE state IN :states
#         GROUP BY state, district, crop_year, season, crop
#         ORDER BY crop_year DESC, total_production DESC
#         """
        
#         rainfall_query = """
#         SELECT state, district, year, month, AVG(avg_rainfall) as avg_rainfall,
#                source_url
#         FROM rainfall 
#         WHERE state IN :states
#         GROUP BY state, district, year, month
#         ORDER BY year DESC, month DESC
#         """
        
#         params = {"states": tuple(states)}
        
#         crop_data = pd.read_sql(crop_query, self.db.bind, params=(params,))
#         rainfall_data = pd.read_sql(rainfall_query, self.db.bind, params=(params,))
        
#         sources = list(set(rainfall_data['source_url'].tolist() + crop_data['source_url'].tolist()))
        
#         return {
#             "data": {
#                 "crop_data": crop_data.to_dict('records'),
#                 "rainfall_data": rainfall_data.to_dict('records')
#             },
#             "sources": sources,
#             "query_type": "policy_recommendation"
#         }
    
#     async def _handle_general_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
#         """Handle general queries"""
#         states = entities.get("states", ["Uttar Pradesh"])
        
#         # Get basic crop and rainfall data
#         crop_query = """
#         SELECT state, district, crop_year, crop,
#                SUM(area) as total_area, SUM(production) as total_production,
#                source_url
#         FROM crop_production 
#         WHERE state IN :states
#         GROUP BY state, district, crop_year, crop
#         ORDER BY total_production DESC
#         LIMIT 100
#         """
        
#         rainfall_query = """
#         SELECT state, district, year, AVG(avg_rainfall) as avg_rainfall,
#                source_url
#         FROM rainfall 
#         WHERE state IN :states
#         GROUP BY state, district, year
#         ORDER BY year DESC
#         LIMIT 100
#         """
        
#         params = {"states": tuple(states)}
        
#         crop_data = pd.read_sql(crop_query, self.db.bind, params=(params,))
#         rainfall_data = pd.read_sql(rainfall_query, self.db.bind, params=(params,))
        
#         sources = list(set(rainfall_data['source_url'].tolist() + crop_data['source_url'].tolist()))
        
#         return {
#             "data": {
#                 "crop_data": crop_data.to_dict('records'),
#                 "rainfall_data": rainfall_data.to_dict('records')
#             },
#             "sources": sources,
#             "query_type": "general"
#         }

from .base_agent import BaseAgent
from sqlalchemy.orm import Session
from typing import Dict, List, Any
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class DataRetrievalAgent(BaseAgent):
    def __init__(self, db: Session):
        super().__init__("DataRetrievalAgent")
        self.db = db

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL queries and retrieve data based on extracted entities"""
        entities = input_data.get("extracted_entities", {})
        query_type = entities.get("query_type", "general")
        states = entities.get("states", ["Uttar Pradesh"])

        # Guard clause: only allow Uttar Pradesh
        if any(state != "Uttar Pradesh" for state in states):
            logger.warning(f"Data retrieval aborted: invalid states {states}")
            return {
                "agent": self.name,
                "status": "error",
                "error": "Data retrieval is restricted to Uttar Pradesh only.",
                "data": [],
                "sources": []
            }

        try:
            if query_type == "comparison":
                result = await self._handle_comparison_query()
            elif query_type == "trend_analysis":
                result = await self._handle_trend_query()
            elif query_type == "district_comparison":
                result = await self._handle_district_query()
            elif query_type == "policy_recommendation":
                result = await self._handle_policy_query()
            else:
                result = await self._handle_general_query()

            result["agent"] = self.name
            result["status"] = "success"
            return result

        except Exception as e:
            logger.error(f"Error in data retrieval: {e}")
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "data": [],
                "sources": []
            }

    # ----------------------------- Query Handlers -----------------------------

    async def _handle_comparison_query(self) -> Dict[str, Any]:
        """Handle comparison queries (rainfall + crops)"""
        # Rainfall data
        rainfall_query = """
            SELECT state, district, year, AVG(avg_rainfall) AS avg_rainfall,
                   source_url, COUNT(*) AS record_count
            FROM rainfall
            WHERE state = 'Uttar Pradesh'
            GROUP BY state, district, year
            ORDER BY year DESC
        """
        rainfall_data = pd.read_sql(rainfall_query, self.db.bind)

        # Crop data
        crop_query = """
            SELECT state, district, crop_year, season, crop,
                   SUM(area) AS total_area, SUM(production) AS total_production,
                   source_url, COUNT(*) AS record_count
            FROM crop_production
            WHERE state = 'Uttar Pradesh'
            GROUP BY state, district, crop_year, season, crop
            ORDER BY total_production DESC
        """
        crop_data = pd.read_sql(crop_query, self.db.bind)

        sources = list(set(rainfall_data['source_url'].tolist() + crop_data['source_url'].tolist()))
        return {
            "data": {"rainfall": rainfall_data.to_dict('records'),
                     "crops": crop_data.to_dict('records')},
            "sources": sources,
            "query_type": "comparison"
        }

    async def _handle_trend_query(self) -> Dict[str, Any]:
        """Handle trend analysis queries"""
        crop_query = """
            SELECT state, district, crop_year, crop,
                   SUM(area) AS total_area, SUM(production) AS total_production,
                   source_url
            FROM crop_production
            WHERE state = 'Uttar Pradesh'
            GROUP BY state, district, crop_year, crop
            ORDER BY crop_year DESC
        """
        crop_data = pd.read_sql(crop_query, self.db.bind)

        rainfall_query = """
            SELECT state, district, year, AVG(avg_rainfall) AS avg_rainfall,
                   source_url
            FROM rainfall
            WHERE state = 'Uttar Pradesh'
            GROUP BY state, district, year
            ORDER BY year DESC
        """
        rainfall_data = pd.read_sql(rainfall_query, self.db.bind)

        sources = list(set(rainfall_data['source_url'].tolist() + crop_data['source_url'].tolist()))
        return {
            "data": {"crop_trends": crop_data.to_dict('records'),
                     "rainfall_trends": rainfall_data.to_dict('records')},
            "sources": sources,
            "query_type": "trend_analysis"
        }

    async def _handle_district_query(self) -> Dict[str, Any]:
        """Handle district-level comparison queries"""
        query = """
            SELECT state, district, crop_year, crop,
                   SUM(area) AS total_area, SUM(production) AS total_production,
                   source_url
            FROM crop_production
            WHERE state = 'Uttar Pradesh'
            GROUP BY state, district, crop_year, crop
            ORDER BY total_production DESC
        """
        data = pd.read_sql(query, self.db.bind)
        sources = list(set(data['source_url'].tolist()))
        return {
            "data": {"district_production": data.to_dict('records')},
            "sources": sources,
            "query_type": "district_comparison"
        }

    async def _handle_policy_query(self) -> Dict[str, Any]:
        """Handle policy recommendation queries"""
        crop_query = """
            SELECT state, district, crop_year, season, crop,
                   SUM(area) AS total_area, SUM(production) AS total_production,
                   source_url
            FROM crop_production
            WHERE state = 'Uttar Pradesh'
            GROUP BY state, district, crop_year, season, crop
            ORDER BY crop_year DESC, total_production DESC
        """
        crop_data = pd.read_sql(crop_query, self.db.bind)

        rainfall_query = """
            SELECT state, district, year, month, AVG(avg_rainfall) AS avg_rainfall,
                   source_url
            FROM rainfall
            WHERE state = 'Uttar Pradesh'
            GROUP BY state, district, year, month
            ORDER BY year DESC, month DESC
        """
        rainfall_data = pd.read_sql(rainfall_query, self.db.bind)

        sources = list(set(rainfall_data['source_url'].tolist() + crop_data['source_url'].tolist()))
        return {
            "data": {"crop_data": crop_data.to_dict('records'),
                     "rainfall_data": rainfall_data.to_dict('records')},
            "sources": sources,
            "query_type": "policy_recommendation"
        }

    async def _handle_general_query(self) -> Dict[str, Any]:
        """Handle general queries"""
        crop_query = """
            SELECT state, district, crop_year, crop,
                   SUM(area) AS total_area, SUM(production) AS total_production,
                   source_url
            FROM crop_production
            WHERE state = 'Uttar Pradesh'
            GROUP BY state, district, crop_year, crop
            ORDER BY total_production DESC
            LIMIT 100
        """
        crop_data = pd.read_sql(crop_query, self.db.bind)

        rainfall_query = """
            SELECT state, district, year, AVG(avg_rainfall) AS avg_rainfall,
                   source_url
            FROM rainfall
            WHERE state = 'Uttar Pradesh'
            GROUP BY state, district, year
            ORDER BY year DESC
            LIMIT 100
        """
        rainfall_data = pd.read_sql(rainfall_query, self.db.bind)

        sources = list(set(rainfall_data['source_url'].tolist() + crop_data['source_url'].tolist()))
        return {
            "data": {"crop_data": crop_data.to_dict('records'),
                     "rainfall_data": rainfall_data.to_dict('records')},
            "sources": sources,
            "query_type": "general"
        }


