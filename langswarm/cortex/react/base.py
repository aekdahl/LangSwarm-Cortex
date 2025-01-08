class BaseReAct:
    def __init__(self, llm):
        self.llm = llm  # LLM instance
        self.memory = []  # Memory to store reasoning and actions

    def reason(self, query):
        raise NotImplementedError("This method should be implemented in a subclass.")

    def act(self, action):
        raise NotImplementedError("This method should be implemented in a subclass.")

    def run(self, query):
        raise NotImplementedError("This method should be implemented in a subclass.")
