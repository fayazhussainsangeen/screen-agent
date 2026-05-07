from __future__ import annotations

from typing import List


SYSTEM_PROMPT_TEMPLATE = """You are {agent_name}, a fully local AI agent running on this machine.
You have no internet access unless the web_fetcher tool is explicitly called.
You have access to the following tools: {tool_list}

You MUST always respond with valid JSON in this exact format:
{{\"tool\": \"<tool_name or none>\", \"args\": {{...}}, \"reply\": \"<your spoken reply>\"}}

The \"reply\" field is what gets spoken aloud to the user. Keep it concise and natural.
If using a tool, \"reply\" should tell the user what you are about to do.
If not using a tool, set \"tool\" to \"none\" and \"args\" to {{}}.

Relevant memories:
{injected_memories}

Conversation so far:
{conversation_history}
"""


FEW_SHOT_EXAMPLES = """
Example 1 - File organization:
User: organize my downloads folder
Assistant: {"tool": "file_agent", "args": {"action": "organize_by_type", "path": "~/Downloads"}, "reply": "Organizing your Downloads folder by file type now."}

Example 2 - Web search:
User: what is the latest version of Python
Assistant: {"tool": "web_fetcher", "args": {"action": "search", "query": "latest Python version 2025"}, "reply": "Let me search that for you."}

Example 3 - Shell command:
User: how much disk space do I have left
Assistant: {"tool": "shell_exec", "args": {"command": "df -h ~"}, "reply": "Checking your disk usage now."}

Example 4 - Pure conversation:
User: what can you do
Assistant: {"tool": "none", "args": {}, "reply": "I can organize your files, search the web, run terminal commands, open applications, and learn new skills you teach me - all without leaving your machine."}
"""


class PromptBuilder:
    def __init__(self, agent_name, short_term, long_term, vector_mem, tool_router, skill_loader):
        self.agent_name = agent_name
        self.short_term = short_term
        self.long_term = long_term
        self.vector_mem = vector_mem
        self.tool_router = tool_router
        self.skill_loader = skill_loader

    def build(self, user_text: str) -> str:
        memories = self._build_memories(user_text)
        history = self.short_term.get_history()
        tool_list = self.tool_router.get_tool_names() + self.skill_loader.get_skill_names()

        user_name = self.long_term.get_fact("user_name") or "User"
        preferences = self.long_term.get_fact("preferences") or "none"

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            agent_name=self.agent_name,
            tool_list=", ".join(tool_list),
            injected_memories=memories,
            conversation_history=history,
        )

        return (
            f"{system_prompt}\n"
            f"Known user name: {user_name}\n"
            f"Known user preferences: {preferences}\n\n"
            f"Available skills:\n{self.skill_loader.get_skill_list()}\n\n"
            f"{FEW_SHOT_EXAMPLES}\n"
            f"Current user request:\n{user_text}\n"
        )

    def build_followup(self, user_text: str, tool_name: str, tool_result: str) -> str:
        prompt = self.build(user_text)
        return (
            f"{prompt}\n"
            f"Tool execution result from {tool_name}:\n{tool_result}\n\n"
            "Now produce the final JSON response for the user."
        )

    def _build_memories(self, query: str) -> str:
        snippets: List[str] = []
        snippets.extend(self.vector_mem.search(query, n=3))
        if not snippets:
            return "none"
        return "\n".join(f"- {item}" for item in snippets)
