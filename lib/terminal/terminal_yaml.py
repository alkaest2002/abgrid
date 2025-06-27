"""
Filename: abgrid_yaml.py
Description: Provides functionality to load and validate YAML data using predefined schemas.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import yaml

from pathlib import Path
from typing import Optional, Dict, Any

class TerminalYAML:
    """
    """

    def __init__(self):
        pass

    def load_data(self, yaml_file_path: Path) -> Optional[Dict[str, Any]]:
        """
        """
        try:
            with open(yaml_file_path, 'r') as file:
                yaml_data = yaml.safe_load(file)
            return yaml_data
        
        except FileNotFoundError:
            return None, f"Cannot locate YAML file {yaml_file_path.name}."
        
        except yaml.YAMLError:
            return None, f"YAML file {yaml_file_path.name} could not be parsed."
