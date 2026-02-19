from pydantic import BaseModel
from typing import List, Optional, Literal

# Enums based on 5W1H and Phase
Category = Literal["Who", "What", "When", "Where", "Why", "How"]
Phase = Literal["Problem", "Solution"]

class Node(BaseModel):
    id: str
    type: str = "default"  # 'default', 'input', 'output', 'ai_suggestion'
    title: str = "" # New: Short interpretation/header
    content: str    # Detailed content or summary
    phase: Phase
    category: Category
    position: dict  # {'x': float, 'y': float}
    is_ai_suggestion: bool = False

class Edge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None

class AnalysisRequest(BaseModel):
    text: str
    current_nodes: List[Node] = []
    current_edges: List[Edge] = []

class AnalysisResponse(BaseModel):
    analysis: dict  # {'category': ..., 'phase': ..., 'summary': ...}
    new_nodes: List[Node]
    new_edges: List[Edge]
