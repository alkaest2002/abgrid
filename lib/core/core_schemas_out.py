"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from pydantic import BaseModel

from lib.core.core_schemas import (
    ABGridIsolatedNodesSchema,
    ABGridRelevantNodesSchema,
    ABGridSNASchema,
    ABGridSociogramSchema,
)


class ABGridGroupSchemaOut(BaseModel):
    """Output schema for group data.

    Contains basic group information extracted from ABGridGroupSchemaIn
    with processed member symbols for display and validation.

    Attributes:
        project_title: Title of the AB-Grid project.
        question_a: Text of question A from the survey.
        question_b: Text of question B from the survey.
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

class ABGridReportSchemaOut(BaseModel):
    """Output schema for comprehensive report data.

    Contains complete analysis results including project metadata, network
    analysis, sociogram data (optional), relevant nodes, and isolated nodes.

    Attributes:
        year: Current year when report was generated.
        project_title: Title of the AB-Grid project.
        question_a: Text of question A from the survey.
        question_b: Text of question B from the survey.
        group: Group identifier.
        group_size: Number of participants in the group.
        sna: Complete social network analysis results.
        sociogram: Sociogram analysis results (None if not requested).
        relevant_nodes_ab: Relevant nodes from both networks.
        isolated_nodes_ab: Isolated nodes from both networks.
    """
    year: int
    project_title: str
    question_a: str
    question_b: str
    group: int
    group_size: int
    sna: ABGridSNASchema
    sociogram: ABGridSociogramSchema | None
    relevant_nodes_ab: ABGridRelevantNodesSchema
    isolated_nodes_ab: ABGridIsolatedNodesSchema

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "forbid"
    }
