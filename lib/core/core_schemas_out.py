"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import pandas as pd
from pydantic import BaseModel

from lib.core.core_schemas_in import ABGridSNASchemaIn, ABGridSociogramSchemaIn


class ABGridRelevantNodesSchema(BaseModel):
    """Schema for relevant nodes analysis results.

    Attributes:
        a: Positive relevance nodes from network A.
        b: Negative relevance nodes from network B.
    """
    a: pd.DataFrame  # Positive relevance nodes from network A
    b: pd.DataFrame  # Negative relevance nodes from network B

    model_config = {
        "arbitrary_types_allowed": True  # Allow pandas DataFrames
    }


class ABGridIsolatedNodesSchema(BaseModel):
    """Schema for isolated nodes by network type.

    Attributes:
        a: Isolated nodes from network A.
        b: Isolated nodes from network B.
    """
    a: pd.Index  # Isolated nodes from network A
    b: pd.Index  # Isolated nodes from network B

    model_config = {
        "arbitrary_types_allowed": True  # Allow pandas Index
    }


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
    project_title: str  # Title of the AB-Grid project
    question_a: str  # Text of question A from the survey
    question_b: str  # Text of question B from the survey
    group: int  # Group identifier
    members: list[str]  # List of member symbols (A, B, C, etc.) based on group size

    model_config = {
        "extra": "forbid"  # Don't allow extra fields
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
    year: int  # Current year when report was generated
    project_title: str  # Title of the AB-Grid project
    question_a: str  # Text of question A from the survey
    question_b: str  # Text of question B from the survey
    group: int  # Group identifier
    group_size: int  # Number of participants in the group
    sna: ABGridSNASchemaIn  # Complete social network analysis results
    sociogram: ABGridSociogramSchemaIn | None  # Sociogram analysis results (None if not requested)
    relevant_nodes_ab: ABGridRelevantNodesSchema  # Relevant nodes from both networks
    isolated_nodes_ab: ABGridIsolatedNodesSchema  # Isolated nodes from both networks

    model_config = {
        "arbitrary_types_allowed": True,  # Allow complex types like DataFrames
        "extra": "forbid"  # Don't allow extra fields
    }

