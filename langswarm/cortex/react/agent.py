class ReActAgent(AgentWrapper, ToolMixin, BaseReAct):
    """
    A specialized agent for ReAct workflows, combining tool management with reasoning and acting logic.
    """

    def __init__(self, name, agent, tools=None, tool_registry=None, capability_registry=None, memory=None, **kwargs):
        super().__init__(name, agent, tools=tools, tool_registry=tool_registry, memory=memory, **kwargs)
        self.capability_registry = capability_registry or CapabilityRegistry()

    def chat(self, query: str) -> str:
        """
        Handle both standard and ReAct-specific queries.
        """
        if query.startswith("REACT:"):
            # Route to ReAct workflow
            return self.react(query[len("REACT:"):].strip())
        else:
            # Default behavior from AgentWrapper
            return super().chat(query)

    def react(self, query: str) -> str:
        """
        Execute the ReAct loop: reason, act, and iterate until a final response is produced.
        """
        while True:
            # Reasoning phase
            reasoning = self.reason(query)
            self.memory.append({"role": "assistant", "content": reasoning})
            self._log_event(f"Reasoning: {reasoning}", "info")

            # Parse action
            action_details = self._parse_action(reasoning)
            if action_details:
                # Route action
                status, result = self._route_action(*action_details)
                if status == 201:  # Successful execution
                    self.memory.append({"role": "system", "content": f"Action Result: {result}"})
                    self._log_event(f"Action Result: {result}", "info")
                elif status == 404:  # Action not found
                    self._log_event(f"Action Error: {result}", "error")
                    return result
            else:
                # If no action detected, return the reasoning as the final response
                return reasoning

    def _parse_action(self, reasoning: str) -> tuple:
        """
        Parse the action from reasoning into a tool name and arguments.
        """
        tool_match = re.match(r"ACTION:\s*tool:(\w+)\s*({.*})", reasoning)
        capability_match = re.match(r"ACTION:\s*capability:(\w+)\s*({.*})", reasoning)

        try:
            if tool_match:
                action_name, params = tool_match.groups()
                return "tool", action_name.strip(), eval(params)
            if capability_match:
                action_name, params = capability_match.groups()
                return "capability", action_name.strip(), eval(params)
        except (SyntaxError, ValueError) as e:
            self._log_event(f"Failed to parse action: {e}", "warning")

        return None

    def _route_action(self, action_type, action_name, params):
        """
        Route actions to the appropriate handler with timeout handling.
        """
        handler = None

        if action_type == "tool":
            handler = self.tools.get(action_name)
        elif action_type == "capability":
            handler = self.capability_registry.get_capability(action_name)

        if handler:
            return 201, self._execute_with_timeout(handler, params)

        self._log_event(f"Action not found: {action_name}", "error")
        return 404, f"{action_type.capitalize()} '{action_name}' not found."

    def _execute_with_timeout(self, handler, params, timeout=10):
        """
        Execute a handler with a timeout.
        """
        def timeout_handler(signum, frame):
            raise TimeoutError("Action execution timed out.")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        try:
            start_time = time.time()
            result = handler(**params)
            execution_time = time.time() - start_time
            self._log_event("Action executed successfully", "info", execution_time=execution_time)
            return result
        except TimeoutError:
            self._log_event("Action execution timed out", "error")
            return "The action timed out."
        except Exception as e:
            self._log_event(f"Error executing action: {e}", "error")
            return f"An error occurred: {e}"
        finally:
            signal.alarm(0)

    def _log_event(self, message, level, **metadata):
        """
        Log an event to GlobalLogger.
        """
        GlobalLogger.log_event(message=message, level=level, name="react_agent", metadata=metadata)
