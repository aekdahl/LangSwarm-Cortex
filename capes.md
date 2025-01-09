# Capabilities Framework for Intelligent Agents

## **Overview**
This document provides a framework for implementing agent capabilities, including foundational capabilities such as **reasoning about code**, **query analysis**, and **goal tracking**. Additionally, it describes how capabilities and tools can collaborate, enabling capabilities to invoke tools for external functionalities.

---

## **Core Concepts**

### **Capabilities**
- Represent the internal abilities of the agent (e.g., reasoning, introspection, memory).
- Defined as modular components with a standardized interface.

### **Tools**
- Represent external functionalities (e.g., querying a database, performing a web search).
- Capabilities can invoke tools to extend their functionality.

---

## **Capabilities Framework**

### **1. Capability Base Class**
Defines the interface for all capabilities.

```python
class BaseCapability:
    """
    Base class for agent capabilities.
    """
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def run(self, query, **kwargs):
        """
        Execute the capability logic.
        :param query: str - The input query.
        :return: str - The capability's output.
        """
        raise NotImplementedError("Each capability must implement the run method.")
```

---

### **2. Capability Registry**
Manages all registered capabilities.

```python
class CapabilityRegistry:
    """
    Centralized registry for managing agent capabilities.
    """
    def __init__(self):
        self.capabilities = {}

    def register_capability(self, capability):
        """
        Register a new capability in the registry.
        :param capability: BaseCapability - The capability to register.
        """
        self.capabilities[capability.name] = capability

    def get_capability(self, capability_name):
        """
        Retrieve a capability by name.
        :param capability_name: str - The name of the capability.
        :return: BaseCapability or None - The matching capability.
        """
        return self.capabilities.get(capability_name, None)

    def list_capabilities(self):
        """
        List all registered capabilities.
        :return: List[Dict] - List of capability names and descriptions.
        """
        return [
            {"name": name, "description": cap.description}
            for name, cap in self.capabilities.items()
        ]
```

---

## **Prototype Capabilities**

### **1. Reasoning About Code**
This capability introspects and analyzes the agent’s source code.

```python
class ReasonAboutCode(BaseCapability):
    """
    Capability for reasoning about the agent's own source code.
    """
    def __init__(self, code_search_tool):
        super().__init__(name="ReasonAboutCode", description="Analyze and reason about source code.")
        self.code_search_tool = code_search_tool

    def run(self, query):
        """
        Analyze relevant code snippets for the query.
        :param query: str - The input query.
        :return: str - Analysis of the source code.
        """
        code_snippets = self.code_search_tool.search(query)
        reasoning_prompt = f"Analyze the following code for '{query}':\n\n{code_snippets}"
        return reasoning_prompt
```

---

### **2. Query Analysis**
Analyzes the intent and structure of a query to guide downstream workflows.

```python
class QueryAnalysis(BaseCapability):
    """
    Capability for analyzing queries to extract intent and structure.
    """
    def __init__(self):
        super().__init__(name="QueryAnalysis", description="Analyze query intent and structure.")

    def run(self, query):
        """
        Analyze the query and return its intent and entities.
        :param query: str - The input query.
        :return: str - Analysis result.
        """
        # Placeholder for intent detection and entity extraction
        intent = "Determine investment opportunities" if "invest" in query.lower() else "General inquiry"
        return f"Intent: {intent}\nQuery: {query}"
```

---

### **3. Goal Tracking**
Tracks goals and sub-goals to manage complex task workflows.

```python
class GoalTracking(BaseCapability):
    """
    Capability for tracking goals and sub-goals.
    """
    def __init__(self):
        super().__init__(name="GoalTracking", description="Track goals and sub-goals.")
        self.goals = []

    def run(self, query, goal=None):
        """
        Manage goals based on the query.
        :param query: str - The input query.
        :param goal: str or None - The goal to add or update.
        :return: str - Current goal status.
        """
        if goal:
            self.goals.append(goal)
        return f"Current Goals: {self.goals}"
```

---

## **Capability-Tool Collaboration**
Capabilities can invoke tools when external functionalities are required. For example, the `ReasonAboutCode` capability uses a `CodeSearchTool` to retrieve relevant code snippets.

### **Base Tool Interface**
Defines the interface for tools.

```python
class BaseTool:
    """
    Base class for tools.
    """
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def run(self, query):
        """
        Execute the tool functionality.
        :param query: str - The input query.
        :return: str - The tool's output.
        """
        raise NotImplementedError("Each tool must implement the run method.")
```

---

### **Code Search Tool Example**

```python
class CodeSearchTool(BaseTool):
    """
    A tool for searching code snippets.
    """
    def __init__(self, index_path):
        super().__init__(name="CodeSearchTool", description="Search source code for relevant snippets.")
        self.index_path = index_path

    def search(self, query):
        """
        Search the codebase for snippets matching the query.
        :param query: str - The input query.
        :return: str - Mocked code snippet result.
        """
        # Mocked search for simplicity
        return "def parse_actions(query):\n    # Example function to parse actions\n    pass"
```

---

## **Integration Example**

### **Setup**
```python
# Initialize capability registry
capability_registry = CapabilityRegistry()

# Define and register capabilities
code_search_tool = CodeSearchTool(index_path="path_to_code_index")
reason_about_code_capability = ReasonAboutCode(code_search_tool=code_search_tool)
query_analysis_capability = QueryAnalysis()
goal_tracking_capability = GoalTracking()

capability_registry.register_capability(reason_about_code_capability)
capability_registry.register_capability(query_analysis_capability)
capability_registry.register_capability(goal_tracking_capability)
```

### **Usage**
```python
# Use capabilities
query = "Analyze the function to parse actions."
response = reason_about_code_capability.run(query)
print(response)

query = "What are the top investment strategies?"
response = query_analysis_capability.run(query)
print(response)

query = "Add a new goal."
response = goal_tracking_capability.run(query, goal="Develop investment strategies workflow")
print(response)
```

---

## **Future Directions**
1. **Feedback Loops**:
   - Allow capabilities to learn from tool outputs and refine their reasoning.

2. **Advanced Collaboration**:
   - Enable multiple capabilities to collaborate on a single task.

3. **Dynamic Capability Loading**:
   - Dynamically add new capabilities at runtime.

Would you like to explore specific extensions or test scenarios for these capabilities?

