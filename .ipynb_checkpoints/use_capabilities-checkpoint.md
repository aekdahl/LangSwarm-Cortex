### EXAMPLE SYSTEM PROMPT (PART)
You are an advanced agent with access to tools and capabilities. To solve tasks:
1. Parse the query and decide whether to use a tool or capability.
2. If unsure, ask for an index of tools and capabilities using: "index tools" or "index capabilities".
3. Use a tool or capability by specifying its name, action, and parameters, like:
   - use tool:GitHubTool|fetch_code|{"file_path": "main.py"}


### Prompt to Explain `fetch_and_store_code` Using `GitHubCodeCapability`

The `GitHubCodeCapability` allows you to interact with GitHub repositories for managing and processing source code. To use the `fetch_and_store_code` action of this capability, follow these steps:

1. **Purpose**:
   - This action fetches a file or all files from a specified GitHub repository and branch.
   - The retrieved files are processed into smaller chunks and stored in a vector database for efficient search and retrieval.

2. **Required Inputs**:
   - `file_path` (str): The path to the file within the repository. If omitted, all files in the repository will be fetched recursively.
   - `branch` (str, optional): The branch to fetch files from. Defaults to `main`.

3. **Example Request**:
   To fetch a specific file from a repository:
   ```
   use capability:GitHubCodeCapability|fetch_and_store_code|{"file_path": "src/utils.py", "branch": "main"}
   ```

   To fetch all files from a repository:
   ```
   use capability:GitHubCodeCapability|fetch_and_store_code|{"branch": "main"}
   ```

4. **Expected Output**:
   - A success message confirming that the files have been fetched, processed, and stored in the database.
   - Example: `"Code from src/utils.py in repo_name (branch: main) has been processed and stored."`

5. **Error Handling**:
   - If the file path does not exist or is invalid, the capability will gracefully return a message indicating the issue.
   - Ensure the repository, branch, and file paths are correctly specified before sending the request.

6. **Agent Guidance**:
   - Use this capability to pre-process and store code for later querying or analysis.
   - If unsure of the file path or repository structure, start by fetching all files, then refine as needed.

**Key Action Format**:
```
use capability:GitHubCodeCapability|fetch_and_store_code|{"file_path": "<path_to_file>", "branch": "<branch_name>"}
```

Replace `<path_to_file>` with the actual file path, and `<branch_name>` with the desired branch (e.g., `main` or `feature/new_branch`). If fetching all files, omit the `file_path` key.
