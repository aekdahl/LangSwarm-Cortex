class ReActAgent(AgentWrapper):
    """
    A specialized agent for ReAct workflows, inheriting from AgentWrapper.
    """

    def __init__(self, name, agent, tools=None, tool_registry=None, memory=None, **kwargs):
        super().__init__(name, agent, tools, tool_registry, memory, **kwargs)

    def reason(self, query: str) -> str:
        """
        Generate reasoning steps using the agent.
        """
        context = " ".join([message["content"] for message in self.in_memory]) if hasattr(self, "in_memory") else ""
        prompt = f"Context: {context}\n\nQuery: {query}\n\nThoughts:"
        return self.agent.invoke(prompt) if callable(self.agent) else self.agent.run(prompt)

    def act(self, action: tuple) -> Any:
        """
        Perform an action based on reasoning.
        """
        tool_name, args = action
        for tool in self.tools:
            if tool.name == tool_name:
                if hasattr(tool, "run"):  # LangChain tools
                    return tool.run(*args)
                elif hasattr(tool, "use"):  # Custom tools
                    return tool.use(*args)
        raise ValueError(f"Tool '{tool_name}' not found.")

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
