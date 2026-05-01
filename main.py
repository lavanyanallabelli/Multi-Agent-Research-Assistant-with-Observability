from openai import OpenAI
from config.settings import OPENAI_API_KEY, TAVILY_API_KEY

print(f"OpenAI key loaded: {bool(OPENAI_API_KEY)}")
print(f"Tavily key loaded: {bool(TAVILY_API_KEY)}")