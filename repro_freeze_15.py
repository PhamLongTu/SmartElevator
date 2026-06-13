import time
from models.building import Building
from models.passenger import Passenger
from models.enums import PassengerType
from algorithms.astar import AStar
from statistics.statistics_manager import StatisticsManager

def repro():
    building = Building(num_floors=7)
    
    # 15 passengers - this is what the user has now
    passengers = [
        Passenger(id=i, origin_floor=i%7, dest_floor=(i+3)%7, spawn_time=i*0.5)
        for i in range(15)
    ]
    
    for p in passengers:
        building.add_passenger(p)
        
    state = building.to_state(current_time=15.0)
    
    print(f"Starting A* search with {len(passengers)} passengers...")
    algo = AStar()
    
    # We'll test with a 10k node limit like in benchmarking
    # but a shorter time limit to see if it triggers the stutter
    start = time.perf_counter()
    result = algo.solve(state, node_limit=10000, time_limit=5.0)
    end = time.perf_counter()
    
    print(f"Search finished in {end - start:.4f} seconds.")
    print(f"Success: {result.success}")
    print(f"Nodes expanded: {result.nodes_expanded}")
    print(f"Nodes generated: {result.nodes_generated}")

if __name__ == "__main__":
    repro()
