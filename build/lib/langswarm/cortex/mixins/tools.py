class ToolMixin:
    """
    A mixin for managing tools in an agent, supporting hybrid tool approaches.
    """

    def __init__(self, tools=None, tool_registry=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tools = tools or []  # Predefined tools
        self.tool_registry = tool_registry  # Centralized tool registry

    def add_tool(self, tool):
        """
        Add a tool (LangChain, LangSwarm, or custom) to the agent's toolset.
        """
        if hasattr(tool, "run") or hasattr(tool, "use"):
            self.tools.append(tool)
        else:
            raise TypeError("Tool must have a `run` or `use` method.")

    def list_tools(self):
        """
        List the names of all available tools.
        """
        return [tool.name for tool in self.tools]

    def request_tool(self, tool_name):
        """
        Dynamically fetch a tool from the registry and add it to the agent.
        """
        if self.tool_registry:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                self.add_tool(tool)
                return f"Tool '{tool_name}' added successfully."
            return f"Tool '{tool_name}' not found in the registry."
        return "No tool registry available."
