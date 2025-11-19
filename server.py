"""
Hermes MCP Server - Development toolkit for Claude Desktop.

Tools:
File Operations:
1. read_file - Read text file contents
2. write_file - Create/overwrite file
3. append_to_file - Append content to file
4. delete_file - Delete a file
5. copy_file - Copy file to new location
6. move_file - Move/rename file
7. file_exists - Check if file exists
8. get_file_info - Get file metadata
9. list_directory - List folder contents
10. search_files - Find files by pattern

Shell & Git:
11. run_powershell - Execute PowerShell commands
12. run_git - Execute Git commands

Web & API:
13. fetch_url - Fetch webpage content as text
14. http_request - Make HTTP API calls (GET/POST/PUT/DELETE)

System:
15. get_time - Get current local date and time

Usage:
    python server.py
    
Configure in Claude Desktop's claude_desktop_config.json
"""

import os
import asyncio
import shutil
import fnmatch
import json
import re
from pathlib import Path
from datetime import datetime

import httpx

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Initialize server
server = Server("hermes-mcp")

# Define allowed base paths for safety
ALLOWED_PATHS = [
    Path("C:/Users/YOUR_USERNAME/Projects"),
    Path("C:/Users/YOUR_USERNAME/Documents"),
]

def is_path_allowed(path: Path) -> bool:
    """Check if path is within allowed directories."""
    path = path.resolve()
    return any(
        path == allowed or allowed in path.parents
        for allowed in ALLOWED_PATHS
    )

def strip_html(html: str) -> str:
    """Basic HTML to text conversion."""
    # Remove script and style elements
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    html = re.sub(r'<[^>]+>', ' ', html)
    # Decode common HTML entities
    html = html.replace('&nbsp;', ' ')
    html = html.replace('&amp;', '&')
    html = html.replace('&lt;', '<')
    html = html.replace('&gt;', '>')
    html = html.replace('&quot;', '"')
    # Collapse whitespace
    html = re.sub(r'\s+', ' ', html)
    return html.strip()

