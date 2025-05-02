from pydantic import BaseModel, Field, constr, field_validator, model_validator
from typing import Dict, List, Set

# Define a Pydantic model for the project schema
class ProjectSchema(BaseModel):
    """
    A Pydantic model that represents a project's data schema.
    """
    titolo: constr(min_length=1, max_length=100) # type: ignore
    numero_gruppi: int = Field(ge=1, le=20)
    numero_partecipanti_per_gruppo: int = Field(ge=4, le=15)
    consegna: constr(min_length=1, max_length=200) # type: ignore
    domandaA: constr(min_length=1, max_length=300) # type: ignore
    domandaA_scelte: constr(min_length=1, max_length=150) # type: ignore
    domandaB: constr(min_length=1, max_length=300) # type: ignore
    domandaB_scelte: constr(min_length=1, max_length=150) # type: ignore
    model_config = {"extra": "forbid"} # Configuration to forbid extra fields

# Define a Pydantic model for the group schema
class GroupSchema(BaseModel):
    """
    A Pydantic model that represents the schema for a group within a project.
    """
    IDGruppo: int = Field(ge=1, le=20)
    scelteA: List[Dict[str, str]]
    scelteB: List[Dict[str, str]]
    model_config = {"extra": "forbid"}  # Configuration to forbid extra fields

    @field_validator('scelteA', 'scelteB')
    def validate_choices(cls, value: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Validator for scelteA and scelteB fields to ensure each choice is well-formed.

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
                raise ValueError(f"Value '{value_str}' must be comma-separated single uppercase letters and contain no empty parts")
            if key in value_parts:
                raise ValueError(f"Key '{key}' cannot be present in its own values")
            if len(value_parts) != len(set(value_parts)):
                raise ValueError(f"Values for key '{key}' contain duplicates: {value_str}")
        return value

    @model_validator(mode='after')
    def validate_schema_constraints(self) -> 'GroupSchema':
        """
        Root validator to ensure the logical constraints between scelteA and scelteB are upheld.

        Returns:
            The validated GroupSchema instance.

        Raises:
            ValueError: If any logical constraints between scelteA and scelteB are violated.
        """
        # Extract all keys from scelteA and scelteB
        scelte_a_keys: Set[str] = {next(iter(choice.keys())) for choice in self.scelteA}
        scelte_b_keys: Set[str] = {next(iter(choice.keys())) for choice in self.scelteB}

        # Check if the sets of keys are identical
        if scelte_a_keys != scelte_b_keys:
            raise ValueError("Keys in scelteA and scelteB must match.")

        # Ensure all values in scelteA come from scelteA keys
        for choice in self.scelteA:
            key: str = next(iter(choice.keys()))
            value_str: str = choice[key]
            value_parts: List[str] = value_str.split(',')

            invalid_values = [v for v in value_parts if v not in scelte_a_keys]
            if invalid_values:
                raise ValueError(
                    f"Values for key '{key}' in scelteA contain letters not present as keys in scelteA: {', '.join(invalid_values)}")

        # Ensure all values in scelteB come from scelteB keys
        for choice in self.scelteB:
            key: str = next(iter(choice.keys()))
            value_str: str = choice[key]
            value_parts: List[str] = value_str.split(',')

            invalid_values = [v for v in value_parts if v not in scelte_b_keys]
            if invalid_values:
                raise ValueError(
                    f"Values for key '{key}' in scelteB contain letters not present as keys in scelteB: {', '.join(invalid_values)}")

        return self
