"""
Filename: abgrid_schema.py
Description: Defines Pydantic models for project and group schemas, ensuring data integrity and validation.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from curses.ascii import isupper
from pydantic import BaseModel, Field, constr, field_validator, model_validator
from typing import Dict, List, Set

# Define a Pydantic model for the project schema
class ProjectSchema(BaseModel):
    """
    A Pydantic model that represents a project's data schema.
    """
    project_title: constr(min_length=1, max_length=80) # type: ignore
    groups: int = Field(ge=1, le=20)
    members_per_group: int = Field(ge=4, le=36)
    explanation: constr(min_length=1, max_length=500) # type: ignore
    question_a: constr(min_length=1, max_length=300) # type: ignore
    question_a_choices: constr(min_length=1, max_length=150) # type: ignore
    question_b: constr(min_length=1, max_length=300) # type: ignore
    question_b_choices: constr(min_length=1, max_length=150) # type: ignore
    model_config = {"extra": "forbid"}

# Define a Pydantic model for the group schema
class GroupSchema(BaseModel):
    """
    A Pydantic model that represents the schema for a group within a project.
    """
    group: int = Field(ge=1, le=20)
    choices_a: List[Dict[str, str | None]]
    choices_b: List[Dict[str, str | None]]
    model_config = {"extra": "forbid"}

    @field_validator("choices_a", "choices_b")
    def validate_choices(cls, value: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Validator for choices_a and choices_b fields to ensure each choice is well-formed.

        Args:
            value: A list of dictionaries representing choices.

        Returns:
            The validated list of choices.

        Raises:
            ValueError: If any validation check fails.
        """
        for choice_dict in value:
            
            # Get key and its corresponding value string
            key = next(iter(choice_dict.keys()))
            value_str = choice_dict[key]
            value_parts = value_str.split(',') if value_str else []

            # Validate each choice
            if not isinstance(choice_dict, dict):
                raise ValueError("Each choice must be a dictionary")
            if len(choice_dict) != 1:
                raise ValueError("Each choice must have exactly one key-value pair")
            if not ((key.isnumeric() and len(key) == 1) or (key.isalpha() and key.isupper() and len(key) == 1)):
                raise ValueError(f"Key '{key}' must be a single uppercase letter or number")
            if any(not part for part in value_parts):
                raise ValueError(f"Value '{value_str}' contains empty entries due to misplaced commas")
            if not all(len(part) < 2 and part.isalnum() for part in value_parts):
                raise ValueError(f"Value '{value_str}' must be comma-separated single uppercase letters or numbers")
            if key in value_parts:
                raise ValueError(f"Key '{key}' cannot be present in its own values")
            if len(value_parts) != len(set(value_parts)):
                raise ValueError(f"Values for key '{key}' contain duplicates: {value_str}")
            
        # If legit, return the original value
        return value

    @model_validator(mode='after')
    def validate_schema_constraints(self) -> 'GroupSchema':
        """
        Root validator to ensure the logical constraints between choices_a and choices_b are upheld.

        Returns:
            The validated GroupSchema instance.

        Raises:
            ValueError: If any logical constraints between choices_a and choices_b are violated.
        """
        # Extract all keys from choices_a and choices_b
        choices_a_keys: Set[str] = {next(iter(choice.keys())) for choice in self.choices_a}
        choices_b_keys: Set[str] = {next(iter(choice.keys())) for choice in self.choices_b}

        # Check if the sets of keys are identical
        if choices_a_keys != choices_b_keys:
            raise ValueError("Keys in choices_a and choices_b are not equal.")

        # Ensure all values in choices_a come from choices_a keys
        for choice in self.choices_a:
            key = next(iter(choice.keys()))
            value_str = choice[key]
            value_parts = value_str.split(',') if value_str else []

            invalid_values = [v for v in value_parts if v not in choices_a_keys]
            if invalid_values:
                raise ValueError(
                    f"Values for key '{key}' in choices_a contain the following illegal letters: {', '.join(invalid_values)}")

        # Ensure all values in choices_b come from choices_b keys
        for choice in self.choices_b:
            key = next(iter(choice.keys()))
            value_str = choice[key]
            value_parts = value_str.split(',') if value_str else []

            invalid_values = [v for v in value_parts if v not in choices_b_keys]
            if invalid_values:
                raise ValueError(
                    f"Values for key '{key}' in choices_b contain the following illegal letters: {', '.join(invalid_values)}")

        # If legit, return self
        return self
