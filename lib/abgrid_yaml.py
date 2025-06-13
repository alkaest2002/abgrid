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
    """
    Class providing methods to load and validate YAML data using predefined schemas for AB-Grid projects.
    """

    def load_data(self, yaml_type: Literal["project", "group"], yaml_file_path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Load and validate YAML data from a file.

        Args:
            yaml_type (Literal["project", "group"]): The type of YAML data being validated.
            yaml_file_path (Path): The file path to the YAML file to be loaded.

        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[str]]: A tuple containing the loaded data and an error message if any:
                - Loaded YAML data dictionary if successful, or None if an error occurs.
                - Error message as a string if an error occurs, or None if successful.
        """
        try:
            with open(yaml_file_path, 'r') as file:
                yaml_data = yaml.safe_load(file)
            return self.validate(yaml_type, yaml_data)
        
        except FileNotFoundError:
            return None, f"Cannot locate YAML file {yaml_file_path.name}."
        
        except yaml.YAMLError:
            return None, f"YAML file {yaml_file_path.name} could not be parsed."
    
    def validate(self, yaml_type: Literal["project", "group"], yaml_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate the YAML data against the specified schema type.

        Args:
            yaml_type (Literal["project", "group"]): The type of YAML data being validated.
            yaml_data (Dict[str, Any]): The YAML data to be validated.

        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[str]]: A tuple containing the validated data and an error message if any:
                - Validated YAML data dictionary if successful, or None if validation fails.
                - Error message as a string if validation fails, or None if successful.
        """
        try:
            if yaml_type == "project":
                validated_data = ProjectSchema.model_validate(yaml_data).model_dump()
            elif yaml_type == "group":
                validated_data = GroupSchema.model_validate(yaml_data).model_dump()
            else:
                return None, "Invalid YAML type specified."
            return validated_data, None
        
        except ValidationError as e:
            return None, e.errors()
