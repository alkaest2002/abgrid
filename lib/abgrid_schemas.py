"""
Filename: abgrid_schema.py
Description: Defines Pydantic models for project and group schemas, ensuring data integrity and validation.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from pydantic import BaseModel, Field, constr, field_validator, model_validator
from typing import Dict, List, Set

# Define a Pydantic model for the project schema
class ProjectSchema(BaseModel):
    """
    A Pydantic model that represents a project's data schema.
    """
    progetto: constr(min_length=1, max_length=50) # type: ignore
    numero_gruppi: int = Field(ge=1, le=20)
    numero_partecipanti_per_gruppo: int = Field(ge=4, le=15)
    consegna: constr(min_length=1, max_length=200) # type: ignore
    domanda_a: constr(min_length=1, max_length=300) # type: ignore
    domanda_a_scelte: constr(min_length=1, max_length=150) # type: ignore
    domanda_b: constr(min_length=1, max_length=300) # type: ignore
    domanda_b_scelte: constr(min_length=1, max_length=150) # type: ignore
    model_config = {"extra": "forbid"}

# Define a Pydantic model for the group schema
class GroupSchema(BaseModel):
    """
    A Pydantic model that represents the schema for a group within a project.
    """
    gruppo: int = Field(ge=1, le=20)
    scelte_a: List[Dict[str, str]]
    scelte_b: List[Dict[str, str]]
    model_config = {"extra": "forbid"}

    @field_validator("scelte_a", "scelte_b")
    def validate_choices(cls, value: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Validator for scelte_a and scelte_b fields to ensure each choice is well-formed.

        Args:
            value: A list of dictionaries representing choices.

        Returns:
            The validated list of choices.

        Raises:
            ValueError: If any validation check fails.
        """
        for choice_dict in value:
            # Get key and its corresponding value string
            key: str = next(iter(choice_dict.keys()))
            value_str: str = choice_dict[key]
            value_parts: List[str] = value_str.split(',')

            # Validate each choice
            if not isinstance(choice_dict, dict):
                raise ValueError("Each choice must be a dictionary")
            if len(choice_dict) != 1:
                raise ValueError("Each choice must have exactly one key-value pair")
            if not key.isalpha() or not key.isupper() or len(key) != 1:
                raise ValueError(f"Key '{key}' must be a single uppercase letter")
            if not value_str:
                raise ValueError(f"Key '{key}' has no values")
            if any(not part for part in value_parts):
                raise ValueError(f"Value '{value_str}' contains empty entries due to misplaced commas")
            if not all(len(part) == 1 and part.isalpha() and part.isupper() for part in value_parts):
                raise ValueError(f"Value '{value_str}' must be comma-separated single uppercase letters and contain no empty values")
            if key in value_parts:
                raise ValueError(f"Key '{key}' cannot be present in its own values")
            if len(value_parts) != len(set(value_parts)):
                raise ValueError(f"Values for key '{key}' contain duplicates: {value_str}")
        return value

    @model_validator(mode='after')
    def validate_schema_constraints(self) -> 'GroupSchema':
        """
        Root validator to ensure the logical constraints between scelte_a and scelte_b are upheld.

        Returns:
            The validated GroupSchema instance.

        Raises:
            ValueError: If any logical constraints between scelte_a and scelte_b are violated.
        """
        # Extract all keys from scelte_a and scelte_b
        scelte_a_keys: Set[str] = {next(iter(choice.keys())) for choice in self.scelte_a}
        scelte_b_keys: Set[str] = {next(iter(choice.keys())) for choice in self.scelte_b}

        # Check if the sets of keys are identical
        if scelte_a_keys != scelte_b_keys:
            raise ValueError("Keys in scelte_a and scelte_b are not equal.")

        # Ensure all values in scelte_a come from scelte_a keys
        for choice in self.scelte_a:
            key: str = next(iter(choice.keys()))
            value_str: str = choice[key]
            value_parts: List[str] = value_str.split(',')

            invalid_values = [v for v in value_parts if v not in scelte_a_keys]
            if invalid_values:
                raise ValueError(
                    f"Values for key '{key}' in scelte_a contain the following illegal letters: {', '.join(invalid_values)}")

        # Ensure all values in scelte_b come from scelte_b keys
        for choice in self.scelte_b:
            key: str = next(iter(choice.keys()))
            value_str: str = choice[key]
            value_parts: List[str] = value_str.split(',')

            invalid_values = [v for v in value_parts if v not in scelte_b_keys]
            if invalid_values:
                raise ValueError(
                    f"Values for key '{key}' in scelte_b contain the following illegal letters: {', '.join(invalid_values)}")

        return self
