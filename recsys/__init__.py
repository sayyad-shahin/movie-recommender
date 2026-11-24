"""Movie recommender: content-based + item-based collaborative filtering, blended into a hybrid."""
from .engine import MovieRecommender, Movie, load_data, DEFAULT_DATA_DIR

__all__ = ["MovieRecommender", "Movie", "load_data", "DEFAULT_DATA_DIR"]
