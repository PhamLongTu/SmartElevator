
import sys
import os
sys.path.append(os.getcwd())

from simulation import SimulationEngine, RandomScenarioGenerator
from controllers.ai_mode import AIMode
from models.enums import ElevatorAction

def test_idle_advances_time():
    # Use seed 7 which we know has a gap at T=17.0
    engine = SimulationEngine(
        generator=RandomScenarioGenerator(num_passengers=15, seed=7)
    )
    engine.new_scenario()
    
    # Fast forward to T=17.0 (where all spawned passengers are delivered)
    # Total spawned by T=17 are 4 people.
    # We'll just fake it by advancing engine time and clearing building.
    engine.time = 17.0
    engine.building.elevator.onboard = []
    for f in range(engine.num_floors):
        engine.building.waiting[f] = []
    
    # Verify it's not finished (more passengers pending)
    print(f"Simulation finished? {engine.is_finished()}")
    print(f"Pending count: {len(engine._pending)}")
    
    controller = AIMode(engine)
    
    print(f"Engine time before: {engine.time}")
    action = controller.next_action()
    print(f"AI Action when idle: {action}")
    
    if action == ElevatorAction.IDLE:
        engine.apply(action)
        print(f"Engine time after IDLE: {engine.time}")
    else:
        print("FAIL: AI did not return IDLE")

if __name__ == "__main__":
    test_idle_advances_time()
