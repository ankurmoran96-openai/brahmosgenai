from openai import AsyncOpenAI
from config import API_BASE_URL, API_KEY, DEFAULT_MODEL
from database import get_history, add_message

client = AsyncOpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL
)

async def get_chat_response(user_id, prompt):
    add_message(user_id, "user", prompt)
    history = get_history(user_id, limit=10)
    
    messages = [{"role": "system", "content": "You are BrahMos GenAI, an advanced AI assistant."}]
    messages.extend(history)
    
    try:
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages
        )
        reply = response.choices[0].message.content
        add_message(user_id, "assistant", reply)
        return reply
    except Exception as e:
        return f"Error connecting to API: {e}"

async def get_models():
    try:
        response = await client.models.list()
        return [model.id for model in response.data]
    except Exception as e:
        print(e)
        return []
