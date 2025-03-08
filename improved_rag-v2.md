Here's the **Markdown documentation** for the **Full Pipeline: Query Re-Centering & Explicit Direction Separation with ChromaDB**. This includes a detailed explanation, setup instructions, and the complete code.

---

### **📌 Full Pipeline: Query Re-Centering & Explicit Direction Separation with ChromaDB**
> **A structured approach to improving retrieval in RAG by dynamically re-centering embeddings and enforcing functional separation using ChromaDB.**

---

## **🚀 Overview**
This pipeline integrates **ChromaDB** with **query re-centering** and **explicit direction separation**, ensuring:
- ✅ **Context-aware retrieval** by dynamically shifting embeddings **relative to the query**.
- ✅ **Functional separation** for semantically similar but functionally different terms.
- ✅ **Consistent embedding model usage** with a **global registry**.

---

## **📦 Setup Instructions**
### **1️⃣ Install Dependencies**
```bash
pip install chromadb sentence-transformers numpy
```

### **2️⃣ Import Required Libraries**
```python
import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer
```

---

## **🔹 1. Embedding Model Registry**
The **EmbeddingModelRegistry** ensures a **consistent embedding model** across indexing and querying.

```python
class EmbeddingModelRegistry:
    """Global registry for managing embedding models."""

    _instance = None  # Singleton instance
    _registry = {}  # Stores user-defined embedding models
    _default_model_name = "all-MiniLM-L6-v2"  # Default model

    PREDEFINED_MODELS = {
        "all-MiniLM-L6-v2": "Compact, efficient model for general-purpose text embeddings.",
        "multi-qa-mpnet-base-dot-v1": "Optimized for QA retrieval tasks.",
        "all-mpnet-base-v2": "Larger model for more accurate sentence embeddings.",
    }

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(EmbeddingModelRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, name, model):
        """Register a new embedding model."""
        if name in cls._registry:
            raise ValueError(f"Model '{name}' is already registered.")
        cls._registry[name] = model

    @classmethod
    def get_model(cls, name=None):
        """Retrieve an explicitly registered embedding model."""
        if name is None:
            name = cls._default_model_name
        if name in cls._registry:
            return cls._registry[name]
        raise ValueError(
            f"Model '{name}' is not registered. Available models: {list(cls._registry.keys())}.\n"
            f"Please register it using `EmbeddingModelRegistry.register(name, model_instance)`."
        )

    @classmethod
    def list_registered(cls):
        """List all user-registered models."""
        return list(cls._registry.keys())

    @classmethod
    def list_predefined(cls):
        """List all predefined models (must be registered before use)."""
        return cls.PREDEFINED_MODELS
```

---

## **🔹 2. Initialize ChromaDB & Index Documents**
We store documents **as vectors in ChromaDB** using our **global embedding model**.

```python
# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")  # Persistent storage
collection = chroma_client.get_or_create_collection(name="documents")

def embed_text(text):
    """Encodes text into a vector using the global model."""
    model = EmbeddingModelRegistry.get_model()
    return model.encode([text], normalize_embeddings=True)[0]  # Single embedding

# Example corpus (documents to store)
documents = [
    "A washing machine cleans clothes.",
    "A dryer removes moisture from clothes.",
    "A dishwasher cleans dishes automatically.",
    "An oven is used for baking food.",
    "A microwave oven heats food quickly."
]

# Register and use the default model
default_model = SentenceTransformer("all-MiniLM-L6-v2")
EmbeddingModelRegistry.register("all-MiniLM-L6-v2", default_model)

# Store documents in ChromaDB
for i, doc in enumerate(documents):
    embedding = embed_text(doc).tolist()
    collection.add(
        ids=[str(i)],
        embeddings=[embedding],
        metadatas=[{"text": doc}]
    )

print("✅ Documents added to ChromaDB.")
```

---

## **🔹 3. Querying ChromaDB with Re-Centering**
1. **Retrieve top-k nearest neighbors**.
2. **Re-center embeddings by subtracting the query vector**.
3. **Re-rank results**.

