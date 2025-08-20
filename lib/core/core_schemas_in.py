"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import re
from typing import Any

from pydantic import BaseModel, model_validator

from lib.core import SYMBOLS
from lib.core.core_schemas_errors import PydanticValidationError
from lib.core.core_utils import verify_hmac_signature


FORBIDDEN_CHARS = re.compile(r"[^A-Za-zÀ-ÖØ-öø-ÿĀ-ſƀ-ɏḀ-ỿЀ-ӿͰ-Ͽ\d\s\'\.,\-\?\!]")


class ABGridGroupSchemaIn(BaseModel):
    """Input schema for AB-Grid group data.

    Validates group data.

    Attributes:
        project_title: Project title (1-100 characters).
        question_a: First question text (1-300 characters).
        question_b: Second question text (1-300 characters).
        group: Group identifier (integer).
        members: Number of members per group (8-50).

    Notes:
        All fields are typed as Any to enable custom validation and
        error collection in a single pass.
    """

    project_title: Any
    question_a: Any
    question_b: Any
    group: Any
    members: Any

    model_config = {
        "extra": "forbid"
    }

    @model_validator(mode="before")
    @classmethod
    def _validate_all_fields(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate all fields and collect errors.

        Performs comprehensive validation of all fields, collecting all
        validation errors and raising a single exception if any fail.

        Args:
            data: Raw input data dictionary.

        Returns:
            Validated data dictionary.

        Raises:
            PydanticValidationError: If validation errors are found.
        """
        errors = []

        # Validate fields
        errors.extend(_validate_text_field("project_title", data.get("project_title"), 1, 100))
        errors.extend(_validate_text_field("question_a", data.get("question_a"), 1, 300))
        errors.extend(_validate_text_field("question_b", data.get("question_b"), 1, 300))
        errors.extend(_validate_group_field(data.get("group")))
        cls._validate_members_field(data.get("members"), errors)

        if errors:
            raise PydanticValidationError(errors)

        return data

    @classmethod
    def _validate_members_field(cls, value: Any, errors: list[dict[str, Any]]) -> None:
        """Validate the members field.

        Ensures members is an integer between 8 and 50 inclusive.

        Args:
            value: Value to validate.
            errors: List to append errors to.
        """
        min_group_size: int = 8
        max_group_size: int = 50
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
        elif not (min_group_size <= value <= max_group_size):
            errors.append({
                "location": "members",
                "value_to_blame": value,
                "error_message": "field_is_out_of_range"
            })


class ABGridReportMultiStepSchemaIn(BaseModel):
    """Input schema for AB-Grid report data via multi-step process.

    Validates report data.

    Attributes:
        project: Project dictionary.
        sna: Social network analysis dictionary.
        sociogram: Sociogram network analysis.

    Notes:
        - All fields typed as Any for custom validation.
    """

    project: dict[str, Any]
    sna: dict[str, Any]
    sociogram: dict[str, Any]

    @model_validator(mode="before")
    @classmethod
    def _validate_all_fields(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate all fields comprehensively including HMAC signature verification.

        Args:
            data: Raw input data dictionary.

        Returns:
            Validated data dictionary.

        Raises:
            PydanticValidationError: If validation errors are found.
        """
        errors = []

        # Validate each field
        for field_name in ["project", "sna", "sociogram"]:
            field_value = data.get(field_name)

            # Check if field exists
            if field_value is None:
                errors.append({
                    "location": field_name,
                    "value_to_blame": None,
                    "error_message": "required_field_is_missing"
                })
                continue

            # Check if field is a dictionary
            if not isinstance(field_value, dict):
                errors.append({
                    "location": field_name,
                    "value_to_blame": str(field_value)[:10],
                    "error_message": "field_must_be_a_dictionary"
                })
                continue

            # Check for mandatory _signature key
            if "_signature" not in field_value:
                errors.append({
                    "location": field_name,
                    "value_to_blame": str(field_value)[:10],
                    "error_message": "signature_is_missing"
                })
                continue

            try:
                # Verify HMAC signature
                if not verify_hmac_signature(field_value):
                    errors.append({
                        "location": field_name,
                        "value_to_blame": field_value.get("_signature"),
                        "error_message": "signature_is_invalid"
                    })
            except Exception:
                errors.append({
                    "location": field_name,
                    "value_to_blame": str(field_value),
                    "error_message": "signature_verification_error"
                })

        if errors:
            raise PydanticValidationError(errors)

        return data

class ABGridReportSchemaIn(BaseModel):
    """Input schema for AB-Grid report data.

    Validates report data.

    Attributes:
        project_title: Project title (1-100 characters).
        question_a: First question text (1-300 characters).
        question_b: Second question text (1-300 characters).
        group: Group identifier (integer).
        choices_a: Choice dictionaries for question A (non-empty list).
        choices_b: Choice dictionaries for question B (non-empty list).

    Notes:
        - All fields typed as Any for custom validation.
        - Keys in choices_a and choices_b must be identical.
        - Values must reference valid keys.
        - Keys and values must be single alphabetic characters.
        - Maximum 60% of nodes can have no choice.
        - Value count must be less than total key count.
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
    def _validate_all_fields(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate all fields comprehensively.

        Validates all fields including complex choice validation logic:
        - Basic field validation.
        - Choice structure correctness.
        - Choice key consistency between questions.
        - Valid value references.
        - Maximum 60% nodes without choices.
        - Value count less than key count.

        Args:
            data: Raw input data dictionary.

        Returns:
            Validated data dictionary.

        Raises:
            PydanticValidationError: If validation errors are found.
        """
        errors = []

        # Validate basic fields
        errors.extend(_validate_text_field("project_title", data.get("project_title"), 1, 100))
        errors.extend(_validate_text_field("question_a", data.get("question_a"), 1, 300))
        errors.extend(_validate_text_field("question_b", data.get("question_b"), 1, 300))
        errors.extend(_validate_group_field(data.get("group")))

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
            raise PydanticValidationError(errors)
        return data

    @model_validator(mode="after")
    def _strip_choice_values_after(self) -> "ABGridReportSchemaIn":
        """Strip spaces from choice values post-validation.

        Removes spaces around commas in choice values after model validation
        confirms data structure validity.

        Returns:
            Model instance with stripped choice values.
        """
        for field_name in ["choices_a", "choices_b"]:
            choices = getattr(self, field_name)
            for choice_dict in choices:
                for key, value in choice_dict.items():
                    if isinstance(value, str) and value.strip():
                        stripped_value = ",".join(part.strip() for part in value.split(","))
                        choice_dict[key] = stripped_value

        return self

    @classmethod
    def _validate_choices_structure(cls, data: dict[str, Any], field_name: str, errors: list[dict[str, Any]]) -> set[str]:
        """Validate choices structure and format.

        Validates:
        - Choices is non-empty list.
        - Each choice is single key-value dictionary.
        - Keys are single alphabetic characters (no duplicates).
        - Keys don't exceed SYMBOLS length.
        - Values have correct format.
        - Keys don't self-reference.
        - No duplicate values within choice.
        - Value count less than key count.

        Args:
            data: Full data dictionary.
            field_name: Name of choices field ("choices_a" or "choices_b").
            errors: List to append errors to.

        Returns:
            Set of extracted keys from choices.
        """
        choices = data.get(field_name)
        extracted_keys: set[str] = set()

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

        # First pass: extract all keys to determine total count
        temp_keys = set()
        for choice_dict in choices:
            if isinstance(choice_dict, dict) and len(choice_dict) == 1:
                key = next(iter(choice_dict.keys()))
                if isinstance(key, str) and len(key) == 1 and key.isalpha():
                    temp_keys.add(key)

        total_keys = len(temp_keys)

        # Second pass: validate each choice with the total key count
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
            elif key in extracted_keys:
                errors.append({
                    "location": f"{field_name}, {key}",
                    "value_to_blame": key,
                    "error_message": "duplicate_key_found"
                })
            else:
                # Add valid key to extracted_keys
                extracted_keys.add(key)

                # Validate value format with total_keys constraint
                cls._validate_value_format(field_name, key, value_str, errors, total_keys)

        return extracted_keys

    @classmethod
    def _validate_value_format(cls, field_name: str, key: str, value_str: Any,
                               errors: list[dict[str, Any]], total_keys: int) -> None:
        """Validate choice value format.

        Validates values are None, empty strings, or comma-separated single
        alphabetic characters. Ensures no self-reference, no duplicates,
        and value count less than key count.

        Args:
            field_name: Name of choices field.
            key: Choice key.
            value_str: Value to validate.
            errors: List to append errors to.
            total_keys: Total number of keys in choice set.
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

        value_parts = [part.strip() for part in value_str.split(",")]

        # Check that the number of values is less than the total number of keys
        if len(value_parts) >= total_keys:
            errors.append({
                "location": f"{field_name}, {key}",
                "value_to_blame": value_str,
                "error_message": "values_list_too_long"
            })

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
    def _validate_value_references(cls, data: dict[str, Any], all_valid_keys: set[str], errors: list[dict[str, Any]]) -> None:
        """Validate value references point to valid keys.

        Ensures every value in choices references only existing keys from
        the combined key set of both choices_a and choices_b.

        Args:
            data: Full data dictionary.
            all_valid_keys: Set of all valid keys from both choices.
            errors: List to append errors to.
        """
        for field_name in ["choices_a", "choices_b"]:
            choices = data.get(field_name)
            if not isinstance(choices, list):
                continue

            for choice_dict in choices:
                if not isinstance(choice_dict, dict) or len(choice_dict) != 1:
                    continue

                key = next(iter(choice_dict.keys()))
                value_str = choice_dict[key]

                if value_str is None or not isinstance(value_str, str) or not value_str.strip():
                    continue

                value_parts = [part.strip() for part in value_str.split(",")]
                invalid_references = [part for part in value_parts if part and part not in all_valid_keys]

                if invalid_references:
                    errors.append({
                        "location": f"{field_name}, {key}",
                        "value_to_blame": value_str,
                        "error_message": "values_reference_invalid_keys"
                    })

    @classmethod
    def _validate_minimum_nodes_with_choices(cls, data: dict[str, Any], errors: list[dict[str, Any]]) -> None:
        """Validate choice completion requirements.

        For both choices_a and choices_b, validates:
        - At least 3 nodes have expressed a choice.
        - Maximum 60% of nodes have empty values.

        A node has expressed a choice if it has a non-null, non-empty value.

        Args:
            data: Full data dictionary.
            errors: List to append errors to.
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
    def _validate_single_choice_set(cls, choices: list[dict[str, Any]], field_name: str, errors: list[dict[str, Any]]) -> None:
        """Validate single choice set for completion requirements.

        Args:
            choices: List of choice dictionaries.
            field_name: Name of choice field for error reporting.
            errors: List to append errors to.
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

        # Validate that no more than 60% of nodes have empty values
        empty_percentage = (nodes_without_choices_count / total_nodes) * 100
        empty_percentage_max = 60
        if empty_percentage > empty_percentage_max:
            errors.append({
                "location": field_name,
                "value_to_blame": round(empty_percentage, 1),
                "error_message": "too_many_nodes_have_empty_values"
            })


def _validate_text_field(field_name: str, value: Any, min_len: int, max_len: int) -> list[dict[str, Any]]:
    """Validate text field with length and character constraints.

    Validates field is a string within length bounds containing only
    allowed characters (letters, numbers, safe punctuation).

    Args:
        field_name: Name of field for error reporting.
        value: Value to validate.
        min_len: Minimum allowed string length.
        max_len: Maximum allowed string length.

    Returns:
        List of error dictionaries. Empty if validation passes.
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
            "error_message": "field_is_too_short"
        })

    if len(value) > max_len:
        errors.append({
            "location": field_name,
            "value_to_blame": value,
            "error_message": "field_is_too_long"
        })

    # Check for forbidden characters
    if FORBIDDEN_CHARS.findall(value):
        errors.append({
            "location": field_name,
            "value_to_blame": value,
            "error_message": "field_contains_invalid_characters"
        })

    return errors


def _validate_group_field(value: Any) -> list[dict[str, Any]]:
    """Validate group field as integer.

    Args:
        value: Value to validate.

    Returns:
        List of error dictionaries. Empty if validation passes.
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
