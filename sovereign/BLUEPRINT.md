# SOVEREIGN Architecture Blueprint

## Core Flow
1. Input capture from microphone or text CLI.
2. PromptBuilder assembles system prompt + short-term memory + vector hits + skills.
3. OllamaClient streams completion.
4. IntentParser enforces JSON tool contract.
5. ToolRouter executes tool or skill.
6. Tool result can be fed back into Ollama for final response.
7. Response is rendered in terminal and spoken by TTS.
8. All turns persist to short-term, long-term SQLite, and vector memory.

## Reliability Rules
- Agent loop never crashes on tool errors.
- Every network/tool call uses timeout and try/except.
- Safe shell blocks destructive command patterns.
- Missing optional subsystems degrade gracefully.

## Data Layout
- SQLite: facts, history, command_log.
- Chroma: semantic memory collection sovereign_memory.
- Skills: hot-reload from skills/*.py using watchdog.
