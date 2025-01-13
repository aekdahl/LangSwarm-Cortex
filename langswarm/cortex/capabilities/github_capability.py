from langchain.tools import GitHubAPIWrapper
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from capabilities.base_capability import BaseCapability  # Assuming BaseCapability is defined.

class GitHubCodeCapability(BaseCapability):
    """
    A capability for fetching, digesting, and querying source code from GitHub.
    """
    def __init__(self, github_token, db_path="code_snippets"):
        super().__init__(
            name="GitHubCodeCapability",
            description="Fetch, digest, and query source code from GitHub repositories."
        )
        self.github_tool = GitHubAPIWrapper(github_access_token=github_token)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = Chroma(persist_directory=db_path, embedding_function=self.embeddings)

    def run(self, query, action="fetch_and_store", **kwargs):
        """
        Execute the capability's actions.
        :param query: str - The input query or repository details.
        :param action: str - The action to perform: 'fetch_and_store' or 'query_code'.
        :param kwargs: dict - Additional arguments for the action.
        :return: str or List[str] - The result of the action.
        """
        if action == "fetch_and_store":
            return self.fetch_and_store_code(**kwargs)
        elif action == "query_code":
            return self.search_code(query)
        else:
            raise ValueError(f"Unsupported action: {action}")

    def fetch_and_store_code(self, repo_name, file_path, branch="main"):
        """
        Fetch code from GitHub and store it in the vector database.
        :param repo_name: str - The GitHub repository name (e.g., 'owner/repo').
        :param file_path: str - The path to the file in the repository.
        :param branch: str - The branch to fetch from (default: 'main').
        :return: str - Success message.
        """
        file_content = self.github_tool.get_repo_content(repo_name=repo_name, path=file_path, branch=branch)
        if file_content["type"] != "file":
            raise ValueError("The specified path is not a file.")
        
        code = file_content["content"]
        metadata = {"repo": repo_name, "path": file_path, "branch": branch}
        chunks = self.text_splitter.split_text(code)
        self.vectorstore.add_texts(chunks, metadatas=[metadata] * len(chunks))
        return f"Code from {file_path} in {repo_name} (branch: {branch}) has been processed and stored."

    def search_code(self, query):
        """
        Search stored code snippets for relevant matches.
        :param query: str - The search query.
        :return: List[str] - Relevant code snippets.
        """
        results = self.vectorstore.similarity_search(query, k=5)
        return [result.page_content for result in results]
