from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any

# Enums based on 5W1H and Phase
Category = Literal["Who", "What", "When", "Where", "Why", "How"]
Phase = Literal["Problem", "Solution"]

class CrossConnectionResult(BaseModel):
    existing_node_id: str       # 기존 노드 ID (history에서 선택)
    connection_label: str       # 연결 관계 설명


class NodeData(BaseModel):
    label: str # Summarized Title
    content: str # One sentence summary details
    category: Category
    phase: Phase
    is_ai_generated: bool

class Node(BaseModel):
    id: str
    type: str = "default"
    data: NodeData
    position: Dict[str, float] # {"x": float, "y": float}

class Edge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None

class AnalysisRequest(BaseModel):
    text: str
    history: List[Dict[str, Any]] = []

class AnalysisResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
