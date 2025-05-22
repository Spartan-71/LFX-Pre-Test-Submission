import asyncio
import json
from fastmcp import Client
from openai import OpenAI

mcp_client = Client("server.py")  # Assumes server.py exists
llm_client = OpenAI(base_url="http://localhost:8080/v1")

async def main(query: str):
    # Connection is established here
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant"
        },
        {
            "role": "user",
            "content": query
        }
    ]
    
    async with mcp_client:
        print(f"Client connected: {mcp_client.is_connected()}\n")
        
        # Make MCP calls within the context
        tools = await mcp_client.list_tools()
        available_tools = [{
            "type": "function",  
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            }
        } for tool in tools]
        
        print(f"Available tools: {available_tools}\n")
        
        # Initial API call to LLM
        response = llm_client.chat.completions.create(
            model="Llama-3-Groq-8B-Tool-Use-Q3_K_M",
            messages=messages,
            tools=available_tools,
            max_tokens=1000,
            temperature=0.7
        )
        
        print(response.choices[0].message)
        
        # Process response and handle tool calls
        final_text = []
        response_message = response.choices[0].message
        
        if response_message.content:
            final_text.append(response_message.content)
            print(f"\n\nLLM Response: {response_message.content}")
            
        elif response_message.tool_calls:
            # Handle tool calls
            tool_call = response_message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            # Execute the tool
            final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
            print(f"\n\nCalling tool {tool_name} with args {tool_args}")
            
            result = await mcp_client.call_tool(tool_name, tool_args)
            print(f"Result: {result[0].text}")
            
            # Add assistant message with tool calls to conversation
            messages.append({
                "role": "assistant",
                "content": response_message.content,  
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                ]
            })
            
            # Add tool result message
            messages.append({
                "role": "tool",  
                "tool_call_id": tool_call.id,  
                "content": result[0].text 
            })
            
            # Get final response from LLM (without tools to prevent re-calling)
            response = llm_client.chat.completions.create(
                model="Llama-3-Groq-8B-Tool-Use-Q3_K_M",
                messages=messages,
                temperature=0.7
            )
            
            final_response = response.choices[0].message.content
            final_text.append(final_response)
            print(f"\n\nFinal LLM Response: {final_response}")
        
        print(f"\n\nFinal Text: {final_text}")
        
        # Connection is closed automatically here
        print(f"Client connected: {mcp_client.is_connected()}")

if __name__ == "__main__":
    asyncio.run(main("hey give me weather alerts in california!!"))