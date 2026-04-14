from anthropic import Anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("VALIDATOR_API_KEY"))

msg = client.messages.create(
    model="claude-sonnet-20240930",
    max_tokens=50,
    messages=[{"role": "user", "content": "Say hello"}]
)

print(msg.content[0].text)