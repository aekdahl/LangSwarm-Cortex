class DocstringGenerator(RepositoryTool):
    def __init__(self, repo_adapter, llm_agent):
        """
        Initialize the Docstring Generator tool.
        Args:
            repo_adapter: Adapter for repository operations.
            llm_agent: LLM agent for generating docstrings.
        """
        super().__init__("Docstring Generator", "Creates detailed docstrings for all functions and classes.", repo_adapter)
        self.llm_agent = llm_agent

    def process_file(self, file_content):
        """
        Add docstrings to all functions and classes in the file content.
        Args:
            file_content (str): The content of the file.

        Returns:
            str: Modified file content with docstrings.
        """
        prompt = (
            "Analyze the following code and add detailed docstrings to all functions and classes. "
            "Describe their purpose, input parameters, outputs, and potential exceptions:\n\n"
            f"{file_content}"
        )
        return self.llm_agent.run(prompt)
