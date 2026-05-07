import traceback
from typing import Any, Dict


class ToolRouter:
    def __init__(self, tools: Dict[str, Any], skill_loader):
        self.tools = tools
        self.skill_loader = skill_loader

    def get_tool_names(self) -> list[str]:
        return list(self.tools.keys())

    def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        try:
            if self.skill_loader.has_skill(tool_name):
                return self.skill_loader.run_skill(tool_name, args)

            tool = self.tools.get(tool_name)
            if tool is None:
                return f"Unknown tool: {tool_name}"

            if hasattr(tool, "execute"):
                return str(tool.execute(args))

            action = args.get("action")
            if action and hasattr(tool, action):
                method = getattr(tool, action)
                call_args = {k: v for k, v in args.items() if k != "action"}
                return str(method(**call_args))

            return f"Tool {tool_name} cannot handle args: {args}"
        except Exception as exc:
            return f"Tool execution failed: {exc}\n{traceback.format_exc()}"
