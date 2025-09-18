
"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
from typing import Any

import orjson

from lib.core.core_data import CoreData
from lib.core.core_schemas_in import (
    ABGridReportSchemaIn,
    ABGridReportStep1SchemaIn,
    ABGridReportStep2SchemaIn,
)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:  # noqa: ARG001
    """
    AWS Lambda function handler for multi-step AB-Grid report generation.

    Args:
        event: Lambda event containing:
            - step: Integer (1 or 2) indicating which step to execute
            - data: Dictionary containing the input data for the step
            - with_sociogram: Boolean (optional, for step 2 only)
        context: Lambda context object

    Returns:
        Dictionary containing:
            - statusCode: HTTP status code
            - body: JSON string with result data or error message

    Raises:
        ValueError: If required data is missing or invalid
        Exception: For any unexpected errors
    """
    # Initialize result
    result: dict[str, Any] = {}

    try:
        # If event contains "body"
        if "body" in event:
            # Extract parameters from body
            body_data: dict[str, Any] = orjson.loads(event.get("body", "{}"))
            step: int = body_data.get("step", -1)
            data: dict[str, Any] = body_data.get("data", {})
            with_sociogram: bool = body_data.get("with_sociogram", False)
        else:
            # Extract parameters from event
            step = event.get("step", -1)
            data = event.get("data", {})
            with_sociogram = event.get("with_sociogram", False)

        # Validate step and data
        if step not in [0, 1, 2] or len(data.keys()) == 0:
            error_message = "invalid_report_data"
            raise ValueError(error_message)  # noqa: TRY301

        # Initialize CoreData instance
        core_data = CoreData()

        # Execute the appropriate step
        match step:

            # Execute step 0: get full report data
            case 0:
                # Validate input data and get result
                validated_data = ABGridReportSchemaIn(**data)
                result = core_data.get_report_data(validated_data, with_sociogram)

            # Execute step 1: get step 1 data
            case 1:
                # Validate input data and get result
                validated_step_1_data = ABGridReportStep1SchemaIn(**data)
                result = core_data.get_multistep_step_1(validated_step_1_data)

            # Execute step 2: get step 2 data
            case 2:
                # Validate input data and get result
                validated_step_2_data = ABGridReportStep2SchemaIn(**data)
                result = core_data.get_multistep_step_2(validated_step_2_data, with_sociogram)

        # Return successful response
        return {
            "statusCode": 200,
            "body": orjson.dumps({
                "success": True,
                "step": step,
                "with_sociogram": with_sociogram,
                "data": result
            }, default=str).decode("utf-8")
        }

    except ValueError as e:
        return {
            "statusCode": 400,
            "body": orjson.dumps({
                "error": str(e),
                "step": step,
                "with_sociogram": with_sociogram,
            }).decode("utf-8")
        }

    except Exception:
        return {
            "statusCode": 500,
            "body": orjson.dumps({
                "error": "aws_internal_server_error",
                "step": step,
                "with_sociogram": with_sociogram,
            }).decode("utf-8")
        }
