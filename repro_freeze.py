import time
from models.building import Building
from models.passenger import Passenger
from models.enums import PassengerType
from algorithms.astar import AStar
from statistics.statistics_manager import StatisticsManager

def repro():
    # Setup a building with 7 floors and 1 elevator (cap 4)
    building = Building(num_floors=7)
    elevator = building.elevator
    
    # Add 12 passengers scattered around (reproducing the high load)
    # 12 is enough to likely exceed search limits
    passengers = [
        Passenger(id=1, origin_floor=0, dest_floor=4, spawn_time=0.0),
        Passenger(id=2, origin_floor=1, dest_floor=6, spawn_time=1.0),
        Passenger(id=3, origin_floor=2, dest_floor=0, spawn_time=2.0),
        Passenger(id=4, origin_floor=3, dest_floor=5, spawn_time=3.0),
        Passenger(id=5, origin_floor=4, dest_floor=1, spawn_time=4.0),
        Passenger(id=6, origin_floor=5, dest_floor=0, spawn_time=5.0),
        Passenger(id=7, origin_floor=6, dest_floor=2, spawn_time=6.0),
        Passenger(id=8, origin_floor=0, dest_floor=6, spawn_time=7.0),
        Passenger(id=9, origin_floor=2, dest_floor=5, spawn_time=8.0),
        Passenger(id=10, origin_floor=4, dest_floor=3, spawn_time=9.0),
        Passenger(id=11, origin_floor=6, dest_floor=1, spawn_time=10.0, passenger_type=PassengerType.URGENT),
        Passenger(id=12, origin_floor=1, dest_floor=5, spawn_time=11.0),
    ]
    
    for p in passengers:
        building.add_passenger(p)
        
    state = building.to_state(current_time=11.0)
    
    print(f"Starting A* search with {len(passengers)} passengers waiting...")
    algo = AStar()
    start = time.perf_counter()
    # Default node_limit=10000, time_limit=1.5
    result = algo.solve(state, node_limit=10000, time_limit=2.0)
    end = time.perf_counter()
    
    print(f"Search finished in {end - start:.4f} seconds.")
    print(f"Success: {result.success}")
    print(f"Nodes expanded: {result.nodes_expanded}")
    print(f"Nodes generated: {result.nodes_generated}")
    print(f"Plan length: {len(result.path)}")

if __name__ == "__main__":
    repro()
