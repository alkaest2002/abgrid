"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from typing import Any

from pydantic import BaseModel


class ABGridGroupSchemaOut(BaseModel):
    """Output schema for group data.

    Contains basic group information extracted from ABGridGroupSchemaIn
    with processed member symbols for display and validation.

    Attributes:
        project_title: Title of the AB-Grid project.
        question_a: Text of question A from the project .
        question_b: Text of question B from the project .
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

class ABGridSnaSchemaOut(BaseModel):
    """Output schema for comprehensive report data.

    Contains Project data and SNA analys (first step of multistep report generation).

    Attributes:
        project: Project data.
        sna: Complete social network analysis results.
    """
    project: dict[str, Any]
    sna: dict[str, Any]

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "forbid"
    }

class ABGridReportSchemaOut(BaseModel):
    """Output schema for comprehensive report data.

    Contains complete analysis results including project metadata, network
    analysis, sociogram data (optional), relevant nodes, and isolated nodes.

    Attributes:
        year: Current year when report was generated.
        project_title: Title of the AB-Grid project.
        question_a: Text of question A from the project .
        question_b: Text of question B from the project .
        group: Group identifier.
        group_size: Number of participants in the group.
        sna: Complete social network analysis results.
        sociogram: Sociogram analysis results (None if not requested).
        relevant_nodes: Relevant nodes from both networks.
        isolated_nodes: Isolated nodes from both networks.
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
