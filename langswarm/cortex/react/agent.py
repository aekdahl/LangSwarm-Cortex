class ReActAgent(AgentWrapper, ToolMixin, BaseReAct):
    """
    A specialized agent for workflows combining reasoning and acting (ReAct). This agent supports tools and capabilities
    for enhanced functionality and flexibility. It parses input for actionable instructions (e.g., tools or capabilities),
    routes actions to the appropriate handlers, and returns structured responses.
    """

    def __init__(self, name, agent, tools=None, tool_registry=None, capability_registry=None, memory=None, **kwargs):
        super().__init__(name, agent, tools=tools, tool_registry=tool_registry, memory=memory, **kwargs)
        self.capability_registry = capability_registry or CapabilityRegistry()

    def chat(self, query: str) -> tuple:
        """
        Handle both standard and ReAct-specific queries.
        :param query: str - The input query.
        :return: Tuple[int, str] - (status_code, response).
        """
        agent_reply = super().chat(query)
        status, result = self.react(agent_reply)
        
        if status == 201:  # Successful action execution
            self._log_event(f"Action Result: {result}", "info")
            return agent_reply = super().chat(result)
        elif status == 200:  # No action detected
            self._log_event(f"No action detected: {result}", "info")
            return agent_reply
        else:  # Action not found or other error
            self._log_event(f"Action Error: {result}", "error")
            return agent_reply

    def react(self, reasoning: str) -> tuple:
        """
        Execute the reasoning and acting workflow: parse the input for tools or capabilities, route the action,
        and return a structured response.
        :param reasoning: str - The input reasoning.
        :return: Tuple[int, str] - (status_code, response).
        """
        # Parse action
        action_details = self._parse_action(reasoning)
        if action_details:
            # Route action
            status, result = self._route_action(*action_details)
            return status, result
        else:
            # No action detected, return the reasoning as the final response
            return 200, reasoning

    def _parse_action(self, reasoning: str) -> tuple:
        """
        Parse the reasoning output to detect tool or capability actions.
        :param reasoning: str - The reasoning output containing potential actions.
        :return: Tuple[str, str, dict] or None - (action_type, action_name, params) if action detected, else None.
        """
        tool_match = re.match(r"use tool:\s*(\w+)\s*({.*})", reasoning, re.IGNORECASE)
        capability_match = re.match(r"use capability:\s*(\w+)\s*({.*})", reasoning, re.IGNORECASE)

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
        :param action_type: str - Type of action (tool or capability).
        :param action_name: str - Name of the action.
        :param params: dict - Parameters for the action.
        :return: Tuple[int, str] - (status_code, result).
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
        :param handler: callable - The action handler.
        :param params: dict - Parameters for the handler.
        :param timeout: int - Timeout in seconds.
        :return: str - The result of the handler.
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
        :param message: str - Log message.
        :param level: str - Log level.
        :param metadata: dict - Additional log metadata.
        """
        GlobalLogger.log_event(message=message, level=level, name="react_agent", metadata=metadata)
