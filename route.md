# Implementation: Embedding-Based Similarity and Clustering for Routing

### **Overview**
This document provides a comprehensive implementation of **Embedding-Based Similarity** and **Clustering** for dynamic routing of queries to workflows or retrievers. The solution leverages **sentence embeddings** for semantic similarity and integrates clustering to adaptively group queries based on their semantic characteristics.

---

## **Embedding-Based Similarity for Routing**

### **Objective**
Match a query to the most relevant retriever or workflow based on semantic similarity.

### **Implementation**

#### Code: Embedding-Based Routing
```python
from sentence_transformers import SentenceTransformer, util

class EmbeddingBasedRouter:
    """
    Routes queries to the most relevant workflow based on semantic similarity.
    """
    def __init__(self, workflow_descriptions):
        """
        Initialize the router with workflow descriptions.
        :param workflow_descriptions: Dict[str, str] - A dictionary of workflow names and their descriptions.
        """
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.workflow_descriptions = workflow_descriptions
        self.workflow_embeddings = self.model.encode(list(workflow_descriptions.values()), convert_to_tensor=True)

    def route(self, query):
        """
        Match the query to the most relevant workflow.
        :param query: str - The input query.
        :return: Tuple[str, float] - The name of the selected workflow and the similarity score.
        """
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        similarities = util.cos_sim(query_embedding, self.workflow_embeddings)
        best_match_idx = similarities.argmax()
        workflow_name = list(self.workflow_descriptions.keys())[best_match_idx]
        return workflow_name, similarities[0][best_match_idx].item()
```

#### Example Usage
```python
# Define workflows
workflow_descriptions = {
    "legal_workflow": "Handles legal documents and case law.",
    "finance_workflow": "Processes financial data and investments.",
    "general_workflow": "Answers general knowledge queries."
}

# Initialize router
router = EmbeddingBasedRouter(workflow_descriptions)

# Query routing
query = "What are the top investments for 2023?"
selected_workflow, confidence = router.route(query)
print(f"Selected workflow: {selected_workflow} with confidence: {confidence}")
```

---

## **Clustering for Adaptive Routing**

### **Objective**
Group similar queries dynamically and assign clusters to specific workflows or retrievers.

### **Implementation**

#### Code: Clustering-Based Routing
```python
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer

class ClusterBasedRouter:
    """
    Routes queries to workflows based on clustering.
    """
    def __init__(self, n_clusters=3):
        """
        Initialize the clustering router.
        :param n_clusters: int - Number of clusters.
        """
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.kmeans = KMeans(n_clusters=n_clusters)
        self.cluster_map = {}

    def fit_clusters(self, query_logs, workflows):
        """
        Fit the clustering model on query embeddings and map clusters to workflows.
        :param query_logs: List[str] - Historical queries.
        :param workflows: List[str] - List of workflow names to associate with clusters.
        """
        embeddings = self.model.encode(query_logs)
        self.kmeans.fit(embeddings)
        cluster_labels = self.kmeans.labels_

        # Map clusters to workflows
        for cluster, workflow in zip(set(cluster_labels), workflows):
            self.cluster_map[cluster] = workflow

    def route(self, query):
        """
        Route a query based on its cluster.
        :param query: str - The input query.
        :return: str - The name of the selected workflow.
        """
        query_embedding = self.model.encode(query).reshape(1, -1)
        cluster_label = self.kmeans.predict(query_embedding)[0]
        return self.cluster_map.get(cluster_label, "general_workflow")
```

#### Example Usage
```python
# Historical queries
query_logs = [
    "What are legal precedents?",
    "How to invest in stocks?",
    "What is the weather like today?"
]

# Workflows
workflows = ["legal_workflow", "finance_workflow", "general_workflow"]

# Initialize and fit router
cluster_router = ClusterBasedRouter(n_clusters=3)
cluster_router.fit_clusters(query_logs, workflows)

# Query routing
query = "What are the legal implications of AI?"
retriever = cluster_router.route(query)
print(f"Selected workflow: {retriever}")
```

---

## **Combining Embedding Similarity and Clustering**

### **Objective**
Use embedding similarity for initial routing and clustering for adaptive refinement based on historical data.

### **Implementation**

#### Code: Hybrid Router
```python
class HybridRouter:
    """
    Combines embedding similarity and clustering for dynamic query routing.
    """
    def __init__(self, workflow_descriptions, n_clusters=3):
        """
        Initialize the hybrid router.
        :param workflow_descriptions: Dict[str, str] - Descriptions of workflows.
        :param n_clusters: int - Number of clusters.
        """
        self.embedding_router = EmbeddingBasedRouter(workflow_descriptions)
        self.cluster_router = ClusterBasedRouter(n_clusters=n_clusters)

    def fit_clusters(self, query_logs, workflows):
        """
        Fit the clustering model using historical queries and workflows.
        :param query_logs: List[str] - Historical queries.
        :param workflows: List[str] - Associated workflows.
        """
        self.cluster_router.fit_clusters(query_logs, workflows)

    def route(self, query):
        """
        Use embedding similarity for initial routing and fallback to clustering.
        :param query: str - The input query.
        :return: str - The selected workflow.
        """
        try:
            workflow, confidence = self.embedding_router.route(query)
            if confidence > 0.8:  # Confidence threshold
                return workflow
        except Exception:
            pass

        # Fallback to clustering
        return self.cluster_router.route(query)
```

#### Example Usage
```python
# Initialize hybrid router
hybrid_router = HybridRouter(workflow_descriptions, n_clusters=3)

# Fit clustering model
hybrid_router.fit_clusters(query_logs, workflows)

# Query routing
query = "Explain the best stocks to invest in for 2023."
workflow = hybrid_router.route(query)
print(f"Selected workflow: {workflow}")
```

---

## **Documentation**

### **1. Embedding-Based Router**
- **Purpose**: Match queries to workflows based on semantic similarity.
- **Strengths**: Works well for semantically rich queries.
- **Limitations**: Relies on well-defined workflow descriptions.

### **2. Clustering-Based Router**
- **Purpose**: Group queries into clusters and map them to workflows dynamically.
- **Strengths**: Adapts to new patterns in queries.
- **Limitations**: Requires sufficient historical data for clustering.

### **3. Hybrid Router**
- **Purpose**: Combine embedding similarity and clustering for robust routing.
- **Strengths**: Balances precision (embeddings) with adaptability (clustering).
- **Limitations**: Hybrid logic introduces complexity.

---

### **Next Steps**
1. **Testing**: Validate the hybrid router with diverse datasets.
2. **Feedback Loops**: Integrate mechanisms to refine routing decisions based on query outcomes.
3. **Scalability**: Optimize clustering and embedding models for larger datasets.

Would you like to expand this implementation further or focus on real-world integration? Let me know!

