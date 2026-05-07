# SOVEREIGN — Local AI Agent: Complete Build Prompt

---

## ROLE

You are a senior Python systems engineer and AI architect. Your task is to build
a fully local, offline-first, voice-driven AI agent called **SOVEREIGN** from
scratch — no cloud APIs, no subscriptions, no external LLM endpoints. Every
component runs entirely on the user's machine.

Do not summarize. Do not ask clarifying questions. Build the complete system.

---

## PROJECT OVERVIEW

SOVEREIGN is a personal AI agent that:

- Listens to the user's voice using on-device speech-to-text (Whisper)
- Thinks using a locally-running LLM via Ollama
- Acts on the file system, terminal, and web without opening a browser
- Remembers context across sessions using local SQLite and ChromaDB
- Speaks responses back using local TTS
- Runs 100% offline with zero cloud dependencies
- Accepts new skills as plain Python files dropped into a `/skills` folder

---

## SYSTEM ARCHITECTURE

```
Voice / Text Input
       │
       ▼
  [ Whisper STT ]  ←── on-device, faster-whisper
       │
       ▼
  [ Prompt Builder ]  ←── injects short-term + long-term memory + skills
       │
       ▼
  [ Local LLM — Ollama ]  ←── mistral:7b or llama3 (user's choice)
       │
       ▼
  [ Intent Parser ]  ←── extracts structured JSON: {tool, args, response}
       │
       ▼
  [ Tool Router ]
    ├── file_agent     → move, sort, rename, delete files
    ├── web_fetcher    → HTTP requests, scraping, DuckDuckGo search
    ├── shell_exec     → run terminal commands via subprocess
    ├── app_controller → open/close applications
    └── skill_loader   → dynamically import user-defined skills
       │
       ▼
  [ Memory Manager ]
    ├── short_term  → rolling conversation buffer (last 20 turns, in RAM)
    ├── long_term   → SQLite (facts, history, preferences)
    └── vector_mem  → ChromaDB (semantic search over past interactions)
       │
       ▼
  [ Output Handler ]
    ├── TTS (pyttsx3 or Coqui) → speak the response
    └── Terminal (rich)        → display structured output
```

---

## EXACT FILE STRUCTURE

Generate every file listed below with complete, working code:

```
sovereign/
├── main.py                   # Entry point — starts the agent loop
├── config.py                 # All user-configurable settings
├── requirements.txt          # All Python dependencies, pinned
├── install.sh                # One-command setup script (Linux/macOS)
├── install.bat               # One-command setup script (Windows)
│
├── core/
│   ├── __init__.py
│   ├── agent_loop.py         # Main listen → think → act → speak loop
│   ├── prompt_builder.py     # Assembles the full LLM prompt
│   ├── intent_parser.py      # Parses LLM output into {tool, args, reply}
│   └── tool_router.py        # Routes parsed intent to correct tool
│
├── input/
│   ├── __init__.py
│   ├── voice_listener.py     # Mic capture + Whisper STT
│   └── text_input.py         # CLI text input fallback
│
├── llm/
│   ├── __init__.py
│   └── ollama_client.py      # Sends prompts to Ollama, streams response
│
├── tools/
│   ├── __init__.py
│   ├── file_agent.py         # File system operations
│   ├── web_fetcher.py        # Web search + scraping + APIs
│   ├── shell_exec.py         # Shell command execution with safety guard
│   ├── app_controller.py     # Open/close/interact with OS applications
│   └── skill_loader.py       # Dynamically loads skills from /skills folder
│
├── memory/
│   ├── __init__.py
│   ├── short_term.py         # In-memory rolling conversation buffer
│   ├── long_term.py          # SQLite-backed persistent facts + history
│   └── vector_mem.py         # ChromaDB semantic memory
│
├── output/
│   ├── __init__.py
│   ├── tts_engine.py         # TTS with pyttsx3 (Coqui optional)
│   └── terminal_display.py   # Rich-formatted terminal output
│
├── skills/
│   ├── README.md             # How to write a custom skill
│   └── example_skill.py      # Fully annotated example skill
│
└── data/
    ├── sovereign.db          # SQLite database (auto-created)
    └── chroma/               # ChromaDB storage (auto-created)
```

