import os
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

# def get_llm(temperature: float = 0) -> ChatGoogleGenerativeAI:
#     return ChatGoogleGenerativeAI(
#         model="gemini-2.5-flash-lite",
#         temperature=temperature,
#         api_key=os.getenv("GOOGLE_API_KEY"),
#     )


def get_llm(temperature: float = 0) -> ChatGroq:
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=temperature,
        api_key=os.getenv("GROQ_API_KEY"),
    )
