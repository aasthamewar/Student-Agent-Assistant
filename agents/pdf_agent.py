from google.adk.agents import LlmAgent
from tools.pdf_reader_tool import pdf_reader_tool
from config import GEMINI_API_KEY

pdf_agent = LlmAgent(
    name="pdf_summary_agent",
    instructions="You summarize any uploaded PDF clearly and concisely.",
    tools=[pdf_reader_tool],
    model="gemini-1.5-flash",
    api_key=GEMINI_API_KEY
)
