from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any


# Enums based on 5W1H and Phase
Category = Literal["Who", "What", "When", "Where", "Why", "How"]
Phase = Literal["Problem", "Solution"]

class UserNode(BaseModel):
    """AI가 인풋 문장에서 추출하는 6하원칙 노드 하나"""
    label: str          # 동사형 짧은 제목
    content: str        # 한 문장 상세 내용
    category: Category  # 6하원칙 분류
    phase: Phase        # Problem / Solution

class CrossConnectionResult(BaseModel):
    """기존 노드와의 연결 정보"""
    existing_node_id: str   # history에서 선택한 기존 노드 ID
    new_node_index: int     # cross_connection 대상: user_nodes 배열의 인덱스 (0-based)
    connection_label: str   # 연결 관계 설명

class NodeData(BaseModel):
    label: str              # Summarized Title
    content: str            # One sentence summary details
    category: Category
    phase: Phase
    is_ai_generated: bool

class Node(BaseModel):
    id: str
    type: str = "default"
    data: NodeData
    position: Dict[str, float]  # {"x": float, "y": float}

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


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    suggestion_title: str
    suggestion_content: str
    suggestion_category: str
    suggestion_phase: str
    messages: List[ChatMessage] = []   # 이전 대화 히스토리
    user_message: str                  # 현재 사용자 메시지


class ChatResponse(BaseModel):
    reply: str


class ChatToNodesRequest(BaseModel):
    suggestion_title: str
    suggestion_content: str
    suggestion_category: str
    suggestion_phase: str
    messages: List[ChatMessage]
    existing_nodes: List[Dict[str, Any]] = []  # history (기존 노드들)
