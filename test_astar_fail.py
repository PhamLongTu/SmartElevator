from models.building import Building
from models.passenger import Passenger
from algorithms.astar import AStar

def test_failure():
    building = Building(num_floors=7)
    # Add many passengers to make it hard
    for i in range(20):
        building.add_passenger(Passenger(id=i, origin_floor=i%7, dest_floor=(i+4)%7, spawn_time=0.0))
        
    state = building.to_state(current_time=0.0)
    algo = AStar()
    
    # Very small node limit to force failure
    result = algo.solve(state, node_limit=10, time_limit=1.0)
    print(f"Success: {result.success}")
    print(f"Path: {result.path}")
    print(f"Best node was root: {len(result.path) == 0}")

if __name__ == "__main__":
    test_failure()