---

## FILE-BY-FILE SPECIFICATIONS

### `config.py`
```python
# All values must be easily changeable by a non-technical user.
# Include:
AGENT_NAME = "Sovereign"
LLM_MODEL = "mistral"           # any model installed in Ollama
LLM_BASE_URL = "http://localhost:11434"
WHISPER_MODEL = "small"         # tiny | small | medium | large
WHISPER_DEVICE = "cpu"          # cpu | cuda
TTS_ENGINE = "pyttsx3"          # pyttsx3 | coqui
TTS_RATE = 175                  # words per minute
WAKE_WORD = "sovereign"         # optional wake-word (empty string = always on)
SHORT_TERM_LIMIT = 20           # max turns kept in RAM
LOG_LEVEL = "INFO"
SAFE_SHELL = True               # if True, blocks destructive shell commands
SKILLS_DIR = "skills/"
DATA_DIR = "data/"
```

### `main.py`
- Parse CLI flags: `--voice` (mic input), `--text` (keyboard input), `--model <name>`
- Print a clean startup banner using `rich` showing model, device, memory status
- Instantiate all components (memory, tools, LLM client, input handler)
- Call `agent_loop.run()` and handle `KeyboardInterrupt` for clean shutdown
- On shutdown, persist short-term memory to long-term SQLite

### `core/agent_loop.py`
Implement the main loop as a class `AgentLoop` with method `run()`:
1. Wait for input (voice or text)
2. If wake word configured, only activate on wake word detection
3. Pass transcript to `PromptBuilder.build()`
4. Send prompt to `OllamaClient.complete()` with streaming
5. Pass raw LLM output to `IntentParser.parse()`
6. If a tool is requested, route to `ToolRouter.execute(tool, args)`
7. Inject tool result back into LLM as a follow-up completion
8. Send final response text to `TTSEngine.speak()` and `TerminalDisplay.show()`
9. Update `ShortTermMemory` and `LongTermMemory`
10. Loop

### `core/prompt_builder.py`
Build a `PromptBuilder` class. The system prompt must instruct the LLM to:
- Always respond in valid JSON: `{"tool": "<name>|none", "args": {}, "reply": "<text>"}`
- Use tool `"none"` for conversational responses
- Available tools: `file_agent`, `web_fetcher`, `shell_exec`, `app_controller`, + any loaded skills
- Include the user's name and preferences from long-term memory if available
- Inject the last N turns from short-term memory as conversation history
- Inject top-3 semantically relevant memories from ChromaDB
- Inject a list of currently available skills with their descriptions

Full system prompt template (include verbatim, with f-string slots):
```
You are {agent_name}, a fully local AI agent running on this machine.
You have no internet access unless the web_fetcher tool is explicitly called.
You have access to the following tools: {tool_list}

You MUST always respond with valid JSON in this exact format:
{{"tool": "<tool_name or none>", "args": {{...}}, "reply": "<your spoken reply>"}}

The "reply" field is what gets spoken aloud to the user. Keep it concise and natural.
If using a tool, "reply" should tell the user what you are about to do.
If not using a tool, set "tool" to "none" and "args" to {{}}.

Relevant memories:
{injected_memories}

Conversation so far:
{conversation_history}
```

### `core/intent_parser.py`
- Parse LLM output string as JSON
- Handle malformed JSON gracefully: attempt to extract JSON from mixed output using regex
- Validate that `tool`, `args`, and `reply` keys are present
- If parsing fails entirely, return `{"tool": "none", "args": {}, "reply": raw_output}`
- Log all parsing failures at DEBUG level

### `core/tool_router.py`
- Map tool name strings to tool handler classes
- Call `tool.execute(args)` and return result as a string
- Wrap every tool call in try/except — never crash the agent loop on tool failure
- Return a user-friendly error string on failure

### `input/voice_listener.py`
Use `faster-whisper` and `sounddevice`:
- Continuously capture audio from the default microphone
- Use voice activity detection (VAD): only transcribe when speech is detected
- VAD implementation: compute RMS of audio chunk; if above threshold, start recording; if below threshold for 1.5 seconds, stop and transcribe
- Use `WhisperModel` from `faster_whisper` with the model size from config
- Return the transcribed string
- If `WAKE_WORD` is set, only return transcript if wake word appears in it (then strip wake word from returned text)

