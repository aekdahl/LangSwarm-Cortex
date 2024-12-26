import numpy as np
import datasets
from sklearn.metrics import accuracy_score, classification_report

class MMLUBenchmark:
    """
    Evaluates performance on the Massive Multitask Language Understanding (MMLU) benchmark.
    """
    def __init__(self):
        self.dataset = datasets.load_dataset("mmlu")

    def evaluate(self, model, subject="math", subset="high_school"):
        """
        Evaluates a model on a specific MMLU subject and subset.
        
        :param model: A callable model that accepts a prompt and returns a response.
        :param subject: Subject to evaluate (e.g., "math").
        :param subset: Subset to evaluate (e.g., "high_school").
        :return: Accuracy score.
        """
        data = self.dataset[subject][subset]
        predictions = [model(question) for question in data["questions"]]
        accuracy = accuracy_score(data["answers"], predictions)
        return accuracy

class TruthfulQA:
    """
    Evaluates performance on TruthfulQA, which measures factual accuracy and avoiding hallucination.
    """
    def __init__(self):
        self.dataset = datasets.load_dataset("truthful_qa")

    def evaluate(self, model, subset="mc"):
        """
        Evaluates a model on the TruthfulQA benchmark.
        
        :param model: A callable model that accepts a prompt and returns a response.
        :param subset: Evaluation subset (e.g., "mc" for multiple-choice).
        :return: Accuracy score.
        """
        data = self.dataset[subset]
        predictions = [model(question) for question in data["questions"]]
        accuracy = accuracy_score(data["answers"], predictions)
        return accuracy

class SuperGLUE:
    """
    Evaluates performance on SuperGLUE tasks.
    """
    def __init__(self, task_name):
        """
        Initializes the SuperGLUE dataset loader for a specific task.
        
        :param task_name: Name of the SuperGLUE task (e.g., "boolq").
        """
        self.dataset = datasets.load_dataset("super_glue", task_name)
        self.task_name = task_name

    def evaluate(self, model, split="validation"):
        """
        Evaluates a model on a specific SuperGLUE task.
        
        :param model: A callable model that accepts a prompt and returns a response.
        :param split: Dataset split to use (e.g., "validation").
        :return: Accuracy score or classification report depending on the task.
        """
        data = self.dataset[split]
        predictions = [model(question) for question in data["question"]]
        if "label" in data:
            accuracy = accuracy_score(data["label"], predictions)
            return accuracy
        else:
            return classification_report(data["answers"], predictions)

class OpenBookQA:
    """
    Evaluates performance on the OpenBookQA benchmark.
    """
    def __init__(self):
        self.dataset = datasets.load_dataset("openbookqa")

    def evaluate(self, model, split="validation"):
        """
        Evaluates a model on OpenBookQA.
        
        :param model: A callable model that accepts a prompt and returns a response.
        :param split: Dataset split to use (e.g., "validation").
        :return: Accuracy score.
        """
        data = self.dataset[split]
        predictions = [model(f"{question} Options: {choices}") for question, choices in zip(data["question"], data["choices"])]
        accuracy = accuracy_score(data["answers"], predictions)
        return accuracy

class TriviaQA:
    """
    Evaluates performance on TriviaQA for factual recall.
    """
    def __init__(self):
        self.dataset = datasets.load_dataset("trivia_qa")

    def evaluate(self, model, split="validation"): 
        """
        Evaluates a model on TriviaQA.
        
        :param model: A callable model that accepts a prompt and returns a response.
        :param split: Dataset split to use (e.g., "validation").
        :return: Accuracy score.
        """
        data = self.dataset[split]
        predictions = [model(question) for question in data["question"]]
        accuracy = accuracy_score(data["answers"], predictions)
        return accuracy

# Example usage of these classes
def example_model(prompt):
    """A mock model function that generates random predictions."""
    return np.random.choice(["A", "B", "C", "D"])

# Instantiate and evaluate a benchmark
if __name__ == "__main__":
    mmlu = MMLUBenchmark()
    accuracy = mmlu.evaluate(example_model)
    print(f"MMLU Accuracy: {accuracy}")
