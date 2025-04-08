"OpenAI model response class AND LangGraph Chat model instance"
import logging
import time
from typing import Any, Dict, Tuple, Optional, List, Callable
import tenacity
from openai import AsyncOpenAI
from langgraph.graph import END
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from app.config.env_config import env_config
import inspect
logging.basicConfig(level=logging.INFO)

MODEL_PRICING = {
    "gpt-4o-mini": {"prompt_per_million": 0.15,"completion_per_million": 0.6, "cached_per_million": 0.075},
    "o3-mini": {"prompt_per_million": 1.10,"completion_per_million": 4.40},
    }

class OpenAIClient:
    "OpenAI structured model response class with client already exisiting inside the class"
    def __init__(self):
        self.api_key = env_config.ai.openai_key
        self._client = None

    @property
    def client(self) -> AsyncOpenAI:
        "OpenAI client instance"
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client
    
    def _extract_token_usage(self, response: Any) -> Dict:
        return {"prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens}
    
    def _calculate_cost(self, token_usage: Dict, model: str) -> Dict:
        model_rates = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o-mini"])
        prompt_cost = (token_usage["prompt_tokens"]/1000000)*model_rates["prompt_per_million"]
        completion_cost = (token_usage["completion_tokens"]/1000000)*model_rates["completion_per_million"]
        return {"prompt_cost": prompt_cost, "completion_cost": completion_cost,
                "total_cost": prompt_cost+completion_cost}
    
    @tenacity.retry(
    retry=tenacity.retry_if_exception_type((TimeoutError, ConnectionError)), wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    stop=tenacity.stop_after_attempt(3), before_sleep=lambda retry_state: logging.warning("Retrying API call after error: %s", retry_state.outcome.exception()))
    async def openai_model_response(self, system_prompt: str, user_prompt: str, response_format: BaseModel, model: str = "gpt-4o-mini") -> Tuple[str, Dict, Dict]:
        "OpenAI Completion function for structured ouput, return models response, token usage, cost"
        try: 
            start_time = time.time()
            params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},{"role": "user", "content": user_prompt}
                ], "response_format": response_format
            }

            response = await self.client.beta.chat.completions.parse(**params)
            execution_time = time.time() - start_time
            logging.info("OpenAI completion generated in %.2fs.", execution_time)

            token_usage = self._extract_token_usage(response)
            cost = self._calculate_cost(token_usage,model)
            content = response.choices[0].message.content
            logging.info("Generated Model Response: %s", content[:35])
            
            return content, token_usage, cost
        except Exception as e:
            logging.error("Error generating OpenAI completion: %s", {str(e)})
            raise
        
class LangGraphClient:
    "LangGraph Chat model instance"
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0):
        self.model_name = model_name
        self.temperature = temperature
        self.llm = ChatOpenAI(model=self.model_name)

    def create_assistant(self, tools: Optional[List[Callable]] = None, response_format: Optional[BaseModel] = None):
        """Create an assistant with tools and response format"""
        logging.info("===== CREATING ASSISTANT =====")
        logging.info("Tools being registered:")
        if tools is not None:
            for tool in tools:
                logging.info("- Tool name: %s", tool.__name__)
                logging.info("  Signature: %s", inspect.signature(tool))
        configured_llm = self.llm
        if tools:
            configured_llm = configured_llm.bind_tools(tools)
        if response_format:
            configured_llm = configured_llm.with_structured_output(response_format, include_raw=True)
        return configured_llm
    
    def create_tool_condition(self, tool_name: str) -> Callable:
        """Create a tool condition"""
        def tool_condition(state: BaseModel):
            last_message = state["messages"][-1]
            if last_message.tool_calls:
                return tool_name
            return END
        return tool_condition
    
    def total_token_cost_calculator(self, token_usage: Dict) -> Dict:
        try:
            logging.info("Calculating total token cost")
            model_rates = MODEL_PRICING["gpt-4o-mini"]
            total_token_usage = token_usage['total_tokens'] + token_usage['input_token_details']['cache_read']
            cost = (token_usage['input_tokens']/1000000)*model_rates['prompt_per_million'] + (token_usage['output_tokens']/1000000)*model_rates['completion_per_million'] + (token_usage['input_token_details']['cache_read']/1000000)*model_rates['cached_per_million']
            return {"token_usage": total_token_usage, "cost": cost}
        except Exception as e:
            logging.error("Error calculating total token cost: %s", {str(e)})
            return {"token_usage": 0, "cost": 0}

