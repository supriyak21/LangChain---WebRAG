import streamlit as st
import os
from dotenv import load_dotenv
from serpapi import GoogleSearch
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent
from langchain.tools import Tool
import requests
from bs4 import BeautifulSoup

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# fetch web page content
def fetch_page_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=" ", strip=True)
        return text[:1500]
    except Exception as e:
        return f"Error fetching content from {url}: {e}"

# Google search tool for LangChain Agent
def serpapi_search(query: str) -> str:
    params = {
        "q": query,
        "engine": "google",
        "api_key": SERPAPI_API_KEY,
        "num": 3
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    links = [res["link"] for res in results.get("organic_results", []) if "link" in res]

    summaries = []
    for link in links:
        content = fetch_page_text(link)
        summaries.append(f"🔗 Source: {link}\n\n{content}")

    return "\n\n---\n\n".join(summaries)

# LangChain Tool & Agent Setup
search_tool = Tool(
    name="GoogleSearch",
    func=serpapi_search,
    description="Search Google for real-time information"
)

llm = ChatOpenAI(
    model_name="gpt-4",
    temperature=0.3,
    openai_api_key=OPENAI_API_KEY
)

agent = initialize_agent(
    tools=[search_tool],
    llm=llm,
    agent="zero-shot-react-description",
    verbose=False
)

# Streamlit UI
st.set_page_config(page_title="AI Q&A with LangChain")
st.title("AI-driven Q&A System")
st.markdown("Hi! I am a Q&A System and I use Google along with the GPT-4 to answer. You can ask me any question.")

user_input = st.text_input("Enter your question:")

if st.button("Get Answer") and user_input:
    with st.spinner("Thinking..."):
        try:
            response = agent.run(user_input)
            st.success("Answer:")
            st.write(response)
        except Exception as e:
            st.error(f"Something went wrong: {e}")
