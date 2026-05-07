import argparse
import logging
import sys

import config
from core.agent_loop import AgentLoop
from core.intent_parser import IntentParser
from core.prompt_builder import PromptBuilder
from core.tool_router import ToolRouter
from input.text_input import TextInput
from input.voice_listener import VoiceListener
from llm.ollama_client import OllamaClient
from memory.long_term import LongTermMemory
from memory.short_term import ShortTermMemory
from memory.vector_mem import VectorMemory
from output.terminal_display import TerminalDisplay
from output.tts_engine import TTSEngine
from tools.app_controller import AppController
from tools.file_agent import FileAgent
from tools.shell_exec import ShellExecutor
from tools.skill_loader import SkillLoader
from tools.web_fetcher import WebFetcher


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SOVEREIGN local AI agent")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--voice", action="store_true", help="Use microphone input")
    mode.add_argument("--text", action="store_true", help="Use keyboard input")
    parser.add_argument("--model", type=str, help="Override Ollama model")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, logging.INFO))

    if args.model:
        config.LLM_MODEL = args.model

    display = TerminalDisplay(config.AGENT_NAME)
    long_term = LongTermMemory(config.SQLITE_PATH)
    short_term = ShortTermMemory(config.SHORT_TERM_LIMIT)
    vector_mem = VectorMemory(config.CHROMA_PATH)

    skill_loader = SkillLoader(config.SKILLS_PATH)
    ollama_client = OllamaClient(base_url=config.LLM_BASE_URL, model=config.LLM_MODEL)
    tools = {
        "file_agent": FileAgent(config.TRASH_PATH),
        "web_fetcher": WebFetcher(llm_client=ollama_client),
        "shell_exec": ShellExecutor(long_term, safe_shell=config.SAFE_SHELL),
        "app_controller": AppController(),
    }

    parser = IntentParser()
    router = ToolRouter(tools=tools, skill_loader=skill_loader)
    prompt_builder = PromptBuilder(
        agent_name=config.AGENT_NAME,
        short_term=short_term,
        long_term=long_term,
        vector_mem=vector_mem,
        tool_router=router,
        skill_loader=skill_loader,
    )

    tts = TTSEngine(config.TTS_ENGINE, rate=config.TTS_RATE)

    input_handler = TextInput()
    mode = "Text"
    if args.voice:
        try:
            input_handler = VoiceListener(
                model_size=config.WHISPER_MODEL,
                device=config.WHISPER_DEVICE,
                wake_word=config.WAKE_WORD,
            )
            mode = "Voice"
        except Exception as exc:
            display.show_error(f"No microphone found or voice init failed, falling back to text mode: {exc}")

    display.show_startup_banner(
        {
            "model": config.LLM_MODEL,
            "stt": f"Whisper {config.WHISPER_MODEL} ({config.WHISPER_DEVICE})",
            "tts": config.TTS_ENGINE,
            "memory": vector_mem.backend_name,
            "skills": skill_loader.count,
            "wake_word": config.WAKE_WORD or "always-on",
            "mode": mode,
        }
    )

    loop = AgentLoop(
        input_handler=input_handler,
        prompt_builder=prompt_builder,
        llm_client=ollama_client,
        intent_parser=parser,
        tool_router=router,
        tts=tts,
        display=display,
        short_term=short_term,
        long_term=long_term,
        vector_mem=vector_mem,
    )

    try:
        loop.run()
    except KeyboardInterrupt:
        display.show_response("Shutting down cleanly. Goodbye.")
    finally:
        for turn in short_term.to_list():
            long_term.save_turn(turn["role"], turn["content"])
        tts.stop()
        skill_loader.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
