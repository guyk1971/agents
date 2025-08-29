import requests
import os 
from dotenv import load_dotenv

# Robust import that works in different contexts
try:
    from .api import oai
except ImportError:
    # Fallback for when running as standalone module
    try:
        from api import oai
    except ImportError:
        # Last resort - add current directory to path
        import sys
        from pathlib import Path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        from api import oai

load_dotenv('.env')

# the below code was borrowed from https://gitlab-master.nvidia.com/atlas/endpoints.git

MODEL_NAME_TO_ID={'clds35':'claude-3-5-sonnet-20241022','clds37':'claude-3-7-sonnet-20250219','clds4':'claude-sonnet-4-20250514','cldo4':'claude-opus-4-20250514','gpt-4o':'gpt-4o-20241120','gpt-4o-mini':'gpt-4o-mini-20240718','gpt-4-turbo':'gpt-4-turbo-20240409','o1-preview':'o1-preview-20240912','o1-mini':'o1-mini-20240912','o1':'o1-20241217',
                   'o3mini':'o3-mini-20250131','llama3.3':'nvdev/meta/llama-3.3-70b-instruct','dsr1':'nvdev/deepseek-ai/deepseek-r1'}
API_VERSION='2024-12-01-preview'

class Frontier(oai.Azure):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        Please get the API key and supported model list from https://confluence.nvidia.com/pages/viewpage.action?spaceKey=PERFLABGRP&title=Perflab+OneAPI
        """
        super().__init__(
            azure_endpoint="https://llm-proxy.perflab.nvidia.com",
            api_version=API_VERSION,
            api_key=api_key,
            model=model,
        )

    def validate(self, system_prompt: str, user_message: str):
        if "o1" in self.model:
            assert (
                not system_prompt
            ), f'O1 requires system prompt to be None or empty but got "{system_prompt}"'
        return True


def ask_frontier_llm(system_prompt,user_message, model_id):
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    frontier = Frontier(api_key=api_key, model=model_id)
    try:
        frontier_response = frontier.query(system_prompt, user_message)
    except Exception as e:
        print("Failed on frontier single response")
        frontier_response = "failed to get frontier response"
    return frontier_response




class Nim(oai.Endpoint):
    """
    Please see https://nvidia.sharepoint.com/sites/nvbuild/SitePages/Endpoints-for-Internal-Development-Use.aspx for model choices and API key setup.
    """
    def __init__(self, api_key: str, model: str = 'nvdev/meta/llama-3.3-70b-instruct'):
        super().__init__('https://integrate.api.nvidia.com/v1', api_key, model)


def ask_nim_llm(system_prompt,user_message, model_id):
    # assert model_name in nim_model_map, f"Unsupported model: {model_name}"
    api_key = os.getenv("NEMO_API_KEY")
    nim = Nim(api_key=api_key, model=model_id)

    try:
        nim_response = nim.query(system_prompt, user_message,top_p=1, temperature=0.3, max_tokens=4096)
    except Exception as e:
        print("Failed on nim single response")
        nim_response = "failed to get nim response"

    return nim_response
