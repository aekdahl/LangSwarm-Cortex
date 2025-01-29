import sys

try:
    import signal as LS_SIGNAL
except ImportError:
    LS_SIGNAL = None

import threading
import time
import json
import re

from langswarm.core.wrappers.generic import AgentWrapper
from ..mixins.tools import ToolMixin
from .base import BaseReAct
from ..registry.capabilities import CapabilityRegistry
from ..defaults.prompts.system import CapabilityInstructions

class ReActAgent(AgentWrapper, ToolMixin, BaseReAct):
    """
    A specialized agent for workflows combining reasoning and acting (ReAct). This agent supports tools and capabilities
    for enhanced functionality and flexibility. It parses input for actionable instructions (e.g., tools or capabilities),
    routes actions to the appropriate handlers, and returns structured responses.
    """

    def __init__(
        self, 
        name, 
        agent, 
        tools=None, 
        tool_registry=None, 
        capability_registry=None, 
        capability_instruction=None, 
        memory=None, 
        **kwargs
    ):
        # Validate that the provided agent is not already wrapped
        if isinstance(agent, AgentWrapper):
            raise ValueError(
                "ReActAgent cannot wrap an already wrapped AgentWrapper. "
                "Please provide a raw agent (e.g., LLM or LangChain agent) instead."
            )
        
        # Continue with normal initialization
        super().__init__(
            name, 
            agent, 
            tools=tools, 
            tool_registry=tool_registry, 
            memory=memory, 
            capability_instruction=capability_instruction or CapabilityInstructions,
            **kwargs
        )
        
        self.timeout = kwargs.get("timeout", 10)
        self.capability_registry = capability_registry or CapabilityRegistry()
        self.tool_command_regex = r"use tool:([a-zA-Z0-9_]+)\|([a-zA-Z0-9_]+)\|(\{[^}]*\})"
        self.capability_command_regex = r"use capability:([a-zA-Z0-9_]+)\|([a-zA-Z0-9_]+)\|(\{[^}]*\})"
        self.request_capability_regex = r"request:capabilities\|(.*)"
        self.ask_to_continue_regex = r"\[CAN I CONTINUE\?\]"

    def chat(self, query: str, max_iterations=3) -> str:
        """
        Handle both standard and ReAct-specific queries.
        :param query: str - The input query.
        :return: Tuple[int, str] - (status_code, response).
        """
        for _ in range(max_iterations):
            asked_to_continue = None
            agent_reply = super().chat(query)
            status, result = self.react(agent_reply)
            
            asked_to_continue = re.search(self.ask_to_continue_regex, agent_reply, re.IGNORECASE)
            if status != 201 and asked_to_continue:
                self._log_event(f"Approved continuation", "info")
                query = f"Please continue."
                continue

            if status == 201:  # Successful action execution
                self._log_event(f"Action Result: {result}", "info")
                #return status, super().chat(result)
                if result:
                    query = result # Use the retrieved action result
                else:
                    self._log_event(f"No result from action: {result}", "info")
                    return f"{agent_reply} + No result from action: {result}."
            elif status == 200:  # No action detected
                self._log_event(f"No action detected: {result}", "info")
                return agent_reply
            else:  # Action not found or other error
                self._log_event(f"Action Error: {result}", "error")
                return agent_reply

        self._log_event(f"Exhausted max iterations: {max_iterations}", "info")
        return agent_reply
    
    def react(self, reasoning: str) -> tuple:
        """
        Execute the reasoning and acting workflow: parse the input for tools or capabilities, route the action,
        and return a structured response.
        :param reasoning: str - The input reasoning.
        :return: Tuple[int, str] - (status_code, response).
        """
        
        action_details = self._parse_action(reasoning)
        if action_details:
            status, result = self._route_action(*action_details)
            return status, result

        return 200, reasoning

    def _parse_action(self, reasoning: str) -> tuple:
        """
        Parse the reasoning output to detect tool or capability actions.
        :param reasoning: str - The reasoning output containing potential actions.
        :return: Tuple[str, str, dict] or None - (action_type, action_name, params) if action detected, else None.
        """
        
        tool_match = re.search(self.tool_command_regex, reasoning, re.IGNORECASE)
        capability_match = re.search(self.capability_command_regex, reasoning, re.IGNORECASE)
        capability_request = re.search(self.request_capability_regex, reasoning, re.IGNORECASE)
        
        # Old checks
        #tool_match = re.match(r"use tool:\s*(\w+)\s*({.*})", reasoning, re.IGNORECASE)
        #capability_match = re.match(r"use capability:\s*(\w+)\s*({.*})", reasoning, re.IGNORECASE)

        try:
            if tool_match:
                tool_name = tool_match.group(1)
                action = tool_match.group(2)
                json_part = re.sub(r'(?<!\\)\n', '\\n', tool_match.group(3)) # Escape newlines
                arguments = json.loads(json_part)
                return "tool", tool_name, action, arguments
            if capability_match:
                capability_name = capability_match.group(1)
                action = capability_match.group(2)
                json_part = re.sub(r'(?<!\\)\n', '\\n', capability_match.group(3)) # Escape newlines
                arguments = json.loads(json_part)
                return "capability", capability_name, action, arguments
            if capability_request:
                capability_info = capability_request.group(1)
                return "capabilities", capability_info, "undefined", {}
        except (SyntaxError, ValueError, json.JSONDecodeError) as e:
            self._log_event(f"Failed to parse action: {e}", "warning")

        return None

    def _route_action(self, action_type, action_name, action, arguments):
        """
        Route actions to the appropriate handler with timeout handling.
        :param action_type: str - Type of action (tool or capability).
        :param action_name: str - Name of the action.
        :param params: dict - Parameters for the action.
        :return: Tuple[int, str] - (status_code, result).
        """
        handler = None

        # ToDo: handler will just be a dict, return the actual tool instead.
        # Handled for capabilities
        
        if action_type == "tool":
            handler = self.tools.get(action_name)
        elif action_type == "capability":
            handler = self.capability_registry.get_capability(action_name)
        elif action_type == "capabilities":
            handler = self.capability_registry.search_capabilities(action_name)
            return 201, json.dumps(handler)

        if handler:
            self._log_event(f"Executing: {action_name} - {action}", "info")
            return 201, self._execute_with_timeout(handler, action, arguments)

        self._log_event(f"Action not found: {action_type} - {action_name}", "error")
        return 404, f"{action_type.capitalize()} '{action_name}' not found."

    def _execute_with_timeout(self, handler, action, arguments):
        """
        Execute a handler with a timeout.
        :param handler: callable - The action handler.
        :param params: dict - Parameters for the handler.
        :return: str - The result of the handler.
        """
        self.timer = None
        def timeout_handler(signum, frame):
            raise TimeoutError("Action execution timed out.")

        if LS_SIGNAL and hasattr(LS_SIGNAL, "SIGALRM"):
            LS_SIGNAL.signal(LS_SIGNAL.SIGALRM, timeout_handler)
            LS_SIGNAL.alarm(self.timeout)
        else:
            # Fallback to threading.Timer for timeout handling
            def timer_handler():
                print("Execution timed out!")
                raise TimeoutError("Execution timed out!")

            # Create a timer to simulate timeout
            self.timer = threading.Timer(self.timeout, timer_handler)
            self.timer.start()

        try:
            start_time = time.time()
            result = handler.run(arguments, action=action)
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
            if LS_SIGNAL and hasattr(LS_SIGNAL, "SIGALRM"):
                LS_SIGNAL.alarm(0)
            elif self.timer and self.timer.is_alive():
                self.timer.cancel()
            
    def suggest_capabilities(self, query: str, top_k: int = 5):
        """
        Suggest capabilities relevant to a query using the capability registry.

        :param query: A string describing the task or need.
        :param top_k: Number of top suggestions to return.
        :return: A list of suggested capabilities with descriptions and similarity scores.
        """
        return self.capability_registry.search_capabilities(query, top_k=top_k)

    def _log_event(self, message, level, **metadata):
        """
        Log an event to GlobalLogger.
        :param message: str - Log message.
        :param level: str - Log level.
        :param metadata: dict - Additional log metadata.
        """
        self.log_event(f"ReAct agent {self.name}: {message}", level)    
        #GlobalLogger.log_event(message=message, level=level, name="react_agent", metadata=metadata)
