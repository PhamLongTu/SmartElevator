
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from controllers.scenario_table import ScenarioTable
from controllers.scenario_validator import ScenarioValidator
from models.enums import PassengerType

table = ScenarioTable()
# Modify a row
table.rows[0].spawn_floor = 2
table.rows[0].destination = 5
table.rows[0].spawn_time = 10
table.rows[0].passenger_type = PassengerType.URGENT

# Export
data = table.export_data()
print(f"Exported data length: {len(data)}")
print(f"Row 0 data: {data[0]}")

# Import into a new table
new_table = ScenarioTable()
new_table.import_data(data)

# Verify
r = new_table.rows[0]
success = (r.spawn_floor == 2 and r.destination == 5 and 
           r.spawn_time == 10 and r.passenger_type == PassengerType.URGENT)
print(f"Persistence Verification: {'SUCCESS' if success else 'FAILED'}")

# Test invalid state
table.rows[1].spawn_floor = 3
table.rows[1].destination = 3
valid = ScenarioValidator.validate_all(table.rows)
print(f"Validation detection: {'SUCCESS' if not valid else 'FAILED'}")
if not valid:
    print(f"Row 1 error: {table.rows[1].error_message}")
