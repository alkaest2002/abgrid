"""
Filename: core_schemas.py

Description: Defines Pydantic models ensuring data integrity and validation.

Author: Pierpaolo Calanna

Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import re
from typing import Dict, List, Any, Set
from pydantic import BaseModel, model_validator

from lib.core import SYMBOLS

forbidden_chars = re.compile(r'[^A-Za-zÀ-ÖØ-öø-ÿĀ-ſƀ-ɏḀ-ỿЀ-ӿͰ-Ͽ\d\s\'\.,\-\?\!]')

class PydanticValidationException(Exception):
    """
    Custom exception that carries structured error information.
    
    This exception is raised when validation fails and contains detailed
    error information for each validation failure.
    
    Attributes:
        errors: List of error dictionaries containing location, value, and message
    """
    
    def __init__(self, errors: List[Dict[str, Any]]):
        """
        Initialize the exception with validation errors.
        
        Args:
            errors: List of dictionaries containing validation error details.
                   Each dictionary should have 'location', 'value_to_blame', 
                   and 'error_message' keys.
        """
        self.errors = errors
        error_messages = [f"{error['location']}: {error['error_message']}" for error in errors]
        super().__init__(f"{'\n'.join(error_messages)}")

def validate_text_field(field_name: str, value: Any, min_len: int, max_len: int) -> List[Dict[str, Any]]:
    """
    Validate a text field with length and character constraints.
    
    This function validates that a field is a string within specified length bounds
    and contains only allowed characters (letters, numbers, and safe punctuation).
    
    Args:
        field_name: Name of the field being validated (for error reporting)
        value: The value to validate
        min_len: Minimum allowed length for the string
        max_len: Maximum allowed length for the string
        
    Returns:
        List of error dictionaries. Empty list if validation passes.
        
    Examples:
        >>> validate_text_field("title", "Hello World", 1, 50)
        []
        >>> validate_text_field("title", "", 1, 50)
        [{'location': 'title', 'value_to_blame': '', 'error_message': 'Must be at least 1 characters long'}]
    """
    errors = []
    
    if value is None:
        errors.append({
            "location": field_name,
            "value_to_blame": None,
            "error_message": "Field is required"
        })
        return errors
    
    if not isinstance(value, str):
        errors.append({
            "location": field_name,
            "value_to_blame": value,
            "error_message": "Must be a string"
        })
        return errors
    
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

    # Check for forbidden characters
    if forbidden_chars_found := forbidden_chars.findall(value):
        unique_forbidden = list(dict.fromkeys(forbidden_chars_found))
        errors.append({
            "location": field_name,
            "value_to_blame": value,
            "error_message": f"Contains invalid characters: {''.join(unique_forbidden)}"
        })
    
    return errors

def validate_group_field(value: Any) -> List[Dict[str, Any]]:
    """
    Validate the group field.
    
    The group field must be an integer between 1 and 50 inclusive.
    
    Args:
        value: The value to validate
        
    Returns:
        List of error dictionaries. Empty list if validation passes.
    """
    errors = []
    
    if value is None:
        errors.append({
            "location": "group",
            "value_to_blame": None,
            "error_message": "Field is required"
        })
    elif not isinstance(value, int):
        errors.append({
            "location": "group",
            "value_to_blame": value,
            "error_message": "Must be an integer"
        })
    
    return errors

class ABGridGroupSchema(BaseModel):
    """
    Pydantic model for basic group information collection.
    
    This schema is used for initial data collection when creating an AB-Grid project.
    It validates the basic information needed before proceeding to the more complex
    choice configuration.
    
    Attributes:
        project_title: The project title (1-80 characters)
        question_a: First question text (1-300 characters)
        question_b: Second question text (1-300 characters)
        group: Group identifier (1-50)
        members: Number of members per group
    """
    
    project_title: str
    question_a: str
    question_b: str
    group: int
    members: int
    
    model_config = {"extra": "forbid"}

    @model_validator(mode="before")
    @classmethod
    def validate_all_fields(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all fields and collect errors.
        
        This method performs comprehensive validation of all fields in the schema.
        It collects all validation errors and raises a single exception with all
        errors if any validation fails.
        
        Args:
            data: Raw input data dictionary
            
        Returns:
            The validated data dictionary
            
        Raises:
            PydanticValidationException: If any validation errors are found
        """
        errors = []
        
        # Validate fields
        errors.extend(validate_text_field("project_title", data.get("project_title"), 1, 80))
        errors.extend(validate_text_field("question_a", data.get("question_a"), 1, 300))
        errors.extend(validate_text_field("question_b", data.get("question_b"), 1, 300))        
        errors.extend(validate_group_field(data.get("group")))
        cls._validate_members_field(data.get("members"), errors)

        if errors:
            raise PydanticValidationException(errors)
        
        return data
    
    @classmethod
    def _validate_members_field(cls, value: Any, errors: List[Dict[str, Any]]) -> None:
        """
        Validate the members field.
        
        The members field must be an integer between 6 and 50 inclusive.
        
        Args:
            value: The value to validate
            
        Returns:
            None.
        """
        if value is None:
            errors.append({
                "location": "members",
                "value_to_blame": None,
                "error_message": "Field is required"
            })
        elif not isinstance(value, int):
            errors.append({
                "location": "members",
                "value_to_blame": value,
                "error_message": "Must be an integer"
            })
        elif not (6 <= value <= 50):
            errors.append({
                "location": "members",
                "value_to_blame": value,
                "error_message": "Must be between 6 and 50"
            })
        

