import asyncio 
from fastmcp import Client

client = Client("server.py")

async def main():
    # connection is establised
    async with client:
        print(f"Client connected: {client.is_connected()}\n\n")

        # make MCP calls with the context
        tools = await client.list_tools()
        print(f"Available tools:\n{tools}\n")
        # print(f"Name: {tools[0].name}")
        # print(f"Description: {tools[0].description}")
        # print(f"Input Schema: {tools[0].inputSchema}\n")
        

        # get the resources
        resources = await client.list_resources()
        print(f"Available Resource: {resources}\n")
        # print(f"Name: {resources[0].name}")
        # print(f"Description: {resources[0].description}")
        # print(f"URI: {resources[0].uri}\n")

        query = input("Enter the query: ")
        print(query)
        # calling the search_in_file tool with a query
        result = await client.call_tool("search_in_file",{"query":"What is FastMCP?"})
        print(f"Result of tool calling:\n{result[0].text}\n")

    # connection is closed automatically
    print(f"Client Connection: {client.is_connected()}")


if __name__ == "__main__":
    asyncio.run(main())

