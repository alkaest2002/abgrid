"""
Filename: abgrid_schemas.py
Description: Defines Pydantic models for project and group schemas, ensuring data integrity and validation.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.types import constr
from typing import Dict, List, Optional


class ProjectSchema(BaseModel):
    """
    Pydantic model representing a project's data schema.
    
    This model validates project information including title, description, 
    and two questions with their associated answer choices.

    Attributes:
        project_title: The project title (1-80 characters)
        explanation: Project description/explanation (1-500 characters)
        question_a: First question text (1-300 characters)
        question_a_choices: Answer choices for question A (1-150 characters)
        question_b: Second question text (1-300 characters)
        question_b_choices: Answer choices for question B (1-150 characters)
    """
    project_title: constr(min_length=1, max_length=80) # type: ignore
    explanation: constr(min_length=1, max_length=500) # type: ignore
    question_a: constr(min_length=1, max_length=300) # type: ignore
    question_a_choices: constr(min_length=1, max_length=150) # type: ignore
    question_b: constr(min_length=1, max_length=300) # type: ignore
    question_b_choices: constr(min_length=1, max_length=150) # type: ignore
    
    model_config = {"extra": "forbid"}


class GroupSchema(BaseModel):
    """
    Pydantic model representing a group within a project.
    
    This model validates the structure of answer choices for both questions
    within a group, ensuring consistency and logical relationships between
    the choices.

    Attributes:
        group: Group identifier (1-20)
        choices_a: List of choice dictionaries for question A. Each dictionary
                  contains a single-letter key mapped to a comma-separated string
                  of single letter values (or None)
        choices_b: List of choice dictionaries for question B. Each dictionary
                  contains a single-letter key mapped to a comma-separated string
                  of single-letter values (or None)
    
    Notes:
        - Keys in choices_a and choices_b must be identical
        - All values must reference valid keys from either choices_a or choices_b
        - Keys and values must be single alphabetic characters
    """
    group: int = Field(ge=1, le=20)
    choices_a: List[Dict[str, Optional[str]]]
    choices_b: List[Dict[str, Optional[str]]]
    
    model_config = {"extra": "forbid"}

    @field_validator("choices_a", "choices_b")
    @classmethod
    def validate_choices(cls, value: List[Dict[str, Optional[str]]]) -> List[Dict[str, Optional[str]]]:
        """
        Validate the structure and content of choice dictionaries.

        Args:
            value: List of choice dictionaries to validate

        Returns:
            List[Dict[str, Optional[str]]]: The validated list of choice dictionaries

        Raises:
            ValueError: If any validation rule fails:
                - Choice is not a dictionary
                - Dictionary doesn't have exactly one key-value pair
                - Key is not a single alphabetic character
                - Value contains empty entries or non-alphabetic characters
                - Value contains duplicate entries
                - Key appears in its own value list
        """
        for choice_dict in value:
            if not isinstance(choice_dict, dict):
                raise ValueError("Each choice must be a dictionary")
            
            if len(choice_dict) != 1:
                raise ValueError("Each choice must have exactly one key-value pair")
            
            # Get the single key-value pair
            key: str = next(iter(choice_dict.keys()))
            value_str: Optional[str] = choice_dict[key]
            
            # Validate key
            if len(key) != 1 or not key.isalpha():
                raise ValueError(f"Key '{key}' must be a single alphabetic character")
            
            # Skip validation if value is None
            if value_str is None:
                continue
                
            # Parse and validate value string
            value_parts: List[str] = value_str.split(',') if value_str else []
            
            if any(not part for part in value_parts):
                raise ValueError(f"Value '{value_str}' contains empty entries due to misplaced commas")
            
            if any(len(part) != 1 or not part.isalpha() for part in value_parts):
                raise ValueError(f"Value '{value_str}' must contain only single alphabetic characters")
            
            if key in value_parts:
                raise ValueError(f"Key '{key}' cannot be present in its own values")
            
            if len(value_parts) != len(set(value_parts)):
                raise ValueError(f"Values for key '{key}' contain duplicates: {value_str}")
        
        return value

    @model_validator(mode="after")
    def validate_schema_constraints(self) -> "GroupSchema":
        """
        Validate logical constraints between choices_a and choices_b.

        Returns:
            GroupSchema: The validated GroupSchema instance

        Raises:
            ValueError: If coherence rules between choices_a and choices_b are violated:
                - Key sets are not identical
                - Values reference non-existent keys

        Notes:
            Ensures that:
            - Keys in choices_a and choices_b are identical
            - All values reference valid keys from the combined key set
            - Cross-references between choices are consistent
        """
        # Extract all keys from both choice sets
        choices_a_keys: set[str] = {next(iter(choice.keys())) for choice in self.choices_a}
        choices_b_keys: set[str] = {next(iter(choice.keys())) for choice in self.choices_b}

        # Verify key sets are identical
        if choices_a_keys != choices_b_keys:
            raise ValueError("Keys in choices_a and choices_b must be identical")

        # Validate that all values reference valid keys
        all_valid_keys: set[str] = choices_a_keys  # Same as choices_b_keys due to above check
        
        for choices_type, choices_list in [("a", self.choices_a), ("b", self.choices_b)]:
            for choice in choices_list:
                key: str = next(iter(choice.keys()))
                value_str: Optional[str] = choice[key]
                
                if value_str is None:
                    continue
                    
                value_parts: List[str] = value_str.split(',') if value_str else []
                invalid_values: List[str] = [v for v in value_parts if v not in all_valid_keys]
                
                if invalid_values:
                    raise ValueError(
                        f"Values for key '{key}' in choices_{choices_type} contain "
                        f"invalid references: {', '.join(invalid_values)}"
                    )

        return self


class ReportSchema(BaseModel):
    """
    Pydantic model representing a report's data schema.
    
    This model validates report information by combining project and group data
    into a unified report structure for comprehensive data validation.

    Args:
        project_data: The project data containing project-level information
        group_data: The group data containing group-level choices and constraints

    Returns:
        ReportSchema: A validated report instance containing both project and group data
    """
    project_data: ProjectSchema
    group_data: GroupSchema
