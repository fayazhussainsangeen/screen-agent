A skill is a plain Python file in the /skills folder.
It must define three things:

SKILL_NAME = "my_skill"
SKILL_DESCRIPTION = "What this skill does, in one sentence."

def execute(args: dict) -> str:
    # do something
    return "result string"

The agent will automatically detect and load your skill on startup (or hot-reload it if already running).
You can then ask the agent to use it by name or by describing what it does.
