from pathlib import Path

AGENT_NAME = "Sovereign"
LLM_MODEL = "mistral"
LLM_BASE_URL = "http://localhost:11434"
WHISPER_MODEL = "small"
WHISPER_DEVICE = "cpu"
TTS_ENGINE = "pyttsx3"
TTS_RATE = 175
WAKE_WORD = "sovereign"
SHORT_TERM_LIMIT = 20
LOG_LEVEL = "INFO"
SAFE_SHELL = True
SKILLS_DIR = "skills/"
DATA_DIR = "data/"

ROOT_DIR = Path(__file__).resolve().parent
SKILLS_PATH = (ROOT_DIR / SKILLS_DIR).resolve()
DATA_PATH = (ROOT_DIR / DATA_DIR).resolve()
CHROMA_PATH = (DATA_PATH / "chroma").resolve()
SQLITE_PATH = (DATA_PATH / "sovereign.db").resolve()
TRASH_PATH = (ROOT_DIR / ".trash").resolve()
