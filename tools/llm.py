"""
AegisOps - Groq LLM Wrapper

Provides a LangChain-compatible LLM interface
for LangGraph agents.
"""

from langchain_core.runnables import RunnableLambda

from groq import Groq
from dotenv import load_dotenv

import os


# Load environment variables
load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")


if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is missing. Add it to Streamlit secrets or .env"
    )


client = Groq(
    api_key=GROQ_API_KEY
)



def groq_call(prompt):

    print("🧠 Groq call started")

    try:

        # Ensure Groq receives only text
        if not isinstance(prompt, str):
            prompt = str(prompt)


        # Prevent oversized prompts
        if len(prompt) > 8000:
            prompt = prompt[:8000]


        print(
            "Prompt length:",
            len(prompt)
        )


        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[

                {
                    "role": "system",
                    "content":
                    """
You are an expert SOC analyst.

Analyze IT incidents using only
provided evidence.

Do not hallucinate.
If evidence is missing,
state that clearly.
"""
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            temperature=0.2,

            max_tokens=700,

            timeout=30

        )


        result = (
            response
            .choices[0]
            .message
            .content
        )


        print("✅ Groq response received")


        return result



    except Exception as e:

        print(
            "❌ Groq error:",
            str(e)
        )


        return (
            "LLM analysis unavailable. "
            f"Error: {str(e)}"
        )



# LangGraph / LangChain compatible object
llm = RunnableLambda(groq_call)
