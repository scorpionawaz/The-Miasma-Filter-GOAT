
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ResearchConfiguration:
    """Configuration for research-related models and parameters.

    Attributes:
        critic_model (str): Model for evaluation tasks.
        worker_model (str): Model for working/generation tasks.
        max_search_iterations (int): Maximum search iterations allowed.
    """

    critic_model: str = "gemini-1.5-pro"
    worker_model: str = "gemini-1.5-pro"
    max_search_iterations: int = 5


config = ResearchConfiguration()