@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="read_file",
            description="Read the contents of a text file. Returns the file content as text.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the file to read"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write content to a file. Creates the file if it doesn't exist, overwrites if it does.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="append_to_file",
            description="Append content to the end of a file. Creates the file if it doesn't exist.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the file"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to append"
                    }
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="delete_file",
            description="Delete a file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the file to delete"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="copy_file",
            description="Copy a file to a new location.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Absolute path to the source file"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Absolute path to the destination"
                    }
                },
                "required": ["source", "destination"]
            }
        ),
        Tool(
            name="move_file",
            description="Move or rename a file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Absolute path to the source file"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Absolute path to the destination"
                    }
                },
                "required": ["source", "destination"]
            }
        ),
        Tool(
            name="file_exists",
            description="Check if a file or directory exists.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to check"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="get_file_info",
            description="Get file metadata (size, modified time, type).",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the file"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="list_directory",
            description="List files and folders in a directory. Returns names with [FILE] or [DIR] prefix.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the directory to list"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="search_files",
            description="Search for files matching a pattern in a directory tree.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the directory to search"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern to match (e.g., '*.py', '*.md')"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Search subdirectories (default: true)"
                    }
                },
                "required": ["path", "pattern"]
            }
        ),
        Tool(
            name="run_powershell",
            description="Execute a PowerShell command and return the output.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "PowerShell command to execute"
                    },
                    "working_directory": {
                        "type": "string",
                        "description": "Optional working directory for the command"
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="run_git",
            description="Execute a Git command and return the output.",
            inputSchema={
                "type": "object",
                "properties": {
                    "args": {
                        "type": "string",
                        "description": "Git arguments (e.g., 'status', 'log --oneline -5')"
                    },
                    "working_directory": {
                        "type": "string",
                        "description": "Repository directory"
                    }
                },
                "required": ["args", "working_directory"]
            }
        ),
        Tool(
            name="fetch_url",
            description="Fetch a webpage and return its content as plain text (HTML stripped).",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to fetch"
                    },
                    "raw": {
                        "type": "boolean",
                        "description": "Return raw HTML instead of stripped text (default: false)"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="http_request",
            description="Make an HTTP API request. Returns response body and status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, PUT, DELETE, PATCH)",
                        "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]
                    },
                    "url": {
                        "type": "string",
                        "description": "URL to request"
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional headers as key-value pairs"
                    },
                    "body": {
                        "type": "string",
                        "description": "Optional request body (for POST/PUT/PATCH)"
                    },
                    "json_body": {
                        "type": "object",
                        "description": "Optional JSON body (will be serialized)"
                    }
                },
                "required": ["method", "url"]
            }
        ),
        Tool(
            name="get_time",
            description="Get current local date and time on the machine.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    
    if name == "read_file":
        path = Path(arguments["path"])
        
        if not is_path_allowed(path):
            return [TextContent(
                type="text",
                text=f"Error: Path not allowed: {path}"
            )]
        
        if not path.exists():
            return [TextContent(
                type="text",
                text=f"Error: File not found: {path}"
            )]
        
        if not path.is_file():
            return [TextContent(
                type="text",
                text=f"Error: Not a file: {path}"
            )]
        
        try:
            content = path.read_text(encoding='utf-8')
            return [TextContent(
                type="text",
                text=content
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error reading file: {e}"
            )]
    
    elif name == "write_file":
        path = Path(arguments["path"])
        content = arguments["content"]
        
        if not is_path_allowed(path):
            return [TextContent(
                type="text",
                text=f"Error: Path not allowed: {path}"
            )]
        
        try:
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            path.write_text(content, encoding='utf-8')
            return [TextContent(
                type="text",
                text=f"Successfully wrote {len(content)} bytes to {path}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error writing file: {e}"
            )]
    
    elif name == "append_to_file":
        path = Path(arguments["path"])
        content = arguments["content"]
        
        if not is_path_allowed(path):
            return [TextContent(
                type="text",
                text=f"Error: Path not allowed: {path}"
            )]
        
        try:
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'a', encoding='utf-8') as f:
                f.write(content)
            return [TextContent(
                type="text",
                text=f"Successfully appended {len(content)} bytes to {path}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error appending to file: {e}"
            )]
    
    elif name == "delete_file":
        path = Path(arguments["path"])
        
        if not is_path_allowed(path):
            return [TextContent(
                type="text",
                text=f"Error: Path not allowed: {path}"
            )]
        
        if not path.exists():
            return [TextContent(
                type="text",
                text=f"Error: File not found: {path}"
            )]
        
        try:
            if path.is_file():
                path.unlink()
                return [TextContent(
                    type="text",
                    text=f"Successfully deleted {path}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Error: {path} is not a file. Use rmdir for directories."
                )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error deleting file: {e}"
            )]
    
    elif name == "copy_file":
        source = Path(arguments["source"])
        destination = Path(arguments["destination"])
        
        if not is_path_allowed(source) or not is_path_allowed(destination):
            return [TextContent(
                type="text",
                text=f"Error: Path not allowed"
            )]
        
        if not source.exists():
            return [TextContent(
                type="text",
                text=f"Error: Source file not found: {source}"
            )]
        
        try:
            # Create parent directories if needed
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, destination)
            return [TextContent(
                type="text",
                text=f"Successfully copied {source} to {destination}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error copying file: {e}"
            )]
    
    elif name == "move_file":
        source = Path(arguments["source"])
        destination = Path(arguments["destination"])
        
        if not is_path_allowed(source) or not is_path_allowed(destination):
            return [TextContent(
                type="text",
                text=f"Error: Path not allowed"
            )]
        
        if not source.exists():
            return [TextContent(
                type="text",
                text=f"Error: Source file not found: {source}"
            )]
        
        try:
            # Create parent directories if needed
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source), str(destination))
            return [TextContent(
                type="text",
                text=f"Successfully moved {source} to {destination}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error moving file: {e}"
            )]
    
    elif name == "file_exists":
        path = Path(arguments["path"])
        
        if not is_path_allowed(path):
            return [TextContent(
                type="text",
                text=f"Error: Path not allowed: {path}"
            )]
        
        exists = path.exists()
        file_type = "directory" if path.is_dir() else "file" if path.is_file() else "unknown"
        
        return [TextContent(
            type="text",
            text=f"{'Exists' if exists else 'Does not exist'}: {path}" + (f" (type: {file_type})" if exists else "")
        )]
    
    elif name == "get_file_info":
        path = Path(arguments["path"])
        
        if not is_path_allowed(path):
            return [TextContent(
                type="text",
                text=f"Error: Path not allowed: {path}"
            )]
        
        if not path.exists():
            return [TextContent(
                type="text",
                text=f"Error: Path not found: {path}"
            )]
        
        try:
            stat = path.stat()
            file_type = "directory" if path.is_dir() else "file"
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
            created = datetime.fromtimestamp(stat.st_ctime).isoformat()
            
            info = f"""Path: {path}
Type: {file_type}
Size: {size} bytes
Modified: {modified}
Created: {created}"""
            
            return [TextContent(
                type="text",
                text=info
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error getting file info: {e}"
            )]
    
    elif name == "list_directory":
        path = Path(arguments["path"])
        
        if not is_path_allowed(path):
            return [TextContent(
                type="text",
                text=f"Error: Path not allowed: {path}"
            )]
        
        if not path.exists():
            return [TextContent(
                type="text",
                text=f"Error: Directory not found: {path}"
            )]
        
        if not path.is_dir():
            return [TextContent(
                type="text",
                text=f"Error: Not a directory: {path}"
            )]
        
        try:
            items = []
            for item in sorted(path.iterdir()):
                prefix = "[DIR]" if item.is_dir() else "[FILE]"
                items.append(f"{prefix} {item.name}")
            
            if not items:
                return [TextContent(
                    type="text",
                    text="(empty directory)"
                )]
            
            return [TextContent(
                type="text",
                text="\n".join(items)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error listing directory: {e}"
            )]
    
    elif name == "search_files":
        path = Path(arguments["path"])
        pattern = arguments["pattern"]
        recursive = arguments.get("recursive", True)
        
        if not is_path_allowed(path):
            return [TextContent(
                type="text",
                text=f"Error: Path not allowed: {path}"
            )]
        
        if not path.exists():
            return [TextContent(
                type="text",
                text=f"Error: Directory not found: {path}"
            )]
        
        try:
            matches = []
            if recursive:
                for root, dirs, files in os.walk(path):
                    for filename in fnmatch.filter(files, pattern):
                        matches.append(os.path.join(root, filename))
            else:
                for item in path.iterdir():
                    if item.is_file() and fnmatch.fnmatch(item.name, pattern):
                        matches.append(str(item))
            
            if not matches:
                return [TextContent(
                    type="text",
                    text=f"No files matching '{pattern}' found in {path}"
                )]
            
            return [TextContent(
                type="text",
                text=f"Found {len(matches)} files:\n" + "\n".join(matches)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error searching files: {e}"
            )]
    
    elif name == "run_powershell":
        command = arguments["command"]
        working_dir = arguments.get("working_directory")
        
        try:
            # Use asyncio.create_subprocess_exec for proper async
            # CRITICAL: stdin=DEVNULL prevents inheriting MCP's stdin pipe
            process = await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-ExecutionPolicy", "Bypass",
                "-Command", command,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=30
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return [TextContent(
                    type="text",
                    text="Error: Command timed out after 30 seconds"
                )]
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace').strip() if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace').strip() if stderr else ""
            
            output = ""
            if stdout_text:
                output += stdout_text
            if stderr_text:
                if output:
                    output += "\n--- STDERR ---\n"
                output += stderr_text
            
            if not output:
                output = "(no output)"
            
            return [TextContent(
                type="text",
                text=f"Exit code: {process.returncode}\n\n{output}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error running command: {e}"
            )]
    
    elif name == "run_git":
        args = arguments["args"]
        working_dir = arguments["working_directory"]
        
        # Find Git executable
        git_exe = r"C:\Program Files\Git\cmd\git.exe"
        if not Path(git_exe).exists():
            git_exe = r"C:\Program Files\Git\bin\git.exe"
        if not Path(git_exe).exists():
            return [TextContent(
                type="text",
                text="Error: Git not found. Check installation."
            )]
        
        try:
            # Parse args string into list for subprocess_exec
            args_list = args.split()
            
            # Use asyncio.create_subprocess_exec - no shell, direct execution
            # CRITICAL: stdin=DEVNULL prevents inheriting MCP's stdin pipe
            # This stops Git from waiting for input that will never come
            process = await asyncio.create_subprocess_exec(
                git_exe,
                *args_list,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            try:
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=10
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return [TextContent(
                    type="text",
                    text="Error: Git command timed out after 10 seconds"
                )]
            
            # Decode output with error handling
            stdout_text = stdout.decode('utf-8', errors='replace').strip() if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace').strip() if stderr else ""
            
            # Combine output
            output = ""
            if stdout_text:
                output = stdout_text
            if stderr_text:
                if output:
                    output += "\n--- STDERR ---\n"
                output += stderr_text
            
            if not output:
                if process.returncode == 0:
                    output = "(Command executed successfully with no output)"
                else:
                    output = f"(Command failed with exit code {process.returncode} but no output)"
            
            return [TextContent(
                type="text",
                text=f"Exit code: {process.returncode}\n\n{output}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error running git: {str(e)}"
            )]
    
    elif name == "fetch_url":
        url = arguments["url"]
        raw = arguments.get("raw", False)
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                
                content = response.text
                
                if not raw:
                    content = strip_html(content)
                
                # Truncate if too long
                if len(content) > 50000:
                    content = content[:50000] + "\n\n... (truncated)"
                
                return [TextContent(
                    type="text",
                    text=f"Status: {response.status_code}\nURL: {response.url}\n\n{content}"
                )]
        except httpx.TimeoutException:
            return [TextContent(
                type="text",
                text=f"Error: Request timed out after 15 seconds"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error fetching URL: {e}"
            )]
    
    elif name == "http_request":
        method = arguments["method"]
        url = arguments["url"]
        headers = arguments.get("headers", {})
        body = arguments.get("body")
        json_body = arguments.get("json_body")
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                # Prepare request kwargs
                kwargs = {"headers": headers}
                
                if json_body:
                    kwargs["json"] = json_body
                elif body:
                    kwargs["content"] = body
                
                # Make request
                response = await client.request(method, url, **kwargs)
                
                # Try to parse as JSON for nice formatting
                try:
                    response_body = json.dumps(response.json(), indent=2)
                except:
                    response_body = response.text
                
                # Truncate if too long
                if len(response_body) > 50000:
                    response_body = response_body[:50000] + "\n\n... (truncated)"
                
                return [TextContent(
                    type="text",
                    text=f"Status: {response.status_code}\nURL: {response.url}\n\n{response_body}"
                )]
        except httpx.TimeoutException:
            return [TextContent(
                type="text",
                text=f"Error: Request timed out after 30 seconds"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error making request: {e}"
            )]
    
    elif name == "get_time":
        now = datetime.now()
        return [TextContent(
            type="text",
            text=f"{now.strftime('%A, %d %B %Y, %I:%M %p')} ({now.strftime('%Y-%m-%d %H:%M:%S')})"
        )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
