"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import os
from typing import Any

import orjson

from lib.core.core_data import CoreData
from lib.core.core_export import CoreExport
from lib.core.core_schemas_in import ABGridReportSchemaIn
from lib.core.core_templates import CoreRenderer


AWS_API_KEY = os.getenv("AWS_API_KEY")

# Initialize once at module level
_abgrid_data = CoreData()
_abgrid_renderer = CoreRenderer()

def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:  # noqa: ARG001
    """
    AWS Lambda function handler for multi-step AB-Grid report generation.

    Args:
        event: Lambda event object containing headers and request data
        context: Lambda context object

    Returns:
        Dictionary containing:
            - statusCode: HTTP status code (200, 403, or 500)
            - body: JSON string with result data or error message

    Raises:
        Exception: For any unexpected errors
    """
    try:
        # Check for API key authentication
        headers = event.get("headers", {})
        api_key = headers.get("x-api-key")

        # Return 403 if API key is missing or invalid
        if not api_key or api_key != AWS_API_KEY:
            return {
                "statusCode": 403,
                "body": {
                    "error": "Forbidden: Invalid or missing API key"
                }
            }

        # If event contains "body"
        if "body" in event:

            # Get body data
            body = event.get("body", "")

            # Parse body
            body_data: dict[str, Any] = orjson.loads(body)

            # Extract parameters from body
            data: dict[str, Any] = body_data.get("data", {})
            with_sociogram: bool = body_data.get("with_sociogram", False)
            language: str = body_data.get("language", "it")

        else:

            # Extract parameters from event
            data = event.get("data", {})
            with_sociogram = event.get("with_sociogram", False)
            language = event.get("language", "it")

        # Validate and process data
        validated_data = ABGridReportSchemaIn(**data)
        data = _abgrid_data.get_report_data(validated_data, with_sociogram)

        # Get template path
        template_path = f"{language}/report.html"

        # Render template
        rendered_report = _abgrid_renderer.render(template_path, data)

        # Serialize data to JSON
        data_json = CoreExport.to_json(data)

    # Handle errors
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {
                "error": str(e),
            }
        }

    # Return successful response
    else:
        return {
            "statusCode": 200,
            "body": {
                "rendered_report": rendered_report,
                "data_json": data_json,
            }
        }
