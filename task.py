## Importing libraries and files
from crewai import Task

from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from tools import search_tool, search_financial_document, analyze_investment_tool, create_risk_assessment_tool

verification = Task(
    description=(
        "Analyze the provided document at the specified path and verify if it is indeed a financial document. "
        "Extract key identifiers such as the title, company name, reporting period, or any other metadata to confirm its authenticity. "
        "If it's not a financial document, halt further analysis."
    ),
    expected_output=(
        "A clear confirmation of whether the document is a valid financial report, accompanied by "
        "extracted metadata (e.g., Company Name, Date, Report Type). If invalid, a clear rejection message."
    ),
    agent=verifier,
    tools=[search_financial_document],
    async_execution=False
)

## Creating a task to help solve user's query
analyze_financial_document = Task(
    description=(
        "Thoroughly analyze the verified financial document. "
        "Focus on addressing the specific query: '{query}'. "
        "Extract critical financial metrics, summarize key sections, and pinpoint significant trends or anomalies. "
        "Use web search if current external context is needed to evaluate the company's position."
    ),
    expected_output=(
        "A detailed, structured report addressing the user's query '{query}'. "
        "Includes extracted financial figures, a summary of key factors, and "
        "objective analysis of the company's financial health."
    ),
    agent=financial_analyst,
    tools=[search_financial_document, search_tool],
    async_execution=False,
)

## Creating an investment analysis task
investment_analysis = Task(
    description=(
        "Based on the analysis provided by the financial analyst regarding the query '{query}', formulate strategic investment advice. "
        "Evaluate profitability, growth, and other extracted metrics to determine the viability of investing."
    ),
    expected_output=(
        "A professional, well-reasoned investment recommendation. "
        "Includes a clear 'Buy/Hold/Sell' or similar strategic stance, supported by specific data points "
        "from the financial document analysis."
    ),
    agent=investment_advisor,
    tools=[analyze_investment_tool],
    async_execution=False,
)

## Creating a risk assessment task
risk_assessment = Task(
    description=(
        "Review the findings from the preceding analyses for the query '{query}' and identify all potential risks "
        "(e.g., market volatility, liquidity issues, high debt). Provide a comprehensive risk profile."
    ),
    expected_output=(
        "A structured risk assessment report detailing identified financial and operational risks, "
        "an overall risk rating (Low/Medium/High), and potential mitigation strategies."
    ),
    agent=risk_assessor,
    tools=[create_risk_assessment_tool],
    async_execution=False,
)