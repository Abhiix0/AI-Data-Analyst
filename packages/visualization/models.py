"""Typed Chart Models and Specifications for Plotly and Next.js frontend rendering."""
from __future__ import annotations
import uuid
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

ChartType = Literal["bar", "line", "scatter", "box", "histogram", "heatmap", "pie"]


class ChartSpec(BaseModel):
    """Declarative specification for interactive chart rendering."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chart_type: ChartType = Field(..., description="Chart visualization type")
    title: str = Field(..., description="Descriptive chart title")
    x: Optional[str] = Field(None, description="X-axis column or dimension")
    y: Optional[Union[str, List[str]]] = Field(None, description="Y-axis column or metric(s)")
    color: Optional[str] = Field(None, description="Grouping or color categorical column")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Row-oriented dataset records")
    orientation: Optional[Literal["v", "h"]] = Field("v", description="Vertical or horizontal orientation")
    barmode: Optional[Literal["group", "stack", "overlay", "relative"]] = Field(None, description="Bar stacking mode")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional Plotly layout options (labels, scales, annotations)")
