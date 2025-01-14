from langswarm.memory import ChromaDBAdapter


class CapabilityRegistry:
    """
    Centralized registry for managing agent capabilities, extended with ChromaDB for querying.
    """
    def __init__(self, collection_name="capabilities_registry", persist_directory=None):
        """
        Initialize the CapabilityRegistry with ChromaDBAdapter for scalable storage.
        
        :param collection_name: Name of the ChromaDB collection for capabilities.
        :param persist_directory: Directory for persisting data (optional).
        """
        self.db_adapter = ChromaDBAdapter(collection_name=collection_name, persist_directory=persist_directory)

    def register_capability(self, capability: dict):
        """
        Register a new capability in the ChromaDB collection.
        
        :param capability: Dict with fields:
            - name (str): Name of the capability.
            - description (str): A description of the capability.
            - metadata (dict, optional): Additional metadata.
        """
        if not isinstance(capability, dict):
            raise ValueError("Capability must be a dictionary.")
        if "name" not in capability or "description" not in capability:
            raise ValueError("Capability must have 'name' and 'description' fields.")

        self.db_adapter.add_documents([{
            "key": capability["name"],
            "text": capability["description"],
            "metadata": capability.get("metadata", {})
        }])
        print(f"Capability '{capability['name']}' registered successfully.")

    def get_capability(self, capability_name: str):
        """
        Retrieve a capability by its name.
        
        :param capability_name: Name of the capability to retrieve.
        :return: Capability details if found, otherwise None.
        """
        results = self.db_adapter.query(query=capability_name, filters={"key": capability_name}, top_k=1)
        if results:
            result = results[0]
            return {
                "name": result["key"],
                "description": result["text"],
                "metadata": result.get("metadata", {})
            }
        return None

    def list_capabilities(self):
        """
        List all registered capabilities.
        
        :return: List of capabilities with names and descriptions.
        """
        capabilities = self.db_adapter.query(query="", top_k=100)
        return [{"name": cap["key"], "description": cap["text"]} for cap in capabilities]

    def query_capabilities(self, query: str, filters: dict = None, top_k: int = 5):
        """
        Query capabilities based on a description or metadata filters.
        
        :param query: Query string to match capability descriptions.
        :param filters: Metadata filters (optional).
        :param top_k: Number of results to retrieve.
        :return: List of matching capabilities.
        """
        results = self.db_adapter.query(query=query, filters=filters, top_k=top_k)
        return [
            {
                "name": res["key"],
                "description": res["text"],
                "metadata": res.get("metadata", {})
            }
            for res in results
        ]

    def delete_capability(self, capability_name: str):
        """
        Delete a capability by its name.
        
        :param capability_name: Name of the capability to delete.
        """
        self.db_adapter.delete([capability_name])
        print(f"Capability '{capability_name}' deleted successfully.")
