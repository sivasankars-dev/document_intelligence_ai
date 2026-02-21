import json
from openai import OpenAI
from shared.config.settings import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)    

def run_extraction_llm(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    try:
        return json.loads(content)
    except:
        return []