### `llm/ollama_client.py`
- Use `requests` to POST to `http://localhost:11434/api/generate`
- Support streaming: read the response line by line, yield tokens as they arrive
- Implement `complete(prompt: str) -> str` that collects the full streamed response
- Implement `stream(prompt: str) -> Generator[str]` that yields tokens (for terminal display)
- Handle connection errors with a clear message: "Ollama is not running. Start it with: ollama serve"
- Auto-detect if the configured model is not pulled and print: "Model not found. Run: ollama pull {model}"

### `tools/file_agent.py`
Implement class `FileAgent` with these methods. All paths must be validated before execution:
- `list_directory(path)` → returns formatted directory tree
- `move_file(src, dst)` → moves file or directory
- `copy_file(src, dst)` → copies file or directory  
- `delete_file(path)` → moves to `.trash/` folder instead of permanent delete
- `rename_file(path, new_name)` → renames in place
- `search_files(directory, pattern)` → glob search
- `organize_by_type(directory)` → sorts files into subfolders by extension:
  - Images: jpg, jpeg, png, gif, webp, svg
  - Documents: pdf, doc, docx, txt, md, xlsx, csv
  - Videos: mp4, mov, avi, mkv
  - Audio: mp3, wav, flac, m4a
  - Code: py, js, ts, html, css, sh, json
  - Archives: zip, tar, gz, rar
- `organize_by_date(directory)` → sorts files into `YYYY/MM` subfolders by modification date

### `tools/web_fetcher.py`
Implement class `WebFetcher`:
- `search(query: str, max_results=5)` → DuckDuckGo search using `duckduckgo_search` library, returns list of {title, url, snippet}
- `fetch_page(url: str)` → fetches URL with `requests`, parses with `BeautifulSoup`, returns clean text (no HTML tags, no scripts, no nav elements)
- `fetch_json(url: str, headers=None)` → fetches and returns parsed JSON from any API endpoint
- `summarize_page(url: str)` → fetch_page + send to LLM with "summarize this in 3 bullet points" instruction
- All methods must have a 10-second timeout
- Respect robots.txt on explicit fetch (not on search)

### `tools/shell_exec.py`
Implement class `ShellExecutor`:
- `execute(command: str)` → runs command via `subprocess.run`, returns stdout + stderr
- If `SAFE_SHELL = True`, reject commands matching a blocklist:
  - `rm -rf /`, `mkfs`, `dd if=`, `:(){ :|:& };:`, `chmod 777 /`, `> /dev/sda`
  - Any command targeting `/etc`, `/sys`, `/boot`
- Log every executed command to SQLite with timestamp
- Timeout all commands at 30 seconds
- Return both stdout and stderr in the result

### `tools/app_controller.py`
Implement class `AppController`:
- `open_app(app_name: str)` → cross-platform app launcher (subprocess on Linux/macOS, os.startfile on Windows)
- `close_app(app_name: str)` → find process by name and terminate gracefully
- `list_running()` → return list of running process names using `psutil`
- `focus_app(app_name: str)` → bring window to foreground using `pyautogui` or `wmctrl` on Linux
- Handle platform detection (sys.platform) for all cross-platform calls

### `tools/skill_loader.py`
Implement class `SkillLoader`:
- On init, scan `SKILLS_DIR` for all `.py` files
- `import importlib.util` to dynamically load each skill module
- Each skill module must expose:
  - `SKILL_NAME: str`
  - `SKILL_DESCRIPTION: str` (used in LLM system prompt)
  - `execute(args: dict) -> str`
- Build a registry: `{skill_name: module}`
- Expose `get_skill_list()` → returns formatted string of all skills + descriptions
- Expose `run_skill(name, args)` → calls skill's `execute(args)`
- Watch `SKILLS_DIR` for new files using a background thread with `watchdog`; hot-reload without restarting the agent

