"""The :class:`SearchNode` used by the search algorithms.

A search node wraps an immutable :class:`~models.state.State` with the
bookkeeping a search needs: the parent link, the action that produced this
node, and the costs ``g`` (path cost so far), ``h`` (heuristic estimate), and
``f = g + h``.

This is deliberately separate from ``State``: ``State`` hashes on world
content only (so equal worlds collapse in the visited-set), whereas two nodes
holding the *same* state may differ in ``g``/``h``/``parent``. Keeping the
bookkeeping outside the hashed object preserves correct duplicate detection.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models.enums import ElevatorAction
from models.state import State


@dataclass(slots=True)
class SearchNode:
    """A node in the search tree.

    Attributes:
        state: The immutable world state this node represents.
        parent: The node expanded to reach this one, or ``None`` for the root.
        action: The action taken from ``parent`` to reach this node.
        g: Accumulated path cost from the root to this node.
        h: Heuristic estimate of remaining cost to a goal.
    """

    state: State
    parent: "SearchNode | None" = None
    action: ElevatorAction | None = None
    g: float = 0.0
    h: float = 0.0

    @property
    def f(self) -> float:
        """Evaluation cost ``f = g + h`` (used by A*)."""
        return self.g + self.h

    def reconstruct_path(self) -> list[ElevatorAction]:
        """Return the ordered list of actions from the root to this node."""
        actions: list[ElevatorAction] = []
        node: "SearchNode | None" = self
        while node is not None and node.action is not None:
            actions.append(node.action)
            node = node.parent
        actions.reverse()
        return actions

    def depth(self) -> int:
        """Number of actions from the root to this node."""
        count = 0
        node: "SearchNode | None" = self.parent
        while node is not None:
            count += 1
            node = node.parent
        return count

    def __lt__(self, other: "SearchNode") -> bool:
        """Order by ``f`` then ``h`` so heap ties prefer more-informed nodes."""
        if self.f != other.f:
            return self.f < other.f
        return self.h < other.h