```python
def query_chroma(query, top_k=3):
    """Search for the top-k most relevant documents in ChromaDB."""
    query_embedding = embed_text(query)

    # Retrieve top-k initial results
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )

    # Extract document embeddings and metadata
    doc_embeddings = np.array(results["embeddings"][0])
    texts = [meta["text"] for meta in results["metadatas"][0]]

    # Step 1: Re-Center embeddings by subtracting the query vector
    recentered_embeddings = doc_embeddings - query_embedding

    # Step 2: Compute similarity in the re-centered space
    cosine_similarities = np.sum(recentered_embeddings * recentered_embeddings, axis=1)

    # Step 3: Rank results based on adjusted similarity
    ranked_indices = np.argsort(-cosine_similarities)

    # Print final ranked results
    print("\n🔍 **Final Ranked Results (Re-Centered Search)**:")
    for idx in ranked_indices:
        print(f"{texts[idx]} (Score: {cosine_similarities[idx]:.4f})")

# Example query
query_chroma("Appliance for cleaning clothes")
```

---

## **🔹 4. Apply Explicit Direction Separation (Post-Retrieval)**
Now, let’s adjust **functionally distinct** embeddings **post-retrieval**.

```python
# Define functionally distinct term pairs
functional_pairs = {
    "washing machine": "dryer",
    "dishwasher": "oven"
}

def apply_functional_separation(texts, doc_embeddings):
    """Adjusts retrieval scores using functional separation vectors."""
    penalties = np.zeros(len(texts))

    for term1, term2 in functional_pairs.items():
        emb1 = embed_text(term1)
        emb2 = embed_text(term2)
        direction_vector = emb1 - emb2  # Define the separation vector

        # Apply penalty if retrieved docs align with functional separation
        for i, emb in enumerate(doc_embeddings):
            projection = np.dot(emb, direction_vector)  # Projection along separation axis
            penalties[i] += np.abs(projection)  # Apply penalty

    return penalties

def score_functional_separation(term1, term2):
    """Uses an LLM to score how functionally different two terms are."""
    system_prompt = (
        "You are an AI assistant that evaluates functional similarity. "
        "On a scale of 0 to 1, where 0 means identical function and 1 means completely different, "
        "score the functional separation between these two words."
    )

    response = openai.ChatCompletion.create(
        model="gpt-4", 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Score the separation between '{term1}' and '{term2}'."}
        ]
    )
    
    score = float(response["choices"][0]["message"]["content"].strip())
    return score

# Example usage
term1 = "washing machine"
term2 = "dryer"
print(f"Functional separation score: {score_functional_separation(term1, term2)}")


def query_with_functional_separation(query, top_k=3):
    """Retrieves documents with query re-centering and applies functional separation."""
    query_embedding = embed_text(query)

    # Retrieve top-k initial results
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )

    # Extract embeddings and metadata
    doc_embeddings = np.array(results["embeddings"][0])
    texts = [meta["text"] for meta in results["metadatas"][0]]

    # Step 1: Re-Center embeddings
    recentered_embeddings = doc_embeddings - query_embedding

    # Step 2: Compute cosine similarity
    cosine_similarities = np.sum(recentered_embeddings * recentered_embeddings, axis=1)

    # Step 3: Apply Explicit Direction Separation
    penalties = apply_functional_separation(texts, doc_embeddings)
    final_scores = cosine_similarities - penalties  # Adjust scores

    # Step 4: Rank based on adjusted scores
    ranked_indices = np.argsort(-final_scores)

    # Print final ranked results
    print("\n🔍 **Final Ranked Results (Re-Centered & Functionally Separated)**:")
    for idx in ranked_indices:
        print(f"{texts[idx]} (Score: {final_scores[idx]:.4f})")

# Example query
query_with_functional_separation("Appliance for cleaning clothes")
```

---

## **📌 Next Steps**
🚀 **Integrate this into a full RAG pipeline.**  
🚀 **Test retrieval benchmarks (BEIR, MSMARCO).**  
🚀 **Optimize functional separation penalty scaling.**  

Would you like **persistent model storage** across sessions next? 🔥