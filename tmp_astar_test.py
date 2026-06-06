"""Smoke test for A*: optimality (== UCS cost), efficiency, open/closed behavior."""
import sys

from algorithms import AStar, UCS, GreedyBestFirst
from simulation import RandomScenarioGenerator, SimulationEngine
from statistics import StatisticsManager


def check(label, cond):
    print(f"{'PASS' if cond else 'FAIL'}: {label}")
    if not cond:
        sys.exit(1)


# Test across several seeds to confirm A* optimality robustly.
optimal_matches = 0
for seed in (7, 21, 33, 44, 99):
    eng = SimulationEngine(generator=RandomScenarioGenerator(num_passengers=4, seed=seed))
    eng.new_scenario()
    initial = eng.snapshot()

    a = AStar().solve(initial)
    u = UCS().solve(initial)

    check(f"[seed {seed}] A* found solution", a.success)
    check(f"[seed {seed}] A* cost == UCS optimal cost", a.cost == u.cost)
    check(f"[seed {seed}] A* expands <= UCS", a.nodes_expanded <= u.nodes_expanded)

    # Execute A* plan -> must solve the scenario.
    for action in a.path:
        eng.apply(action)
    check(f"[seed {seed}] A* plan solves scenario", eng.is_finished())
    optimal_matches += 1

# Detailed comparison on seed 7.
eng = SimulationEngine(generator=RandomScenarioGenerator(num_passengers=4, seed=7))
eng.new_scenario()
initial = eng.snapshot()
stats = StatisticsManager()
a = AStar().solve(initial, stats=stats)
u = UCS().solve(initial)
g = GreedyBestFirst().solve(initial)

check("A* name set", a.algorithm == "A*")
check("A* stats mirrored", stats.solution_cost == a.cost)
check("A* heuristic name is span", AStar().heuristic_name == "span")

print(f"  A*:     cost={a.cost}, len={a.plan_length}, expanded={a.nodes_expanded}")
print(f"  UCS:    cost={u.cost}, len={u.plan_length}, expanded={u.nodes_expanded}")
print(f"  Greedy: cost={g.cost}, len={g.plan_length}, expanded={g.nodes_expanded}")
print(f"  -> A* matched optimal cost on {optimal_matches}/5 seeds, "
      f"expanding {u.nodes_expanded - a.nodes_expanded} fewer nodes than UCS on seed 7")

print("\nAll A* smoke tests passed.")
