
from typing import Any

import orjson

from lib.core.core_data import CoreData
from lib.core.core_schemas_in import (
    ABGridReportStep1SchemaIn,
    ABGridReportStep2SchemaIn,
)


# Define constants
STEP_1 = 1
STEP_2 = 2

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
    """
    try:
        # Handle Function URL vs direct invocation
        if "body" in event:

            # If body is a string
            if isinstance(event["body"], str):
                # Parse JSON body
                body_data: dict[str, Any] = orjson.loads(event["body"])
            else:
                # Body is already a dict
                body_data = event["body"]

            # Extract parameters from body
            step: int = body_data.get("step", 0)
            data: dict[str, Any] = body_data.get("data", {})
            with_sociogram: bool = body_data.get("with_sociogram", False)
        else:
            # Direct invocation
            step = event.get("step", 0)
            data = event.get("data", {})
            with_sociogram = event.get("with_sociogram", False)

        # Initialize CoreData instance
        core_data = CoreData()

        # Validate step and data
        if step not in [1, 2] or len(data.keys()) == 0:
            error_message = "required_data_missing_or_invalid"
            raise ValueError(error_message)  # noqa: TRY301

        result = None

        # Execute appropriate step
        if step == STEP_1:
            # Validate input data for step 1
            validated_step_1_data = ABGridReportStep1SchemaIn(**data)
            # Call step 1 method
            result = core_data.get_multistep_step_1(validated_step_1_data)

        elif step == STEP_2:
            # Validate input data for step 2
            validated_step_2_data = ABGridReportStep2SchemaIn(**data)
            # Call step 2 method
            result = core_data.get_multistep_step_2(validated_step_2_data, with_sociogram)

        # Return successful response
        return {
            "statusCode": 200,
            "body": orjson.dumps({
                "success": True,
                "step": step,
                "data": result
            }, default=str).decode("utf-8")
        }

    except ValueError as e:
        return {
            "statusCode": 400,
            "body": orjson.dumps({
                "error": str(e),
                "step": event.get("step", 0)
            }).decode("utf-8")
        }

    except Exception:
        return {
            "statusCode": 500,
            "body": orjson.dumps({
                "error": "aws_internal_server_error",
                "step": event.get("step", 0)
            }).decode("utf-8")
        }
