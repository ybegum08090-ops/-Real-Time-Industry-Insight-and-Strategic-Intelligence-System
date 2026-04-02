import asyncio
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from fastmcp import Client

async def test():
    server_path = os.path.join(os.path.dirname(__file__), "compserver.py")
    print(f"Server path: {server_path}")
    print(f"Server exists: {os.path.exists(server_path)}")
    print(f"SERP_API_KEY set: {bool(os.getenv('SERP_API_KEY'))}")
    
    async with Client(server_path) as client:
        # List available tools
        tools = await client.list_tools()
        print(f"\nAvailable tools: {tools}")
        
        # Call the tool
        result = await client.call_tool("get_brand_data", {"brand_name": "nike", "product_type": "shoes"})
        print(f"\nResult type: {type(result)}")
        print(f"Result repr: {repr(result)}")
        
        # Try to inspect individual items
        if isinstance(result, list):
            for i, item in enumerate(result):
                print(f"\n  Item {i}: type={type(item)}, value={repr(item)}")
                if hasattr(item, '__dict__'):
                    print(f"  Item {i} attrs: {item.__dict__}")
                if hasattr(item, 'text'):
                    print(f"  Item {i} text: {item.text}")
                if hasattr(item, 'content'):
                    print(f"  Item {i} content: {item.content}")
        elif hasattr(result, 'content'):
            print(f"\nResult.content: {result.content}")
            for i, item in enumerate(result.content):
                print(f"  Content item {i}: type={type(item)}, repr={repr(item)}")
                if hasattr(item, 'text'):
                    print(f"  Content item {i} text: {item.text}")

if __name__ == "__main__":
    asyncio.run(test())
