
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from controllers.scenario_table import ScenarioTable
from controllers.scenario_validator import ScenarioValidator

table = ScenarioTable()
valid = ScenarioValidator.validate_all(table.rows)
print(f"Default table valid: {valid}")
for i, row in enumerate(table.rows):
    if not row.is_valid:
        print(f"Row {i} invalid: {row.error_message}")