class ABGridReportSchema(BaseModel):
    """
    Pydantic model representing a complete ABGrid data project.
    
    This schema validates the complete AB-Grid project data including the choice
    structures that define the relationships between different options. It ensures
    that all choice keys are consistent between questions and that all value
    references are valid.
    
    Attributes:
        project_title: The project title (1-80 characters)
        question_a: First question text (1-300 characters)
        question_b: Second question text (1-300 characters)
        group: Group identifier (1-50)
        choices_a: List of choice dictionaries for question A
        choices_b: List of choice dictionaries for question B
        
    Notes:
        - Keys in choices_a and choices_b must be identical
        - All values must reference valid keys from either choices_a or choices_b
        - Keys and values must be single alphabetic characters
        - Choice keys must follow the SYMBOLS pattern (A, B, C, etc.)
    """
    
    project_title: str
    question_a: str
    question_b: str
    group: int
    choices_a: List[Dict[str, Any]]
    choices_b: List[Dict[str, Any]]
    
    model_config = {"extra": "forbid"}

    @model_validator(mode="before")
    @classmethod
    def validate_all_fields(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation of all fields.
        
        This method validates all fields in the schema, including the complex
        choice validation logic. It ensures that:
        1. Basic fields are valid
        2. Choice structures are correct
        3. Choice keys are consistent between questions
        4. All value references are valid
        
        Args:
            data: Raw input data dictionary
            
        Returns:
            The validated data dictionary
            
        Raises:
            PydanticValidationException: If any validation errors are found
        """
        errors = []
        
        # Validate basic fields
        errors.extend(validate_text_field("project_title", data.get("project_title"), 1, 80))
        errors.extend(validate_text_field("question_a", data.get("question_a"), 1, 300))
        errors.extend(validate_text_field("question_b", data.get("question_b"), 1, 300))
        errors.extend(validate_group_field(data.get("group")))
        
        # Validate choices
        choices_a_keys = cls._validate_choices(data, "choices_a", errors)
        choices_b_keys = cls._validate_choices(data, "choices_b", errors)
        
        # Check keys equality
        if choices_a_keys != choices_b_keys:
            errors.append({
                "location": "choices_a.keys vs choices_b.keys",
                "value_to_blame": {
                    "choices_a_keys": sorted(choices_a_keys),
                    "choices_b_keys": sorted(choices_b_keys)
                },
                "error_message": "Keys in choices_a and choices_b must be identical"
            })
        
        if errors:
            raise PydanticValidationException(errors)
        
        return data
    
    @classmethod
    def _validate_choices(cls, data: Dict[str, Any], field_name: str, errors: List[Dict[str, Any]]) -> Set[str]:
        """
        Validate choices structure and content.
        
        This method validates that:
        1. Choices is a non-empty list
        2. Each choice is a dictionary with exactly one key-value pair
        3. Keys are single alphabetic characters following the SYMBOLS pattern
        4. Values are either None or comma-separated lists of valid key references
        5. Keys don't reference themselves
        6. No duplicate values within a choice
        
        Args:
            data: The full data dictionary
            field_name: Name of the choices field ("choices_a" or "choices_b")
            errors: List to append errors to
            
        Returns:
            Set of extracted keys from the choices
        """
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
        
        if len(choices) > len(SYMBOLS):
            errors.append({
                "location": field_name,
                "value_to_blame": choices,
                "error_message": f"Number of choices ({len(choices)}) exceeds maximum allowed ({len(SYMBOLS)})"
            })
            return extracted_keys
        
        expected_keys = set(SYMBOLS[:len(choices)])
        
        # Validate each choice
        for i, choice_dict in enumerate(choices):
            choice_location = f"{field_name}[{i}]"
            
            if not isinstance(choice_dict, dict) or len(choice_dict) != 1:
                errors.append({
                    "location": choice_location,
                    "value_to_blame": choice_dict,
                    "error_message": "Each choice must be a dictionary with exactly one key-value pair"
                })
                continue
            
            key = next(iter(choice_dict.keys()))
            value_str = choice_dict[key]
            
            # Validate key
            if not isinstance(key, str) or len(key) != 1 or not key.isalpha():
                errors.append({
                    "location": f"{choice_location}.{key}",
                    "value_to_blame": key,
                    "error_message": "Key must be a single alphabetic character"
                })
            else:
                extracted_keys.add(key)
                
                # Validate value
                if value_str is not None and isinstance(value_str, str) and value_str.strip():
                    value_parts = [part.strip() for part in value_str.split(',')]
                    
                    # Check all parts are valid single alphabetic characters
                    invalid_parts = [part for part in value_parts if len(part) != 1 or not part.isalpha()]
                    if invalid_parts:
                        errors.append({
                            "location": f"{choice_location}.{key}",
                            "value_to_blame": value_str,
                            "error_message": "Value must contain only single alphabetic characters"
                        })
                    
                    # Check key doesn't reference itself
                    if key in value_parts:
                        errors.append({
                            "location": f"{choice_location}.{key}",
                            "value_to_blame": value_str,
                            "error_message": "Key cannot be present in its own values"
                        })
                    
                    # Check for duplicates
                    if len(value_parts) != len(set(value_parts)):
                        errors.append({
                            "location": f"{choice_location}.{key}",
                            "value_to_blame": value_str,
                            "error_message": "Values contain duplicates"
                        })
                    
                    # Check references are valid (will be validated against expected_keys)
                    invalid_values = [v for v in value_parts if v not in expected_keys]
                    if invalid_values:
                        errors.append({
                            "location": f"{choice_location}.{key}",
                            "value_to_blame": value_str,
                            "error_message": "Values contain invalid references"
                        })
        
        # Check keys match expected pattern
        if extracted_keys != expected_keys:
            errors.append({
                "location": f"{field_name}.keys",
                "value_to_blame": sorted(extracted_keys),
                "error_message": "Keys are not correct"
            })
        
        return extracted_keys
