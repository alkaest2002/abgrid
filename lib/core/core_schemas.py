"""
Author: Pierpaolo Calanna

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
        super().__init__("\n".join(error_messages))

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
    """
    errors = []
    
    if value is None:
        errors.append({
            "location": field_name,
            "value_to_blame": None,
            "error_message": "field_is_required"
        })
        return errors
    
    if not isinstance(value, str):
        errors.append({
            "location": field_name,
            "value_to_blame": value,
            "error_message": "field_must_be_a_string"
        })
        return errors
    
    if len(value) < min_len:
        errors.append({
            "location": field_name,
            "value_to_blame": value,
            "error_message": f"field_is_too_short"
        })
    
    if len(value) > max_len:
        errors.append({
            "location": field_name,
            "value_to_blame": value,
            "error_message": f"field_is_too_long"
        })

    # Check for forbidden characters
    if forbidden_chars.findall(value):
        errors.append({
            "location": field_name,
            "value_to_blame": value,
            "error_message": f"field_contains_invalid_characters"
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
            "error_message": "field_is_required"
        })
    elif not isinstance(value, int):
        errors.append({
            "location": "group",
            "value_to_blame": value,
            "error_message": "field_must_be_an_integer"
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
        group: Group identifier (must be an integer)
        members: Number of members per group (intergr betwenn 8 and 50)
    """
    
    project_title: Any
    question_a: Any
    question_b: Any
    group: Any
    members: Any
    
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
        errors.extend(validate_text_field("project_title", data.get("project_title"), 1, 100))
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
                "error_message": "field_is_required"
            })
        elif not isinstance(value, int):
            errors.append({
                "location": "members",
                "value_to_blame": value,
                "error_message": "field_must_be_an_integer"
            })
        elif not (8 <= value <= 50):
            errors.append({
                "location": "members",
                "value_to_blame": value,
                "error_message": "field_is_out_of_range"
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
        - At least 3 nodes must have expressed a choice (have non-null, non-empty values)
    """
    
    project_title: Any
    question_a: Any
    question_b: Any
    group: Any
    choices_a: Any
    choices_b: Any
    
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
        4. All value references point to valid keys
        5. No more than 30% of nodes have expressed no choice
        
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
        
        # Validate choices structure and collect keys
        choices_a_keys = cls._validate_choices_structure(data, "choices_a", errors)
        choices_b_keys = cls._validate_choices_structure(data, "choices_b", errors)
        
        # Check keys equality
        if choices_a_keys != choices_b_keys:
            errors.append({
                "location": "choices_a vs choices_b",
                "value_to_blame": {
                    "choices_a_keys": sorted(choices_a_keys),
                    "choices_b_keys": sorted(choices_b_keys)
                },
                "error_message": "keys_in_a_and_b_must_be_identical"
            })
        
        # Validate that all value references point to valid keys
        # Only do this if we have valid key sets and they match
        if choices_a_keys == choices_b_keys and choices_a_keys:
            cls._validate_value_references(data, choices_a_keys, errors)
        
        # Check minimum nodes with choices
        cls._validate_minimum_nodes_with_choices(data, errors)
        
        if errors:
            raise PydanticValidationException(errors)
        return data
    
    @model_validator(mode="after")
    def strip_choice_values_after(self) -> "ABGridReportSchema":
        """
        Strip spaces from choice values after validation.
        
        This method removes spaces around commas in choice values after
        the model has been validated and the data structure is confirmed valid.
        
        Returns:
            The model instance with stripped choice values
        """
        for field_name in ["choices_a", "choices_b"]:
            choices = getattr(self, field_name)
            for choice_dict in choices:
                for key, value in choice_dict.items():
                    if isinstance(value, str) and value.strip():
                        stripped_value = ','.join(part.strip() for part in value.split(','))
                        choice_dict[key] = stripped_value
        
        return self
    
    @classmethod
    def _validate_choices_structure(cls, data: Dict[str, Any], field_name: str, errors: List[Dict[str, Any]]) -> Set[str]:
        """
        Validate choices structure and format.
        
        This method validates that:
        1. Choices is a non-empty list
        2. Each choice is a dictionary with exactly one key-value pair
        3. Keys are single alphabetic characters (no duplicates)
        4. Keys should not exceed SYMBOLS length
        5. Values have correct format (comma-separated single alphabetic characters)
        6. Keys don't reference themselves in values
        7. No duplicate values within a choice
        
        Args:
            data: The full data dictionary
            field_name: Name of the choices field ("choices_a" or "choices_b")
            errors: List to append errors to
            
        Returns:
            Set of extracted keys from the choices
        """
        choices = data.get(field_name)
        extracted_keys = set()
        
        # Type validation
        if not isinstance(choices, list):
            errors.append({
                "location": field_name,
                "value_to_blame": choices,
                "error_message": "field_must_be_a_list"
            })
            return extracted_keys
        
        # Empty list validation
        if len(choices) == 0:
            errors.append({
                "location": field_name,
                "value_to_blame": choices,
                "error_message": "field_cannot_be_empty"
            })
            return extracted_keys
        
        # Length validation
        if len(choices) > len(SYMBOLS):
            errors.append({
                "location": field_name,
                "value_to_blame": choices,
                "error_message": "choices_exceeds_availability_of_symbols"
            })
            return extracted_keys
        
        # Validate each choice
        for index, choice_dict in enumerate(choices):
            if not isinstance(choice_dict, dict) or len(choice_dict) != 1:
                errors.append({
                    "location": f"{field_name}, 0-based index: {index}",
                    "value_to_blame": choice_dict,
                    "error_message": "choice_must_be_a_single_key_value_pair"
                })
                continue
            
            key = next(iter(choice_dict.keys()))
            value_str = choice_dict[key]
            
            # Validate key
            if not isinstance(key, str) or len(key) != 1 or not key.isalpha():
                errors.append({
                    "location": f"{field_name}, {key}",
                    "value_to_blame": key,
                    "error_message": "key_must_be_a_single_alphabetic_character"
                })
            else:
                # Check for duplicate keys
                if key in extracted_keys:
                    errors.append({
                        "location": f"{field_name}, {key}",
                        "value_to_blame": key,
                        "error_message": "duplicate_key_found"
                    })
                else:
                    extracted_keys.add(key)
                    
                    # Validate value format
                    cls._validate_value_format(field_name, index, key, value_str, errors)
        
        return extracted_keys
    
    @classmethod
    def _validate_value_format(cls, field_name: str, index: int, key: str, value_str: Any, errors: List[Dict[str, Any]]) -> None:
        """
        Validate the format of a choice value.
        
        This method validates that values are either None, empty strings, or
        comma-separated lists of single alphabetic characters. It also ensures
        that keys don't reference themselves and there are no duplicates.
        
        Args:
            field_name: Name of the choices field
            index: the choice zero-based index
            key: The choice key
            value_str: The value to validate
            errors: List to append errors to
        """
        if value_str is None:
            return
            
        if not isinstance(value_str, str):
            errors.append({
                "location": f"{field_name}, {key}",
                "value_to_blame": value_str,
                "error_message": "value_must_be_string_or_null"
            })
            return
        
        if not value_str.strip():
            return  # Empty string is valid
        
        value_parts = [part.strip() for part in value_str.split(',')]
        
        # Check all parts are valid single alphabetic characters
        invalid_parts = [part for part in value_parts if len(part) != 1 or not part.isalpha()]
        if invalid_parts:
            errors.append({
                "location": f"{field_name}, {key}",
                "value_to_blame": value_str,
                "error_message": "value_must_contain_only_single_alphabetic_characters"
            })
        
        # Check key doesn't reference itself
        if key in value_parts:
            errors.append({
                "location": f"{field_name}, {key}",
                "value_to_blame": value_str,
                "error_message": "key_cannot_be_present_in_its_own_values"
            })
        
        # Check for duplicates
        if len(value_parts) != len(set(value_parts)):
            errors.append({
                "location": f"{field_name}, {key}",
                "value_to_blame": value_str,
                "error_message": "values_contain_duplicates"
            })
    
    @classmethod
    def _validate_value_references(cls, data: Dict[str, Any], all_valid_keys: Set[str], errors: List[Dict[str, Any]]) -> None:
        """
        Validate that all value references point to valid keys.
        
        This method ensures that every value in the choices references only
        keys that actually exist in the combined key set from both choices_a
        and choices_b.
        
        Args:
            data: The full data dictionary
            all_valid_keys: Set of all valid keys from both choices
            errors: List to append errors to
        """
        for field_name in ["choices_a", "choices_b"]:
            choices = data.get(field_name)
            if not isinstance(choices, list):
                continue
                
            for index, choice_dict in enumerate(choices):
                if not isinstance(choice_dict, dict) or len(choice_dict) != 1:
                    continue
                    
                key = next(iter(choice_dict.keys()))
                value_str = choice_dict[key]
                
                if value_str is None or not isinstance(value_str, str) or not value_str.strip():
                    continue
                    
                value_parts = [part.strip() for part in value_str.split(',')]
                invalid_references = [part for part in value_parts if part and part not in all_valid_keys]
                
                if invalid_references:
                    errors.append({
                        "location": f"{field_name}, {key}",
                        "value_to_blame": value_str,
                        "error_message": "values_reference_invalid_keys"
                    })
    
    @classmethod
    def _validate_minimum_nodes_with_choices(cls, data: Dict[str, Any], errors: List[Dict[str, Any]]) -> None:
        """
        Validate choice completion requirements for each choice set separately.
        
        This method validates that for both choices_a and choices_b:
        1. At least 3 nodes have expressed a choice
        2. No more than 60% of nodes have empty values (i.e., no choices)
        
        A node is considered to have expressed a choice if it has a non-null,
        non-empty value in the respective choice set.
        
        Args:
            data: The full data dictionary
            errors: List to append errors to
        """
        choices_a = data.get("choices_a")
        choices_b = data.get("choices_b")
        
        # Skip validation if choices are not valid lists
        if not isinstance(choices_a, list) or not isinstance(choices_b, list):
            return
        
        # Validate choices_a separately
        cls._validate_single_choice_set(choices_a, "choices_a", errors)
        
        # Validate choices_b separately
        cls._validate_single_choice_set(choices_b, "choices_b", errors)

    @classmethod
    def _validate_single_choice_set(cls, choices: List[Dict[str, Any]], field_name: str, errors: List[Dict[str, Any]]) -> None:
        """
        Validate a single choice set for completion requirements.
        
        Args:
            choices: List of choice dictionaries
            field_name: Name of the choice field for error reporting
            errors: List to append errors to
        """
        if len(choices) == 0:
            return  # No choices to validate
        
        # Count nodes with and without choices
        nodes_with_choices = set()
        total_nodes = 0
        
        for choice_dict in choices:
            if isinstance(choice_dict, dict) and len(choice_dict) == 1:
                key = next(iter(choice_dict.keys()))
                value = choice_dict[key]
                total_nodes += 1
                
                # Check if this node has expressed a choice
                if value is not None and isinstance(value, str) and value.strip():
                    nodes_with_choices.add(key)
        
        if total_nodes == 0:
            return  # No valid nodes to validate
        
        nodes_with_choices_count = len(nodes_with_choices)
        nodes_without_choices_count = total_nodes - nodes_with_choices_count
                
        # Validate that no more than 30% of nodes have empty values
        empty_percentage = (nodes_without_choices_count / total_nodes) * 100
        if empty_percentage > 60:
            errors.append({
                "location": field_name,
                "value_to_blame": {
                    "nodes_without_choices_count": nodes_without_choices_count,
                    "total_nodes": total_nodes,
                    "empty_percentage": round(empty_percentage, 1),
                    "max_allowed_percentage": 60.0
                },
                "error_message": "too_many_nodes_have_empty_values"
            })

