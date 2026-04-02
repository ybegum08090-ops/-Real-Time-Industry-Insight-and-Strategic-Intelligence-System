# Real-Time Industry Insight & Strategic Intelligence System
This project is an AI-powered application that provides real-time industry insights by integrating live data from multiple external sources. It helps users analyze market trends, compare brands, and make better decisions using up-to-date information.

## Overview

Traditional AI models rely on static data and may not reflect current market conditions. This system connects AI with real-time APIs such as Google Search, Shopping, and Wikipedia to generate dynamic insights.
The application uses a modular architecture with a Streamlit frontend and a FastMCP-based backend to process and display data efficiently.

## Features

- Real-time market analysis  
- Brand comparison (price, ratings, product details)  
- Trend analysis using frequency and patterns  
- AI-generated insights  
- Chat-based assistant for queries  
- Wikipedia integration for additional information  
- Data visualization using charts  

## Tech Stack

- Python  
- Streamlit (frontend)  
- FastMCP (backend communication)  
- SerpAPI (Google Search and Shopping data)  
- Wikipedia API  
- LangChain / HuggingFace (AI models)  
- Matplotlib (visualization)  
- dotenv (environment management)  

## Project Structure

industry/  
- app.py              -> main Streamlit application  
- ai_engine.py        -> analysis and scoring logic  
- chat_module.py      -> chat-based AI assistant  
- compclient.py       -> client-side API calls  
- compserver.py       -> comparison logic  
- mcp_server.py       -> MCP server  
- pdf_report.py       -> report generation  
- debug_mcp.py        -> debugging utilities  

## How It Works

1. User enters a query or brand name  
2. Streamlit UI sends request to backend  
3. FastMCP server processes the request  
4. External APIs are called to fetch live data  
5. Data is analyzed and processed  
6. Results are displayed as tables, charts, and insights  

## Use Cases

Market trend analysis
Business intelligence
Brand comparison
Competitor analysis
AI-assisted decision making

## Future Scope

More data sources (news, social media)
Advanced predictive analytics
User authentication
Cloud deployment

## Author

Developed by Group-1 under the Infosys Springboard initiative.

Project: Real-Time Industry Insight & Strategic Intelligence System

## License

MIT License

