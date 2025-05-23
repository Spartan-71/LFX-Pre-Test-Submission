# Pre-test-3

## Task
Create a simple Python application that
1. takes user input
2. calls the LLM API server
3. handles LLM tool calls using MCP
4. sends LLM response back to the user


## Implementation Details

- Used `FastMCP 2.0` sdk for creating the MCP server and client.
- OpenAI SDK for building the AI Agent.
- LlamaEdge for using locally hosted LLM.
- LLM used : Llama-3-Groq-8B-Tool-Use-Q3_K_M

Note: `basic_client.py` contains the initial (scrapy) version of the MCP client, whereas `client.py` is enhanced by Claude, which is modularised and provides a better error handling. 


## Screenshots

![image](https://github.com/user-attachments/assets/22417c45-d8ec-491a-b8d7-f151e751c196)


A chat conversation with the MCP-based AI Agent.






