"""
LLMs are the brains or intelligence of AI agents and applications.

## Working with LLMs
- LLMs are stateless. Each time you invoke an LLM (whether through an API or locally), it has no memory of previous interactions.
- To build AI agents from scratch, we have to implement memory, tools, and the agent loop ourselves.

## Working with APIs
- You can call API endpoints directly using the requests or httpx libraries for example.
- However, it's convenient to use an SDK (software development kit) when available. SDKs handle authentication, error handling, and other boilerplate code for you.
- The examples in this tutorial use the Google Gemini Python SDK but the same concepts apply to any LLM provider.
"""
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import os

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

##########################################
# Basic API Call
##########################################

# Generate a response from the model
response = client.models.generate_content(
    model="gemma-4-31b-it",
    contents="Hello world.",
)

# Access just the model output text
print(response.text)

# Adding a system prompt
print("== After adding a system prompt ==")
response = client.models.generate_content(
    model="gemma-4-31b-it",
    contents="Hello world.",
    config=types.GenerateContentConfig(
        system_instruction="Your name is Aura. Always respond like a pirate.",
    ),
)

# Print the response text
print(response.text)

##########################################
# Structured Outputs
##########################################
# https://ai.google.dev/gemini-api/docs/structured-output

class SupportTicket(BaseModel):
    """A support ticket."""
    subject: str = Field(..., description="The subject of the support ticket")
    body: str = Field(..., description="A description of the support ticket")

print("== Using structured outputs ==")
response = client.models.generate_content(
    model="gemma-4-31b-it",
    contents="I can't login to my account.",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=SupportTicket,
    ),
)

parsed = response.parsed or SupportTicket.model_validate_json(response.text)
print(parsed)


##########################################
# Streaming API Call
##########################################

# Generate a response and stream back the results
stream = client.models.generate_content_stream(
    model="gemma-4-31b-it",
    contents="Hello world.",
    config=types.GenerateContentConfig(
        system_instruction="Your name is Aura. Always respond like a pirate.",
    ),
)

print("== Using streaming API ==")
# Filter for just the text deltas
for chunk in stream:
    if chunk.text:
        print(chunk.text, end="", flush=True)
