import asyncio
import json
from typing import List, Dict
from fastmcp import Client
from openai import OpenAI

class Assistant:
    def __init__(
            self, 
            mcp_server_path: str = "server.py", 
            llm_base_url: str = "http://localhost:8080/v1",
            model: str = "Llama-3-Groq-8B-Tool-Use-Q3_K_M"
            ):
        """Initialize the assistant with configuration"""
        self.mcp_client = Client(mcp_server_path)
        self.llm_client = OpenAI(base_url=llm_base_url)
        self.model = model
        self.max_tokens = 6000
        self.temperature = 0.7
        
        # Conversation state
        self.messages = []
        self.available_tools = []
        self.is_running = False
        
        # System prompt
        self.system_prompt = "You are a helpful AI assistant with access to various tools. Use them when appropriate to help the user."

    async def initialize(self):
        """Initialize the MCP connection and get available tools"""
        try:
            await self.mcp_client.__aenter__()
            print(f"✓ MCP Client connected: {self.mcp_client.is_connected()}")
            
            # Get available tools
            tools = await self.mcp_client.list_tools()
            self.available_tools = [{
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                }
            } for tool in tools]
            
            print(f"✓ Available tools: {[tool['function']['name'] for tool in self.available_tools]}")
            
            # Initialize conversation with system prompt
            self.messages = [{"role": "system", "content": self.system_prompt}]
            self.is_running = True
            
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            raise

    async def cleanup(self):
        """Clean up resources"""
        try:
            await self.mcp_client.__aexit__(None, None, None)
            print("✓ MCP Client disconnected")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

    async def process_query(self, user_input: str) -> str:
        """Process a single user query and return the response"""
        if not self.is_running:
            return "❌ Assistant not initialized. Please call initialize() first."
        
        # Add user message
        self.messages.append({"role": "user", "content": user_input})
        
        try:
            # Get LLM response
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.available_tools if self.available_tools else None,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            response_message = response.choices[0].message
            
            # Handle direct response (no tools)
            if response_message.content and not response_message.tool_calls:
                self.messages.append({
                    "role": "assistant", 
                    "content": response_message.content
                })
                return response_message.content
            
            # Handle tool calls
            elif response_message.tool_calls:
                return await self._handle_tool_calls(response_message)
            
            else:
                return "❌ Received empty response from LLM"
                
        except Exception as e:
            return f"❌ Error processing query: {str(e)}"

    async def _handle_tool_calls(self, response_message) -> str:
        """Handle tool calls from the LLM"""
        try:
            # Add assistant message with tool calls
            self.messages.append({
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
                    } for tool_call in response_message.tool_calls
                ]
            })
            
            # Execute each tool call
            tool_results = []
            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"🔧 Calling tool: {tool_name} with args: {tool_args}\n")
                
                # Execute the tool
                result = await self.mcp_client.call_tool(tool_name, tool_args)
                tool_result = result[0].text
                
                # Add tool result message
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
                
                tool_results.append(f"Tool {tool_name}: {tool_result}")
            
            # Get final response from LLM
            final_response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature
            )
            
            final_content = final_response.choices[0].message.content
            
            # Add final assistant response
            self.messages.append({
                "role": "assistant",
                "content": final_content
            })
            
            return final_content
            
        except Exception as e:
            return f"❌ Error handling tool calls: {str(e)}"

    def get_conversation_history(self) -> List[Dict]:
        """Get the current conversation history"""
        return [msg for msg in self.messages if msg["role"] != "system"]

    def clear_conversation(self):
        """Clear conversation history but keep system prompt"""
        self.messages = [{"role": "system", "content": self.system_prompt}]
        print("✓ Conversation history cleared")

    def set_system_prompt(self, prompt: str):
        """Update the system prompt"""
        self.system_prompt = prompt
        self.messages[0] = {"role": "system", "content": prompt}
        print(f"✓ System prompt updated")

    async def chat_loop(self):
        """Interactive chat loop"""
        print("\n🤖 LLM-MCP Assistant Started!")
        print("Type 'quit' to exit, 'clear' to clear history, 'history' to see conversation")
        print("-" * 60)
        
        while self.is_running:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'clear':
                    self.clear_conversation()
                    continue
                elif user_input.lower() == 'history':
                    self._print_history()
                    continue
                elif not user_input:
                    continue
                
                print("🤖 Assistant: ", end="", flush=True)
                response = await self.process_query(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def _print_history(self):
        """Print conversation history"""
        history = self.get_conversation_history()
        if not history:
            print("📝 No conversation history")
            return
        
        print("\n📝 Conversation History:")
        print("-" * 100)
        for i, msg in enumerate(history, 1):
            role_emoji = "👤" if msg["role"] == "user" else "🤖" if msg["role"] == "assistant" else "🔧"
            role_name = msg["role"].title()
            content = msg.get("content", "[Tool call]")
            print(f"{i}. {role_emoji} {role_name}: {content}")

# Usage example and main execution
async def main():
    """Main function to run the assistant"""
    assistant = Assistant()
    
    try:
        # Initialize the assistant
        await assistant.initialize()
        
        # Start interactive chat
        await assistant.chat_loop()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Clean up
        await assistant.cleanup()


if __name__ == "__main__":
    # Run interactive chat
    asyncio.run(main())
    