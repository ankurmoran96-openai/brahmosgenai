import json
import logging
from openai import AsyncOpenAI
from config import API_BASE_URL, API_KEY, DEFAULT_MODEL
from database import get_history, add_message

client = AsyncOpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL
)

# Define the tools available to the LLM
tools = [
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generate an image based on a prompt. Use this when the user asks to draw, paint, or create an image.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "A detailed prompt describing the image to generate.",
                    }
                },
                "required": ["prompt"],
            },
        }
    }
]

async def generate_image(prompt: str) -> str:
    """Calls the image generation API and returns the image URL or an error message."""
    try:
        response = await client.images.generate(
            model="vertex/imagen-4.0-fast-generate-001", # You can change this based on allowed models
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        return response.data[0].url
    except Exception as e:
        logging.error(f"Image generation failed: {e}")
        return f"Error: Failed to generate image. {e}"

async def get_chat_response(user_id, prompt):
    add_message(user_id, "user", prompt)
    history = get_history(user_id, limit=10)
    
    system_prompt = (
        "You are BrahMos GenAI, an advanced autonomous AI assistant. "
        "You have access to tools. If the user asks for an image, USE the generate_image tool. "
        "Do NOT tell the user to use a command. You handle everything autonomously. "
        "When you generate an image, briefly describe it and present the link nicely."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    
    photo_url = None

    try:
        # First API call
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        # Check if a tool was called
        if message.tool_calls:
            messages.append(message) # Append the assistant's tool call message
            
            for tool_call in message.tool_calls:
                if tool_call.function.name == "generate_image":
                    args = json.loads(tool_call.function.arguments)
                    img_prompt = args.get("prompt")
                    
                    # Execute tool
                    url_or_error = await generate_image(img_prompt)
                    
                    if url_or_error.startswith("http"):
                        photo_url = url_or_error
                    
                    # Append tool result
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": url_or_error
                    })
            
            # Second API call to get the final conversational response
            second_response = await client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages
            )
            final_reply = second_response.choices[0].message.content
            add_message(user_id, "assistant", final_reply)
            return {"text": final_reply, "photo_url": photo_url}
        else:
            # Normal text response
            reply = message.content
            add_message(user_id, "assistant", reply)
            return {"text": reply, "photo_url": None}

    except Exception as e:
        logging.error(f"LLM API Error: {e}")
        return {"text": f"Error connecting to API: {e}", "photo_url": None}

async def get_models():
    try:
        response = await client.models.list()
        return [model.id for model in response.data]
    except Exception as e:
        print(e)
        return []
