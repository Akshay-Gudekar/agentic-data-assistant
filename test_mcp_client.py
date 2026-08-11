import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools — proves the client can discover what the server offers
            tools = await session.list_tools()
            print("--- Available tools ---")
            for tool in tools.tools:
                print(f"{tool.name}: {tool.description}")

            # Call get_schema
            print("\n--- Calling get_schema ---")
            result = await session.call_tool("get_schema", {"csv_path": "data.csv"})
            print(result.content[0].text)

            # Call get_sample_rows
            print("\n--- Calling get_sample_rows ---")
            result = await session.call_tool("get_sample_rows", {"csv_path": "data.csv", "n": 3})
            print(result.content[0].text)

asyncio.run(main())