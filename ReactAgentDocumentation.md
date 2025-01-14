# Documentation: ReActAgent with Enhanced Features

## **Overview**
The `ReActAgent` is a specialized agent designed for workflows combining reasoning and acting (ReAct). This implementation supports tools and capabilities for enhanced functionality and flexibility. It parses input for actionable instructions (e.g., tools or capabilities), routes actions to the appropriate handlers, and returns structured responses.

---

## **Key Features**

### **1. Action Parsing (`_parse_action`)**
- Detects and extracts actionable commands from the reasoning phase.
- Supports tools and capabilities with structured input.

**Example Action Formats:**
- Tool Action:
  ```
  use tool:example_tool {"query": "example input"}
  ```
- Capability Action:
  ```
  use capability:example_capability {"key": "value"}
  ```

### **2. Action Routing (`_route_action`)**
- Dynamically routes parsed actions to the appropriate handler (tool or capability).
- Ensures that invalid actions are logged and gracefully handled.

### **3. Logging (`_log_event`)**
- Centralized logging for monitoring reasoning, actions, and errors.
- Logs metadata such as execution times and error messages.
- Integrated with `GlobalLogger` for consistent logging across the system.

### **4. Timeout Handling for Actions (`_execute_with_timeout`)**
- Prevents tools or capabilities from blocking workflows indefinitely.
- Configurable timeout ensures responsiveness even with external dependencies.

---

## **Code Structure**

### **Initialization**
```python
class ReActAgent(AgentWrapper, ToolMixin, BaseReAct):
    def __init__(self, name, agent, tools=None, tool_registry=None, capability_registry=None, memory=None, **kwargs):
        super().__init__(name, agent, tools=tools, tool_registry=tool_registry, memory=memory, **kwargs)
        self.capability_registry = capability_registry or CapabilityRegistry()
```
- **Parameters:**
  - `name`: Name of the agent.
  - `agent`: The underlying LLM or agent instance.
  - `tools`: Dictionary of tools available for the agent.
  - `tool_registry`: Optional tool registry for dynamic tool management.
  - `capability_registry`: Registry of capabilities available to the agent.
  - `memory`: Optional memory for context retention.

### **Chat Method**
```python
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
            return super().chat(result)
        elif status == 200:  # No action detected
            self._log_event(f"No action detected: {result}", "info")
            return agent_reply
        else:  # Action not found or other error
            self._log_event(f"Action Error: {result}", "error")
            return agent_reply
```
- **Workflow:**
  1. Handles both standard and ReAct-specific queries.
  2. Invokes `react()` for actionable queries detected in the agent's reasoning.
  3. Returns structured responses with status codes.

### **ReAct Workflow (`react`)**
```python
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
```
- **Workflow:**
  1. Parses the agent's reasoning for tools or capabilities.
  2. Routes the detected action and returns the result.
  3. If no action is detected, returns the reasoning as the final response.

### **Action Parsing**
```python
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
```
- Parses reasoning to identify tool or capability actions.
- Returns a tuple of action type, name, and parameters.

### **Action Routing**
```python
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
```
- Dynamically routes actions to tools or capabilities.
- Returns a success status (201) or a not-found error (404).

### **Timeout Handling**
```python
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
```
- Executes a handler with a configurable timeout to prevent long-running operations.

### **Logging**
```python
    def _log_event(self, message, level, **metadata):
        GlobalLogger.log_event(message=message, level=level, name="react_agent", metadata=metadata)
```
- Centralized logging for actions, reasoning, and errors.
- Uses `GlobalLogger` for consistent logging across modules.

---

## **Usage Examples**

### **1. Handling ReAct-Specific Queries**
```python
query = "use tool:example_tool {\"query\": \"example input\"}"
status, response = react_agent.chat(query)
print(f"Status: {status}, Response: {response}")
```

### **2. Standard Queries**
```python
query = "What is the latest in AI?"
status, response = react_agent.chat(query)
print(f"Status: {status}, Response: {response}")
```

### **3. Dynamic Tool or Capability Execution**
```python
reasoning = "use capability:example_capability {\"key\": \"value\"}"
status, response = react_agent.react(reasoning)
print(f"Status: {status}, Response: {response}")
```

---

## **Future Enhancements**
1. **Dynamic Tool and Capability Registration**:
   - Allow tools and capabilities to be added or removed dynamically during runtime.
2. **Advanced Action Parsing**:
   - Support nested or chained actions for more complex workflows.
3. **Enhanced Logging**:
   - Include additional metadata such as memory usage and API call counts.

---

Let me know if further details or refinements are required!

