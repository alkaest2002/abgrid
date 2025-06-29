"""
Filename: core_schemas.py
Description: Defines Pydantic models ensuring data integrity and validation.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from typing import Dict, List, Any, Set
from pydantic import BaseModel, model_validator

from lib.core import SYMBOLS

class ValidationException(Exception):
    """Custom exception that carries structured error information."""
    
    def __init__(self, errors: List[Dict[str, Any]]):
        self.errors = errors
        error_messages = [
            f"{error['location']}: {error['error_message']}"
            for error in errors
        ]
        super().__init__(f"{'\n'.join(error_messages)}")


class ABGridSchema(BaseModel):
    """
    Pydantic model representing an ABGrid data project.
    
    Attributes:
        project_title: The project title (1-80 characters)
        prompt: Project prompt (1-500 characters)
        question_a: First question text (1-300 characters)
        question_a_choices: Answer choices for question A (1-150 characters)
        question_b: Second question text (1-300 characters)
        question_b_choices: Answer choices for question B (1-150 characters)
        group: Group identifier (1-50)
        choices_a: List of choice dictionaries for question A
        choices_b: List of choice dictionaries for question B
    
    Notes:
        - Keys in choices_a and choices_b must be identical
        - All values must reference valid keys from either choices_a or choices_b
        - Keys and values must be single alphabetic characters
    """
    
    # Fields - using Any to bypass Pydantic's built-in validation
    project_title: Any
    group: Any
    prompt: Any
    question_a: Any
    question_a_choices: Any
    question_b: Any
    question_b_choices: Any
    choices_a: Any
    choices_b: Any
    
    model_config = {"extra": "forbid"}

    @model_validator(mode="before")
    @classmethod
    def validate_all_fields(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation following the specified order and collecting all errors.
        
        Args:
            data: Raw input data dictionary
            
        Returns:
            Dict[str, Any]: Validated data dictionary
            
        Raises:
            ValueError: Contains all validation errors found across all fields and constraints
        """
        errors: List[Dict[str, Any]] = []
        
        # STEP 1: Check basic fields
        errors.extend(cls._validate_basic_fields(data))
        
        # STEP 2: Check that choices_a keys are correct
        choices_a_keys = cls._validate_choices_keys(data, "choices_a", errors)
        
        # STEP 3: Check that choices_a values are correct
        cls._validate_choices_values(data, "choices_a", choices_a_keys, errors)
        
        # STEP 4: Check that choices_b keys are correct
        choices_b_keys = cls._validate_choices_keys(data, "choices_b", errors)
        
        # STEP 5: Check that choices_b values are correct
        cls._validate_choices_values(data, "choices_b", choices_b_keys, errors)
        
        # STEP 6: Check that choices_a keys and choices_b keys are equal
        cls._validate_keys_equality(choices_a_keys, choices_b_keys, errors)
        
        # Raise all errors at once
        cls._raise_errors_if_any(errors)
        
        return data
    
    @classmethod
    def _validate_basic_fields(cls, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """STEP 1: Validate basic fields (project_title, group, prompt, questions)."""
        errors: List[Dict[str, Any]] = []
        
        # String fields validation
        string_fields = {
            "project_title": (1, 80),
            "prompt": (1, 500),
            "question_a": (1, 300),
            "question_a_choices": (1, 150),
            "question_b": (1, 300),
            "question_b_choices": (1, 150),
        }
        
        for field_name, (min_len, max_len) in string_fields.items():
            value = data.get(field_name)
            
            if value is None:
                errors.append({
                    "location": field_name,
                    "value_to_blame": None,
                    "error_message": "Field is required"
                })
                continue
            
            if not isinstance(value, str):
                errors.append({
                    "location": field_name,
                    "value_to_blame": value,
                    "error_message": "Must be a string"
                })
                continue
            
            if len(value) < min_len:
                errors.append({
                    "location": field_name,
                    "value_to_blame": value,
                    "error_message": f"Must be at least {min_len} characters long"
                })
            
            if len(value) > max_len:
                errors.append({
                    "location": field_name,
                    "value_to_blame": value,
                    "error_message": f"Must be at most {max_len} characters long"
                })
        
        # Group field validation
        group_value = data.get("group")
        
        if group_value is None:
            errors.append({
                "location": "group",
                "value_to_blame": None,
                "error_message": "Field is required"
            })
        elif not isinstance(group_value, int):
            errors.append({
                "location": "group",
                "value_to_blame": group_value,
                "error_message": "Must be an integer"
            })
        else:
            if group_value < 1:
                errors.append({
                    "location": "group",
                    "value_to_blame": group_value,
                    "error_message": "Must be greater than or equal to 1"
                })
            if group_value > 50:
                errors.append({
                    "location": "group",
                    "value_to_blame": group_value,
                    "error_message": "Must be less than or equal to 50"
                })
        
        return errors
   
    @classmethod
    def _validate_choices_keys(cls, data: Dict[str, Any], field_name: str, errors: List[Dict[str, Any]]) -> Set[str]:
        """STEP 2/4: Validate that choices keys are correct (equal to SYMBOLS[:len(choices)])."""
        choices = data.get(field_name)
        extracted_keys = set()
        
        if not isinstance(choices, list):
            return extracted_keys
        
        if len(choices) == 0:
            errors.append({
                "location": field_name,
                "value_to_blame": choices,
                "error_message": "List cannot be empty"
            })
            return extracted_keys
        
        # Check if length exceeds SYMBOLS limit
        if len(choices) > len(SYMBOLS):
            errors.append({
                "location": field_name,
                "value_to_blame": choices,
                "error_message": f"Number of choices ({len(choices)}) exceeds maximum allowed ({len(SYMBOLS)})"
            })
            return extracted_keys
        
        # Calculate expected keys based on length
        expected_keys = set(SYMBOLS[:len(choices)])
        
        # Extract keys from choices
        for i, choice_dict in enumerate(choices):
            choice_location = f"{field_name}[{i}]"
            
            if not isinstance(choice_dict, dict):
                errors.append({
                    "location": choice_location,
                    "value_to_blame": choice_dict,
                    "error_message": "Each choice must be a dictionary"
                })
                continue
            
            if len(choice_dict) != 1:
                errors.append({
                    "location": choice_location,
                    "value_to_blame": choice_dict,
                    "error_message": "Each choice must have exactly one key-value pair"
                })
                continue
            
            key = next(iter(choice_dict.keys()))
            
            if not isinstance(key, str) or len(key) != 1 or not key.isalpha():
                errors.append({
                    "location": f"{choice_location}.{key}",
                    "value_to_blame": key,
                    "error_message": "Key must be a single alphabetic character"
                })
            else:
                extracted_keys.add(key)
        
        # Compare extracted keys with expected keys
        if extracted_keys != expected_keys:
            errors.append({
                "location": f"{field_name}.keys",
                "value_to_blame": sorted(extracted_keys),
                "error_message": f"Keys are not correct"
            })
        
        return extracted_keys
    
    @classmethod
    def _validate_choices_values(cls, data: Dict[str, Any], field_name: str, valid_keys: Set[str], errors: List[Dict[str, Any]]) -> None:
        """STEP 3/5: Validate that choices values are correct using the established criteria."""
        choices = data.get(field_name)
        
        if not isinstance(choices, list):
            return
        
        for i, choice_dict in enumerate(choices):
            choice_location = f"{field_name}[{i}]"
            
            if not isinstance(choice_dict, dict) or len(choice_dict) != 1:
                continue  # Skip invalid choices (already reported in key validation)
            
            key = next(iter(choice_dict.keys()))
            value_str = choice_dict[key]
            
            # Skip if key is invalid (already reported)
            if not isinstance(key, str) or len(key) != 1 or not key.isalpha():
                continue
            
            # Validate value (can be None, or string with comma-separated values)
            if value_str is not None:
                if not isinstance(value_str, str):
                    errors.append({
                        "location": f"{choice_location}.{key}",
                        "value_to_blame": value_str,
                        "error_message": "Value must be a string or None"
                    })
                    continue
                
                # Parse and validate value parts
                if value_str.strip():  # Only validate non-empty strings
                    value_parts = [part.strip() for part in value_str.split(',')]
                    
                    if not value_parts:  # Empty after cleaning
                        errors.append({
                            "location": f"{choice_location}.{key}",
                            "value_to_blame": value_str,
                            "error_message": "Value contains only empty entries or whitespace"
                        })
                        continue
                    
                    # Check each part is a single alphabetic character
                    invalid_parts = [part for part in value_parts if len(part) != 1 or not part.isalpha()]
                    if invalid_parts:
                        errors.append({
                            "location": f"{choice_location}.{key}",
                            "value_to_blame": value_str,
                            "error_message": f"Value must contain only single alphabetic characters"
                        })
                    
                    # Check key doesn't appear in its own values
                    if key in value_parts:
                        errors.append({
                            "location": f"{choice_location}.{key}",
                            "value_to_blame": value_str,
                            "error_message": "Key cannot be present in its own values"
                        })
                    
                    # Check for duplicates
                    if len(value_parts) != len(set(value_parts)):
                        duplicates = [part for part in set(value_parts) if value_parts.count(part) > 1]
                        errors.append({
                            "location": f"{choice_location}.{key}",
                            "value_to_blame": value_str,
                            "error_message": f"Values contain duplicates"
                        })
                    
                    # Check that all values reference valid keys
                    invalid_values = [v for v in value_parts if v not in valid_keys]
                    if invalid_values:
                        errors.append({
                            "location": f"{choice_location}.{key}",
                            "value_to_blame": value_str,
                            "error_message": "Values contain invalid references"
                        })
    
    @classmethod
    def _validate_keys_equality(cls, choices_a_keys: Set[str], choices_b_keys: Set[str], errors: List[Dict[str, Any]]) -> None:
        """STEP 6: Check that choices_a keys and choices_b keys are equal."""
        if choices_a_keys != choices_b_keys:
            errors.append({
                "location": "choices_a.keys vs choices_b.keys",
                "value_to_blame": {
                    "choices_a_keys": sorted(choices_a_keys),
                    "choices_b_keys": sorted(choices_b_keys)
                },
                "error_message": "Keys in choices_a and choices_b must be identical"
            })
    
    @classmethod
    def _raise_errors_if_any(cls, errors: List[Dict[str, Any]]) -> None:
        """Raise custom exception with structured errors."""
        if errors:
            raise ValidationException(errors)
