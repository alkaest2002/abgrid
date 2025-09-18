import orjson
from typing import Any, Dict

from lib.core.core_data import CoreData
from lib.core.core_schemas_in import (
    ABGridReportStep1SchemaIn,
    ABGridReportStep2SchemaIn,
)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
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
         # Handle Function URL (body is JSON string) vs direct invocation
        if "body" in event and event["body"]:
            
            # If body is a string
            if isinstance(event["body"], str):
                # Parse JSON body
                body_data: Dict[str, Any] = orjson.loads(event["body"])
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
            error_message = "required data is missing or invalid"
            raise ValueError(error_message)
        
        result = None
        
        # Execute appropriate step
        if step == 1:
            # Validate input data for step 1
            validated_step_1_data = ABGridReportStep1SchemaIn(**data)
            # Call step 1 method
            result = core_data.get_multistep_step_1(validated_step_1_data)
            
        elif step == 2:
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
            }, default=str).decode('utf-8')
        }
        
    except ValueError as e:
        return {
            "statusCode": 400,
            "body": orjson.dumps({
                "error": f"Validation error: {str(e)}",
                "step": event.get("step", 0)
            }).decode('utf-8')
        }
        
    except Exception as e:        
        return {
            "statusCode": 500,
            "body": orjson.dumps({
                "error": "Internal server error",
                "step": event.get("step", 0)
            }).decode('utf-8')
        }