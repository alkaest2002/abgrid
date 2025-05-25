"""
Filename: abgrid_yaml.py
Description: Provides functionality to load and validate YAML data using predefined schemas.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import yaml

from pathlib import Path
from typing import Literal, Tuple, Optional, Dict, Any
from pydantic import ValidationError
from lib.abgrid_schemas import ProjectSchema, GroupSchema

class ABGridYAML:

    def load_data(self, yaml_type: str, yaml_file_path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Load and validate YAML data from a file.

        Args:
            yaml_type (str): The type of YAML data being validated ('project' or 'group').
            yaml_file_path (str): The file path to the YAML file to be loaded.

        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[str]]: A tuple containing the loaded data and an error message (if any).
        """
        try:
            # Open and read the YAML file
            with open(yaml_file_path, 'r') as file:
                # Parse the YAML file using safe_load
                yaml_data = yaml.safe_load(file)
                # Ensure that all keys are strings
                yaml_data = self.convert_keys_to_strings(yaml_data)
                
            # Validate the parsed YAML data
            return self.validate(yaml_type, yaml_data)
        
        except FileNotFoundError:
            # Return error for file not found
            return None, f"Cannot locate YAML file {yaml_file_path.name}."
        
        except yaml.YAMLError:
            # Return error for YAML parsing issues
            return None, "YAML file {yaml_file_path.name} could not be parsed."
        
    def convert_keys_to_strings(self, yaml_data: dict | list) :
        """
        Recursively ensure that all keys in a given data structure are strings.

        Args:
            yaml_data: The data structure loaded from the YAML file (e.g., a dictionary or list).

        Returns:
            A new data structure with all keys converted to strings.
        """
        if isinstance(yaml_data, dict):
            return {str(key): self.convert_keys_to_strings(value) for key, value in yaml_data.items()}
        elif isinstance(yaml_data, list):
            return [self.convert_keys_to_strings(element) for element in yaml_data]
        else:
            return yaml_data
    
    def validate(self, yaml_type: Literal["project", "group"], yaml_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate the YAML data against the specified schema type.

        Args:
            yaml_type (str): The type of YAML data being validated ('project' or 'group').
            yaml_data (dict): The YAML data to be validated.

        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[str]]: A tuple containing the validated data and an error message (if any).
        """
        try:
            # Validate YAML data based on the specified type
            if yaml_type == "project":
                # Validate using ProjectSchema
                validated_data = ProjectSchema.model_validate(yaml_data).model_dump()
            elif yaml_type == "group":
                # Validate using GroupSchema
                validated_data = GroupSchema.model_validate(yaml_data).model_dump()
            else:
                # Return an error for an invalid YAML type
                return None, "Invalid YAML type specified."
            
            # Return validated data if no exceptions were raised
            return validated_data, None
        
        except ValidationError as e:
            # Return validation errors if any
            return None, e.errors()