### `memory/short_term.py`
- Class `ShortTermMemory` with a `deque(maxlen=SHORT_TERM_LIMIT)`
- `add(role, content)` → appends `{"role": role, "content": content}`
- `get_history()` → returns formatted string of conversation turns
- `clear()` → empties the buffer
- `to_list()` → returns the raw deque as a list (for serialization to SQLite)

### `memory/long_term.py`
Use `sqlite3` (stdlib, no extra deps):
- Auto-create `data/sovereign.db` on first run
- Tables:
  - `facts(id, key, value, timestamp)` — user preferences, name, etc.
  - `history(id, role, content, timestamp)` — all conversation turns ever
  - `command_log(id, command, output, timestamp)` — shell command history
- `save_fact(key, value)` → upsert into facts
- `get_fact(key)` → retrieve by key
- `save_turn(role, content)` → append to history
- `get_recent(n=50)` → last n turns from history
- `search_history(query)` → LIKE search over content

### `memory/vector_mem.py`
Use `chromadb`:
- Auto-create persistent client at `data/chroma/`
- Collection name: `"sovereign_memory"`
- `add(text: str, metadata: dict)` → embed and store using ChromaDB's default embedding
- `search(query: str, n=3)` → semantic search, return top-n results as list of strings
- `delete_all()` → wipe the collection
- Fall back gracefully if ChromaDB is not installed: log a warning and skip vector ops

### `output/tts_engine.py`
- Class `TTSEngine`
- If `TTS_ENGINE = "pyttsx3"`: use `pyttsx3`, set rate from config, speak in a background thread so it doesn't block the loop
- If `TTS_ENGINE = "coqui"`: use `TTS` from `TTS` package with `tts_models/en/ljspeech/tacotron2-DDC`
- `speak(text: str)` → non-blocking speech
- `stop()` → interrupt current speech
- `set_voice(voice_id)` → change voice (pyttsx3)

### `output/terminal_display.py`
Use `rich`:
- `show_response(text)` → print in a styled panel with agent name header
- `show_tool_call(tool, args)` → print in amber with tool icon
- `show_tool_result(result)` → print in green with result icon
- `show_error(msg)` → print in red
- `show_startup_banner(config)` → full startup card showing model, device, memory backends, skills loaded
- `show_listening()` → animated spinner: "Listening..."
- `show_thinking()` → animated spinner: "Thinking..."

---

## SYSTEM PROMPT ENGINEERING

The LLM must understand its tool interface perfectly. Include these canonical examples
in the system prompt as few-shot demonstrations:

**Example 1 — File organization:**
```
User: organize my downloads folder
Assistant: {"tool": "file_agent", "args": {"action": "organize_by_type", "path": "~/Downloads"}, "reply": "Organizing your Downloads folder by file type now."}
```

**Example 2 — Web search:**
```
User: what is the latest version of Python
Assistant: {"tool": "web_fetcher", "args": {"action": "search", "query": "latest Python version 2025"}, "reply": "Let me search that for you."}
```

**Example 3 — Shell command:**
```
User: how much disk space do I have left
Assistant: {"tool": "shell_exec", "args": {"command": "df -h ~"}, "reply": "Checking your disk usage now."}
```

**Example 4 — Pure conversation:**
```
User: what can you do
Assistant: {"tool": "none", "args": {}, "reply": "I can organize your files, search the web, run terminal commands, open applications, and learn new skills you teach me — all without leaving your machine."}
```

---

## REQUIREMENTS.TXT

Generate a complete `requirements.txt` with pinned versions for:
```
faster-whisper>=1.0.0
sounddevice>=0.4.6
numpy>=1.24.0
requests>=2.31.0
beautifulsoup4>=4.12.0
duckduckgo-search>=6.0.0
chromadb>=0.5.0
pyttsx3>=2.90
rich>=13.7.0
psutil>=5.9.0
watchdog>=4.0.0
pyautogui>=0.9.54
ollama>=0.2.0
```
Mark optional: `TTS>=0.22.0  # optional: Coqui TTS`

---

## INSTALL SCRIPTS

