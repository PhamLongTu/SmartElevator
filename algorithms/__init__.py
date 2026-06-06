"""AI search algorithms package.

Contains the planning artifacts (:class:`SearchNode`) and the concrete
search algorithm implementations. This layer is pure: it never imports
Pygame nor touches the mutable runtime world.
"""

from algorithms.algorithm_factory import AlgorithmFactory, AlgorithmInfo
from algorithms.astar import AStar
from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.beam_search import BeamSearch
from algorithms.bfs import BFS
from algorithms.dfs import DFS
from algorithms.greedy import GreedyBestFirst
from algorithms.hill_climbing import HillClimbing
from algorithms.search_node import SearchNode
from algorithms.ucs import UCS

__all__ = [
    "SearchNode",
    "SearchAlgorithm",
    "SearchResult",
    "BFS",
    "DFS",
    "UCS",
    "GreedyBestFirst",
    "AStar",
    "HillClimbing",
    "BeamSearch",
    "AlgorithmFactory",
    "AlgorithmInfo",
]
