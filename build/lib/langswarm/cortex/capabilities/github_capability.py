import json

from langchain_community.utilities.github import GitHubAPIWrapper
from .base import BaseCapability

class GitHubCodeCapability(BaseCapability):
    """
    A capability for interacting with GitHub repositories to fetch, update, and manage source code.
    
    This capability allows the agent to:
    - Fetch code files or repositories from GitHub and store them in a vector database for efficient querying.
    - Query and retrieve relevant code snippets from stored data.
    - Create, update, and delete files in GitHub repositories.
    - Create branches and pull requests to manage code contributions.
    
    Use cases:
    - Extracting code for analysis or retrieval.
    - Updating files with comments, docstrings, or refactored code.
    - Creating new branches or pull requests for code changes.
    
    """
    def __init__(
        self, 
        github_repository, 
        github_app_id, 
        github_app_private_key,
        adapter
    ):
        super().__init__(
            name="GitHubCodeCapability",
            description=(
                f"Use this capability to interact with the GitHub repository `{github_repository.split('/')[-1]}`, "
                f"owned by `{github_repository.split('/')[0]}`. The connection is already configured and ready. "
                "Supports fetching files and write them to database, creating branches, pull requests, and file operations."
            ),
            instruction="""
- **Actions and Parameters**:
    - `fetch_and_store`: Fetch and index code for querying.
      - IMPORTANT!:
        - Generate the complete content of the file without using ellipses (...) or truncating any sections. Include all required code or text, and ensure it is self-contained and ready to be uploaded to GitHub.
      - Parameters:
        - `file_path` (str, optional): Path to a specific file. Defaults to all files.
        - `branch` (str, optional): Branch to fetch from. Defaults to `main`.

    - `create_branch`: Create a new branch in the repository.
      - Parameters:
        - `proposed_branch_name` (str): Desired name for the new branch.

    - `create_pull_request`: Create pull requests for contributions.
      - Parameters:
        - `pr_query` (str): Title and body for the PR. First line is the title, remaining lines are the body.

    - `read_file`: Read the content of a file.
      - Parameters:
        - `file_path` (str): Path to the file in the repository.

    - `create_file`: Add a new file to the repository.
      - IMPORTANT:
        - Generate the complete content of the file without using ellipses (...) or truncating any sections. Include all required code or text, and ensure it is self-contained and ready to be uploaded to GitHub.
        - Make sure to separate the path and the content with a linebreak (\n)
      - Parameters:
        - `file_query` (str): File path and content. First line is the path, remaining lines are content.

    - `update_file`: Update existing file content.
      - IMPORTANT! Do not truncate Old or New content.
        - Make sure to separate the path and the content with a linebreak (\n)
      - Parameters:
        - `file_query` (str): File path, old content, and new content.
          - File path: The path to the file ending with a new line.
          - Old content: Wrapped in `OLD <<<<` and `>>>> OLD`.
          - New content: Wrapped in `NEW <<<<` and `>>>> NEW`.
      - For example:
        /test/hello.txt
        OLD <<<< Hello Earth! >>>> OLD
        NEW <<<< Hello Mars! >>>> NEW

    - `replace_file`: Replace an entire file in the repository.
      - IMPORTANT!:
        - Generate the complete content of the file without using ellipses (...) or truncating any sections. Include all required code or text, and ensure it is self-contained and ready to be uploaded to GitHub.
        - If you are only doing minor updates to a file, consider using `update_file` instead.
        - Make sure to separate the path and the content with a linebreak (\n)
      - Parameters:
        - `file_query` (str): File path and content. First line is the path, remaining lines are content.

    - `delete_file`: Delete a file.
      - Parameters:
        - `file_path` (str): Path to the file to be deleted.

    - `set_active_branch`: Set the active branch to work on.
      - Parameters:
        - `branch` (str, optional): Branch to set as active. Defaults to `main`.

    - `list_branches_in_repo`: Get all branches in repo.
      - No parameters required

    - `list_all_files`: List all files in a directory or from root.
      - Parameters:
        - `file_path` (str, optional): Path to a specific directory. Defaults to root.
        - `branch` (str, optional): Branch to fetch from. Defaults to `main`.
        
- **Agent query format**:
  ```
  use capability:name|action|{"param1": "value1", "param2": "value2"}
  ```
  Replace `name`, `action` and parameters as needed.

Example:
- To fetch and store all files:
  ```
  use capability:github_capability|fetch_and_store|{"branch": "main"}
  ```
        """
        )
        self.github_tool = GitHubAPIWrapper(
            github_repository=github_repository, 
            github_app_id=github_app_id, 
            github_app_private_key=github_app_private_key
        )

        self.vectorstore = adapter

    def run(self, payload, action="fetch_and_store"):
        """
        Execute the capability's actions.
        :param payload: str or dict - The input query or tool details.
        :param action: str - The action to perform: 'fetch_and_store' or 'query_code'.
        :return: str or List[str] - The result of the action.
        """
        if action == "fetch_and_store":
            return self.fetch_and_store_code(**payload)
        elif action == "create_branch":
            return self.create_branch(**payload)
        elif action == "create_pull_request":
            return self.create_pull_request(**payload)
        elif action == "read_file":
            return self.read_file(**payload)
        elif action == "create_file":
            return self.create_file(**payload)
        elif action == "update_file":
            return self.update_file(**payload)
        elif action == "delete_file":
            return self.delete_file(**payload)
        elif action == "set_active_branch":
            return self.set_active_branch(**payload)
        elif action == "list_all_files":
            return self.list_all_files(**payload)
        elif action == "replace_file":
            return self.replace_file(**payload)
        elif action == "list_branches_in_repo":
            return self.list_branches_in_repo(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
       
    def set_active_branch(self, branch="main"):
        """
        Set the active branch.
        :param branch: str - The branch to fetch from (default: 'main').
        :return: str - Success message.
        """
        action = self.github_tool.set_active_branch(branch_name=branch)
        print(action)
        return action
    
    def list_branches_in_repo(self):
        """
        List all branches.
        :return: str - String of branches.
        """
        action = self.github_tool.list_branches_in_repo()
        print(action)
        return action
    
    def create_pull_request(self, pr_query):
        """
        Makes a pull request from the bot's branch to the base branch
        Parameters:
            pr_query(str): a string which contains the PR title
            and the PR body. The title is the first line
            in the string, and the body are the rest of the string.
            For example, "Updated README\nmade changes to add info"
        Returns:
            str: A success or failure message
        """
        action = self.github_tool.create_pull_request(pr_query)
        print(action)
        return action
        
    def read_file(self, file_path):
        """
        Read a file from the repository in a case-insensitive manner.
        Read a file from this agent's branch, defined by self.active_branch,
        which supports PR branches.
        Parameters:
            file_path(str): the file path
        Returns:
            str: The file decoded as a string, or an error message if not found
        """
        # Extract the directory and file name
        directory = "/".join(file_path.split("/")[:-1])  # Get the directory path (if any)
        file_name = file_path.split("/")[-1]            # Get the file name

        # Get all files in the directory
        contents = self.github_tool.github_repo_instance.get_contents(directory or "")
   
        for content_file in contents:
            if content_file.name.lower() == file_name.lower():
                file_content = self.github_tool.read_file(file_path=content_file.path)
                return file_content  # Return the matching file object

        return 'File not found'
        
    def create_file(self, file_query):
        """
        Creates a new file on the Github repo
        Parameters:
            file_query(str): a string which contains the file path
            and the file contents. The file path is the first line
            in the string, and the contents are the rest of the string.
            For example, "hello_world.md\n# Hello World!"
        Returns:
            str: A success or failure message
        """
        action = self.github_tool.create_file(file_query)
        print(action)
        return action
        
    def update_file(self, file_query):
        """
        Updates a file with new content.
        Parameters:
            file_query(str): Contains the file path and the file contents.
                The old file contents is wrapped in OLD <<<< and >>>> OLD
                The new file contents is wrapped in NEW <<<< and >>>> NEW
                For example:
                /test/hello.txt
                OLD <<<<
                Hello Earth!
                >>>> OLD
                NEW <<<<
                Hello Mars!
                >>>> NEW
        Returns:
            A success or failure message
        """
        action = self.github_tool.update_file(file_query)
        print(action)
        return action
    
    def replace_file(self, file_query):
        """
        Updates an entire file in the Github repo
        Parameters:
            file_query(str): a string which contains the file path
            and the file contents. The file path is the first line
            in the string, and the contents are the rest of the string.
            For example, "hello_world.md\n# Hello World!"
        Returns:
            str: A success or failure message
        """
        file_path: str = file_query.split("\n", 1)[0]
        file_content: str = file_query.split("\n", 1)[-1]
        action = self.github_tool.github_repo_instance.update_file(
            path=file_path,
            message="Update " + str(file_path),
            content=file_content,
            branch=self.github_tool.active_branch,
            sha=self.github_tool.github_repo_instance.get_contents(
                file_path, ref=self.github_tool.active_branch
            ).sha,
        )
        print(action)
        return action
        
    def delete_file(self, file_path):
        """
        Deletes a file from the repo
        Parameters:
            file_path(str): Where the file is
        Returns:
            str: Success or failure message
        """
        action = self.github_tool.delete_file(file_path)
        print(action)
        return action

    def create_branch(self, proposed_branch_name):
        """
        Create a new branch, and set it as the active bot branch.
        Equivalent to `git switch -c proposed_branch_name`
        If the proposed branch already exists, we append _v1 then _v2...
        until a unique name is found.

        Returns:
            str: A plaintext success message.
        """
        action = self.github_tool.create_branch(proposed_branch_name)
        print(action)
        return action

    def _read_and_store(self, file_path, branch="main"):
        file_content = self.github_tool.read_file(file_path=file_path.path)
        metadata = {"repo": self.github_tool.github_repository, "path": file_path.path, "branch": branch}
        document = {"key": file_path.path, "text": file_content, "metadata": metadata}
        self.vectorstore.add_documents([document])
        print(f"Code from {file_path.path} in {self.github_tool.github_repository} (branch: {branch}) has been processed and stored.")

    def fetch_and_store_code(self, file_path=None, branch="main"):
        """
        Fetch code from GitHub and store it in the vector database.
        :param file_path: str - The path to the file in the repository.
        :param branch: str - The branch to fetch from (default: 'main').
        :return: str - Success message.
        """
        print(self.github_tool.set_active_branch(branch_name=branch))
        if file_path:
            self._read_and_store(file_path, branch=branch)
        else:
            contents = self.github_tool.github_repo_instance.get_contents("")
            while contents:
                file_path = contents.pop(0)
                if file_path.type == "dir":
                    contents.extend(self.github_tool.github_repo_instance.get_contents(file_path.path))
                else:
                    self._read_and_store(file_path, branch=branch)
        
        return 'done'

    def list_all_files(self, file_path=None, branch="main"):
        """
        Fetch code from GitHub and store it in the vector database.
        :param file_path: str - The path to the file in the repository.
        :param branch: str - The branch to fetch from (default: 'main').
        :return: str - Success message.
        """
        print(self.github_tool.set_active_branch(branch_name=branch))
        files = []
        
        if file_path:
            # Extract the directory and file name
            directory = "/".join(file_path.split("/")[:-1])  # Get the directory path (if any)
            file_name = file_path.split("/")[-1]            # Get the file name

            # Get all files in the directory
            contents = self.github_tool.github_repo_instance.get_contents(directory or "")
        else:
            # Get all files
            contents = self.github_tool.github_repo_instance.get_contents("")
            
        while contents:
            file_path = contents.pop(0)
            if file_path.type == "dir":
                contents.extend(self.github_tool.github_repo_instance.get_contents(file_path.path))
            else:
                files.append(file_path.path)
        
        return json.dumps(files)