import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


class CapabilityRegistry:
    """
    A registry for managing agent-specific capabilities with semantic search support.
    Stores capabilities in a dictionary and uses embeddings for similarity-based queries.
    """

    def __init__(self, embedding_model=None):
        """
        Initialize the CapabilityRegistry.

        :param embedding_model: A callable that generates embeddings for a given text.
                                Defaults to SentenceTransformer's 'all-MiniLM-L6-v2'.
        """
        # Use the provided embedding model or load the default one
        self.included_capabilities = set()  # Tracks capabilities already introduced
        self.embedding_model = embedding_model or SentenceTransformer('all-MiniLM-L6-v2').encode
        self.capabilities = {}
        self.embeddings = {}

    def register_capability(self, capability_name: str, capability):
        """
        Register a new capability and generate its embedding.

        :param capability_name: Name of the capability to register.
        :param capability: A callable object or function representing the capability. 
                           It must have a `description` attribute.
        :raises ValueError: If the capability is already registered or lacks a description.
        """
        if capability_name in self.capabilities:
            raise ValueError(f"Capability '{capability_name}' is already registered.")
        if not hasattr(capability, "description"):
            raise ValueError(f"Capability '{capability_name}' must have a 'description' attribute.")
        
        self.capabilities[capability_name] = capability
        self.embeddings[capability_name] = self.embedding_model(capability.description)

    def get_capability(self, capability_name: str):
        """
        Retrieve a capability by its name.

        :param capability_name: Name of the capability to retrieve.
        :return: The registered capability if found, otherwise None.
        """
        return self.capabilities.get(capability_name)

    def list_capabilities(self):
        """
        List all registered capabilities.

        :return: A list of capability names.
        """
        return list(self.capabilities.keys())

    def remove_capability(self, capability_name: str):
        """
        Remove a capability by its name.

        :param capability_name: Name of the capability to remove.
        :raises ValueError: If the capability does not exist.
        """
        if capability_name not in self.capabilities:
            raise ValueError(f"Capability '{capability_name}' is not registered.")
        del self.capabilities[capability_name]
        del self.embeddings[capability_name]

    def search_capabilities(self, query: str, top_k: int = 5):
        """
        Search for capabilities using semantic similarity based on their descriptions.

        :param query: A string to match against capability descriptions.
        :param top_k: Number of top results to return.
        :return: A list of matching capabilities, sorted by similarity score.
        """
        query_embedding = self.embedding_model(query)
        capability_names = list(self.embeddings.keys())
        capability_embeddings = np.array([self.embeddings[name] for name in capability_names])

        # Compute cosine similarity
        similarities = cosine_similarity([query_embedding], capability_embeddings)[0]
        ranked_indices = np.argsort(similarities)[::-1][:top_k]

        # Mark these capabilities as included
        self.included_capabilities.update([capability_names[i] for i in ranked_indices])
        
        return [
            {
                "name": capability_names[i],
                "description": self.capabilities[capability_names[i]].description,
                "instruction": self.capabilities[capability_names[i]].instruction,
                #"score": similarities[i],
            }
            for i in ranked_indices
        ]

    def reset_context(self):
        """
        Reset the included capabilities, clearing the context.
        """
        self.included_capabilities.clear()
        print("Context reset: All included capabilities cleared.")