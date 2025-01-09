class ReActAgent(AgentWrapper, ToolMixin, BaseReAct):
    """
    A specialized agent for ReAct workflows, combining tool management with reasoning and acting logic.
    """

    def __init__(self, name, agent, tools=None, tool_registry=None, memory=None, **kwargs):
        super().__init__(name, agent, tools=tools, tool_registry=tool_registry, memory=memory, **kwargs)

    def run_react(self, query: str) -> str:
        """
        Execute the ReAct loop: reason, act, and iterate until a final response is produced.
        """
        while True:
            # Reasoning phase
            reasoning = self.reason(query)
            self.memory.append({"role": "assistant", "content": reasoning})
            self.log_event(f"Reasoning: {reasoning}", "info")

            if "ACTION" in reasoning:
                # Parse action
                tool_name, args = self._parse_action(reasoning)
                # Acting phase
                try:
                    result = self.act((tool_name, args))
                    self.memory.append({"role": "system", "content": f"Action Result: {result}"})
                    self.log_event(f"Action Result: {result}", "info")
                except ValueError as e:
                    self.log_event(f"Action Error: {e}", "error")
                    break
            else:
                # If no action, return the reasoning as the final response
                return reasoning

    def _parse_action(self, reasoning: str) -> tuple:
        """
        Parse the action from reasoning into a tool name and arguments.
        """
        if "ACTION:" not in reasoning:
            raise ValueError("No actionable reasoning found.")
        action_str = reasoning.split("ACTION:")[1].strip()
        tool_name = action_str.split("(")[0]
        args = eval(action_str.split("(")[1][:-1])  # Simplistic argument parsing
        return tool_name, args

    def request_tool_from_registry(self, tool_name, registry: ToolRegistry):
        """
        Dynamically request a tool from the registry.
        """
        tool = registry.get_tool(tool_name)
        if tool:
            self.add_tool(tool)
            return f"Tool '{tool_name}' added successfully."
        return f"Tool '{tool_name}' not found in the registry."
