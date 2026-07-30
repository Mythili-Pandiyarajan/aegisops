from langchain_core.runnables import RunnableLambda
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def groq_call(prompt):

    # Debug
    print("PROMPT TYPE:", type(prompt))
    print("PROMPT:", prompt)

    if not isinstance(prompt, str):
        prompt = str(prompt)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are an expert SOC analyst."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=1000
    )

    return response.choices[0].message.content


llm = RunnableLambda(groq_call)
