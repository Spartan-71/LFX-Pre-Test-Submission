from fastmcp import FastMCP, Context
from fastmcp.resources import FileResource
from pathlib import Path
import os

# Create a FastMCP server
mcp = FastMCP(name="QnA")

file_path="QnA_data.txt"
# Create a file resource that points to the text file
if os.path.exists(file_path):
    file_path_resolved = Path(file_path).resolve()
    # Create a FileResource pointing to the text file
    qa_file_resource = FileResource(
        uri=f"file://{file_path_resolved}",  # URI for the resource
        path=file_path_resolved,             # Actual file path
        name="Q&A Data File",                # Friendly name
        description="Text file containing questions and answers",
        mime_type="text/plain"               # MIME type for text
    )
    # Add the resource to the MCP server
    mcp.add_resource(qa_file_resource)
    print(f"Added file resource: {file_path}")
else:
    print(f"Warning: File {file_path} not found")

@mcp.tool()
async def search_in_file(query: str, ctx: Context) -> str:
    """
    Search for a query in the Q&A text file and return relevant sections.
    
    The LLM will need to interpret the text file format itself.
    """
    # Access the file through the MCP resource system

    # Read the file resource
    resource_content = await ctx.read_resource(f"file://{Path(file_path).resolve()}")
        
    if not resource_content:
        return "Error: Could not read file resource"
        
    # Get the text content
    file_text = resource_content[0].content
        
    # Simple search function to find relevant parts of the text
    query = query.lower()
    
    # Split the text into Q&A blocks
    blocks = []
    current_block = ""
    
    for line in file_text.split('\n'):
        if line.startswith("Q:") and current_block:
            blocks.append(current_block)
            current_block = line
        else:
            current_block += '\n' + line if current_block else line
            
    # Add the last block
    if current_block:
        blocks.append(current_block)
    
    # Find matching blocks
    matching_blocks = [block for block in blocks if query in block.lower()]
    
    if not matching_blocks:
        return f"No matches found for '{query}' in the file"
    
    return f"Found {len(matching_blocks)} matches in the file:\n\n" + "\n\n".join(matching_blocks)
        

if __name__ == "__main__":
    # Start the MCP server
    mcp.run()