### `install.sh` (Linux/macOS)
```bash
#!/bin/bash
set -e
echo "Installing SOVEREIGN..."
# Check Python 3.10+
python3 --version
# Create virtualenv
python3 -m venv .venv
source .venv/bin/activate
# Install deps
pip install --upgrade pip
pip install -r requirements.txt
# Check Ollama
if ! command -v ollama &> /dev/null; then
  echo "Ollama not found. Installing..."
  curl -fsSL https://ollama.ai/install.sh | sh
fi
# Pull default model
ollama pull mistral
echo "Setup complete. Run: python main.py --voice"
```

### `install.bat` (Windows)
Equivalent batch script using `py -m venv`, `pip install`, and `winget` for Ollama if not found.

---

## SKILLS SYSTEM

### `skills/README.md`
Document the skill interface:
```
A skill is a plain Python file in the /skills folder.
It must define three things:

SKILL_NAME = "my_skill"
SKILL_DESCRIPTION = "What this skill does, in one sentence."

def execute(args: dict) -> str:
    # do something
    return "result string"

The agent will automatically detect and load your skill on startup (or hot-reload it if already running).
You can then ask the agent to use it by name or by describing what it does.
```

### `skills/example_skill.py`
A working example skill that:
- Is named `"weather_checker"`
- Accepts `{"city": "London"}` as args
- Fetches weather from `wttr.in/{city}?format=3` (no API key needed)
- Returns a formatted weather string
- Includes full inline comments explaining each part

---

## ERROR HANDLING RULES

Apply these rules everywhere:
1. **Never crash the agent loop.** All tool calls and LLM calls are wrapped in `try/except`
2. **Ollama not running** → print startup message with fix command, exit cleanly
3. **Whisper model not downloaded** → auto-download on first run (faster-whisper does this)
4. **No microphone found** → fall back to text input automatically, print warning
5. **ChromaDB not installed** → skip vector memory, log warning, continue
6. **Tool execution fails** → return error string to LLM as tool result so it can tell the user
7. **LLM returns invalid JSON** → IntentParser falls back gracefully
8. **File operation on protected path** → reject with explanation

---

## CROSS-PLATFORM REQUIREMENTS

- All file paths use `pathlib.Path` — no hardcoded `/` or `\`
- Platform detection: `sys.platform` for `linux`, `darwin`, `win32`
- `app_controller.py` and `tts_engine.py` have platform-specific branches
- `install.sh` and `install.bat` both provided
- Works on Python 3.10, 3.11, 3.12

---

## STARTUP SEQUENCE

When `python main.py --voice` is run, the terminal must show:

```
╔══════════════════════════════════════════╗
║           S O V E R E I G N             ║
║        Local AI Agent — v1.0.0          ║
╠══════════════════════════════════════════╣
║  Model      │ mistral (Ollama)           ║
║  STT        │ Whisper small (CPU)        ║
║  TTS        │ pyttsx3                    ║
║  Memory     │ SQLite + ChromaDB          ║
║  Skills     │ 1 loaded (weather_checker) ║
╠══════════════════════════════════════════╣
║  Wake word  │ "sovereign"                ║
║  Mode       │ Voice                      ║
╚══════════════════════════════════════════╝
  Listening... (say "sovereign" to activate)
```

---

## WHAT NOT TO DO

- Do NOT use OpenAI, Anthropic, Cohere, or any other cloud LLM API
- Do NOT use LangChain or LlamaIndex (build the agent loop from scratch)
- Do NOT use asyncio unless absolutely required (keep it synchronous and simple)
- Do NOT store any data outside the `data/` folder
- Do NOT make any outbound network calls except via `web_fetcher.py` and Ollama localhost
- Do NOT hard-code file paths — always use `pathlib` and `config.py`
- Do NOT skip error handling to save lines
- Do NOT generate placeholder code with `# TODO` — every function must be fully implemented

---

## FINAL INSTRUCTION

Generate every file listed in the file structure above, in full, with working code.
Start with `requirements.txt` and `config.py`, then `main.py`, then work through
`core/`, `input/`, `llm/`, `tools/`, `memory/`, `output/`, and finally `skills/`.

After all files are generated, print a final summary of:
- How to install (one command)
- How to start in voice mode
- How to start in text mode
- How to add a new skill
- How to change the LLM model

The system must work end-to-end with zero modification after `install.sh` completes.
