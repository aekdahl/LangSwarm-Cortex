class ReasonAboutCode(BaseCapability):
    """
    Capability for reasoning about the agent's own source code.
    """
    def __init__(self, code_search_tool):
        super().__init__(name="ReasonAboutCode", description="Analyze and reason about source code.")
        self.code_search_tool = code_search_tool

    def run(self, query):
        """
        Use the code search tool to analyze code relevant to the query.
        """
        code_snippets = self.code_search_tool.search(query)
        reasoning_prompt = f"Analyze the following code for '{query}':\n\n{code_snippets}"
        return reasoning_prompt
