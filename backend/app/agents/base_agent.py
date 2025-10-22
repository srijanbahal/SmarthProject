from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from groq import Groq
import json
import logging
import os
import httpx

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, name: str, model: str = "llama-3.3-70b-versatile"):
        self.name = name
        self.model = model
        # self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        # 1. Create an httpx client with proxies explicitly set to None
        http_client = httpx.Client(proxies=None)
        
        # 2. Pass this client to Groq
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY"),
            http_client=http_client
        )
        logger.info("base Agent Constructor here hai !!!!!!!!!!!!!!!!!!!")
        self.conversation_history = []
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return output"""
        pass
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})
    
    async def call_llm(self, messages: List[Dict], tools: Optional[List[Dict]] = None) -> str:
        """Call Groq LLM with messages and optional tools"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto" if tools else "none",
                temperature=0.1
            )
            
            message = response.choices[0].message
            return message.content or ""
            
        except Exception as e:
            logger.error(f"Error calling LLM in {self.name}: {e}")
            return f"Error processing request: {str(e)}"
    
    def extract_tool_calls(self, response) -> List[Dict]:
        """Extract tool calls from LLM response"""
        if hasattr(response, 'tool_calls') and response.tool_calls:
            return [
                {
                    "id": call.id,
                    "type": call.type,
                    "function": {
                        "name": call.function.name,
                        "arguments": json.loads(call.function.arguments)
                    }
                }
                for call in response.tool_calls
            ]
        return []
