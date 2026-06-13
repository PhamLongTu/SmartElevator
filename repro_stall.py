
import sys
import os
sys.path.append(os.getcwd())

from models.building import Building
from models.passenger import Passenger
from models.enums import PassengerType
from algorithms.astar import AStar
from simulation import SimulationEngine, RandomScenarioGenerator

def test_astar_stall():
    engine = SimulationEngine(
        generator=RandomScenarioGenerator(num_passengers=15, seed=7)
    )
    engine.new_scenario()
    
    # Simulate some steps if needed, but the user's screenshot is at T=17.0
    # Let's just try to plan from the initial state
    initial_state = engine.snapshot()
    print(f"Initial state targets: {initial_state.targets()}")
    print(f"Elevator floor: {initial_state.elevator_floor}")
    print(f"Onboard: {len(initial_state.onboard)}")
    print(f"Waiting: {initial_state.num_waiting}")
    
    algo = AStar()
    result = algo.solve(initial_state, node_limit=2000, time_limit=0.15)
    
    print(f"Nodes expanded: {result.nodes_expanded}")
    print(f"Nodes generated: {result.nodes_generated}")
    print(f"Success: {result.success}")
    print(f"Path length: {len(result.path)}")
    print(f"Path: {result.path}")

if __name__ == "__main__":
    test_astar_stall()
