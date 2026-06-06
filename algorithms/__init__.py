"""AI search algorithms package.

Contains the planning artifacts (:class:`SearchNode`) and the concrete
search algorithm implementations. This layer is pure: it never imports
Pygame nor touches the mutable runtime world.
"""

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.bfs import BFS
from algorithms.search_node import SearchNode

__all__ = ["SearchNode", "SearchAlgorithm", "SearchResult", "BFS"]
