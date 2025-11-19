# Hermes MCP

A lightweight, reliable MCP server for Claude Desktop with 14 essential development tools.

**Platform:** Windows (uses PowerShell, Git for Windows paths)  
**Key feature:** Fixes the critical async subprocess stdin inheritance bug that causes tools to hang.

## Why Hermes?

Most MCP file/shell servers are flaky. Hermes is:
- **Reliable** - Proper async subprocess handling with stdin isolation
- **Complete** - 14 tools covering files, shell, git, and HTTP
- **Simple** - Pure Python, ~600 lines, easy to understand and modify
- **Fast** - Direct execution, no unnecessary overhead

## Platform Support

**Currently Windows-optimized:**
- Uses `powershell.exe` for shell commands
- Git paths default to `C:\Program Files\Git\`
- Path separators are Windows-style

**Unix/Mac adaptation needed:**
- Replace `run_powershell` with `run_bash`
- Update git executable detection
- Adjust path handling

PRs for Unix/Mac support welcome!

## The Critical Fix

If you're building MCP tools that spawn subprocesses, you'll hit this: **subprocesses inherit MCP's stdin pipe and hang waiting for input**.

The fix:
```python
process = await asyncio.create_subprocess_exec(
    executable, *args,
    stdin=asyncio.subprocess.DEVNULL,  # THIS IS THE KEY
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)
```

Without `stdin=asyncio.subprocess.DEVNULL`, git and shell commands will hang indefinitely in Claude Desktop.

## Tools (14)

### File Operations (10)
| Tool | Description |
|------|-------------|
| `read_file` | Read text file contents |
| `write_file` | Create/overwrite file |
| `append_to_file` | Append to file |
| `delete_file` | Delete a file |
| `copy_file` | Copy file |
| `move_file` | Move/rename file |
| `file_exists` | Check existence |
| `get_file_info` | Size, dates, type |
| `list_directory` | List contents |
| `search_files` | Find by glob pattern |

### Shell & Git (2)
| Tool | Description |
|------|-------------|
| `run_powershell` | Execute PowerShell commands (Windows) |
| `run_git` | Execute Git commands |

### Web & API (2)
| Tool | Description |
|------|-------------|
| `fetch_url` | Fetch webpage as text |
| `http_request` | Full HTTP API calls |

## Installation

### Prerequisites
- Windows 10/11
- Python 3.10+
- Git for Windows
- Claude Desktop

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/hermes-mcp.git
cd hermes-mcp
```

### 2. Create virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure allowed paths

Edit `server.py` and update the `ALLOWED_PATHS` list to match your system:
```python
ALLOWED_PATHS = [
    Path("C:/Users/YOUR_USERNAME/Documents"),
    Path("C:/Users/YOUR_USERNAME/Projects"),
    # Add your paths here
]
```

### 5. Add to Claude Desktop config

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hermes": {
      "command": "C:\\path\\to\\hermes-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\hermes-mcp\\server.py"]
    }
  }
}
```

### 6. Restart Claude Desktop

## Usage Examples

```python
# Read a file
hermes:read_file path="C:\Users\me\project\README.md"

# Git operations
hermes:run_git args="status" working_directory="C:\Users\me\project"
hermes:run_git args="log --oneline -5" working_directory="C:\Users\me\project"

# Search for files
hermes:search_files path="C:\Users\me\project" pattern="*.py"

# Fetch a webpage
hermes:fetch_url url="https://example.com"

# API call
hermes:http_request method="GET" url="https://api.github.com/zen"

# POST with JSON
hermes:http_request method="POST" url="https://api.example.com/data" json_body={"key": "value"}
```

## Security

- File operations are restricted to paths in `ALLOWED_PATHS`
- Web/API tools have no URL restrictions (intentional for development)
- No authentication or rate limiting (local use only)

## Dependencies

- `mcp` - Model Context Protocol SDK
- `httpx` - Async HTTP client

## Technical Details

### Async Subprocess Pattern
```python
async def run_command(...):
    process = await asyncio.create_subprocess_exec(
        executable, *args,
        stdin=asyncio.subprocess.DEVNULL,  # Prevents stdin inheritance
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
        # Handle timeout
```

### Why stdin=DEVNULL?

MCP servers communicate via stdio. When you spawn a subprocess, it inherits the parent's stdin by default. This means:

1. Your subprocess's stdin points to MCP's communication pipe
2. If the subprocess tries to read stdin (git, shell, etc.), it blocks
3. The MCP message it reads isn't valid input, causing hangs or errors

Setting `stdin=DEVNULL` tells the subprocess "you have no stdin" - it won't try to read, and won't interfere with MCP's communication.

## Troubleshooting

**Tools hang indefinitely**
- Check that `stdin=asyncio.subprocess.DEVNULL` is set
- Verify the executable path exists

**"Path not allowed" errors**
- Add your paths to `ALLOWED_PATHS` in server.py

**Git not found**
- Install Git for Windows
- Check the paths in `run_git` match your installation

## Contributing

PRs welcome. Key areas:
- **Unix/Mac support** - Replace PowerShell with bash, update paths
- Additional tools
- Better error messages

## License

MIT

## Credits

The stdin fix was discovered through painful debugging - hopefully it saves you time.

---

*Named after Hermes, messenger of the gods - because that's what MCP servers do.*
