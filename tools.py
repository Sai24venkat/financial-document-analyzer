## Importing libraries and files
import os
import logging
from dotenv import load_dotenv
load_dotenv()

from crewai_tools import tools, tool
from crewai_tools.tools.serper_dev_tool import SerperDevTool
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)

## Creating search tool
search_tool = SerperDevTool()

@tool("Search Financial Document")
def search_financial_document(path: str, query: str) -> str:
    """Uses RAG to extract highly relevant chunks from large financial PDFs."""
    try:
        loader = PyPDFLoader(path)
        docs = loader.load()

        # Chunk the document to prevent token limit errors
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(docs)

        # Create localized semantic search
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = FAISS.from_documents(splits, embeddings)
        
        # Retrieve the Top 5 most relevant chunks
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        relevant_docs = retriever.invoke(query)
        
        context = "\n\n...".join([doc.page_content for doc in relevant_docs])
        return f"Found Context for '{query}':\n{context}"
    except Exception as e:
        logger.error(f"PDF Error: {e}", exc_info=True)
        return f"Error reading PDF: {str(e)}"

## Creating Investment Analysis Tool
@tool("Analyze Investment")
def analyze_investment_tool(financial_document_data: str) -> str:
    """Tool to analyze an investment from financial document data."""
    # Process and analyze the financial document data
    processed_data = financial_document_data
    
    # Clean up the data format
    i = 0
    while i < len(processed_data):
        if processed_data[i:i+2] == "  ":  # Remove double spaces
            processed_data = processed_data[:i] + processed_data[i+1:]
        else:
            i += 1
            
    # Simple investment analysis logic (mock implementation for completeness)
    if "profit" in processed_data.lower() or "growth" in processed_data.lower():
        return "The document indicates positive trends. Consider standard investment strategies focusing on growth."
    else:
         return "The document does not strongly indicate positive trends. Maintain caution."

## Creating Risk Assessment Tool
@tool("Create Risk Assessment")
def create_risk_assessment_tool(financial_document_data: str) -> str:
    """Tool to create a risk assessment based on document data."""
    # Simple risk assessment logic (mock implementation for completeness)
    if "risk" in financial_document_data.lower() or "loss" in financial_document_data.lower() or "liability" in financial_document_data.lower():
        return "Significant risk factors identified in the text. Ensure a diversified portfolio."
    else:
        return "Standard market risks apply based on the text provided."