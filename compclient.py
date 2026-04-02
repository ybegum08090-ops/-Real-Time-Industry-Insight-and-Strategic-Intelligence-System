import asyncio
from fastmcp import Client

async def run_comparison():
    async with Client("industry/compserver.py") as client:
        nike_data = await client.call_tool("get_brand_data", {"brand_name": "nike"})
        puma_data = await client.call_tool("get_brand_data", {"brand_name": "puma"})

        
        context = f"Nike Data: {nike_data}\nPuma Data: {puma_data}"
        final_prompt = f"""
        Based on this real-time data:
        {context}
        
        Compare the average price and ratings between Nike and Puma. 
        Which brand currently offers better value for money?
        """
        
        print("--- Context Provided to AI ---")
        print(final_prompt)
        # Note: You would normally send 'final_prompt' to an LLM like GPT-4 or Claude here.

if __name__ == "__main__":
    asyncio.run(run_comparison())
