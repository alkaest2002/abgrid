"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from typing import Any

from pydantic import BaseModel


class ABGridGroupSchemaOut(BaseModel):
    """Output schema for Group data.

    Contains basic group information extracted from ABGridGroupSchemaIn
    with processed member symbols for display and validation.

    Attributes:
        project_title: Title of the project.
        question_a: Text of question A from the project.
        question_b: Text of question B from the project.
        group: Group identifier.
        members: List of member symbols (A, B, C, etc.) based on group size.
    """
    project_title: str
    question_a: str
    question_b: str
    group: int
    members: list[str]

    model_config = {
        "extra": "forbid"
    }


##################################################################################################################
#   SINGLE STEP REPORT GENERATION
##################################################################################################################
#
#   This class handles the report generation process in a single request
#   For high specs servers or terminal apps
#
##################################################################################################################

class ABGridReportSchemaOut(BaseModel):
    """Output schema for Report data.

    Complete report schema containing all analysis results for AB-Grid project reporting.

    Attributes:
        year: Current year when report was generated.
        project_title: Title of the AB-Grid project.
        question_a: Text of question A from the project.
        question_b: Text of question B from the project.
        group: Group identifier.
        group_size: Number of participants in the group.
        sna: Social network analysis results as dictionary.
        sociogram: Sociogram analysis results as dictionary (None if not requested).
        relevant_nodes: Relevant nodes from both networks as dictionary.
        isolated_nodes: Isolated nodes from both networks as dictionary.
    """
    year: int
    project_title: str
    question_a: str
    question_b: str
    group: int
    group_size: int
    sna: dict[str, Any]
    sociogram: dict[str, Any] | None
    relevant_nodes: dict[str, Any]
    isolated_nodes: dict[str, Any]

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "forbid"
    }


##################################################################################################################
#   MULTI STEP REPORT GENERATION
##################################################################################################################
#
#   These classes split the report generation process into three steps
#   For low specs servers
#
##################################################################################################################

class ABGridReportStep1SchemaOut(BaseModel):
    """Output schema for step 1 data in multi-step report generation.

    Contains Group data and SNA analysis results for multistep report generation.

    Attributes:
        group_data: Group data as dictionary.
        sna_data: Social network analysis results as dictionary.
    """
    group_data: dict[str, Any]
    sna_data: dict[str, Any]

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "forbid"
    }


class ABGridReportStep2SchemaOut(ABGridReportSchemaOut):
    """Output schema for AB-Grid step 2 data via multi-step process"""


class ABGridReportStep3SchemaOut(ABGridReportSchemaOut):
    """Output schema for AB-Grid step 3 data via multi-step process"""
