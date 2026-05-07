from __future__ import annotations


class AgentLoop:
    def __init__(
        self,
        input_handler,
        prompt_builder,
        llm_client,
        intent_parser,
        tool_router,
        tts,
        display,
        short_term,
        long_term,
        vector_mem,
    ):
        self.input_handler = input_handler
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client
        self.intent_parser = intent_parser
        self.tool_router = tool_router
        self.tts = tts
        self.display = display
        self.short_term = short_term
        self.long_term = long_term
        self.vector_mem = vector_mem

    def run(self) -> None:
        while True:
            self.display.show_listening()
            user_text = self.input_handler.get_input()
            if not user_text:
                continue
            if user_text.lower() in {"exit", "quit"}:
                break

            self.short_term.add("user", user_text)
            self.long_term.save_turn("user", user_text)

            prompt = self.prompt_builder.build(user_text)
            self.display.show_thinking()
            try:
                raw = self.llm_client.complete(prompt)
            except Exception as exc:
                self.display.show_error(str(exc))
                continue
            intent = self.intent_parser.parse(raw)

            reply = intent["reply"]
            tool_name = intent["tool"]
            tool_args = intent["args"]

            if tool_name != "none":
                self.display.show_tool_call(tool_name, tool_args)
                tool_result = self.tool_router.execute(tool_name, tool_args)
                self.display.show_tool_result(tool_result)

                followup = self.prompt_builder.build_followup(user_text, tool_name, tool_result)
                try:
                    raw_followup = self.llm_client.complete(followup)
                    followup_intent = self.intent_parser.parse(raw_followup)
                    reply = followup_intent.get("reply", reply)
                except Exception as exc:
                    self.display.show_error(f"Follow-up generation failed: {exc}")

            self.display.show_response(reply)
            self.tts.speak(reply)
            self.short_term.add("assistant", reply)
            self.long_term.save_turn("assistant", reply)
            self.vector_mem.add(user_text, {"role": "user"})
            self.vector_mem.add(reply, {"role": "assistant"})
