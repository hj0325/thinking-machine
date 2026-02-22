import os
import random
import uuid
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from .models import Node, Edge, NodeData, Category, Phase, UserNode, CrossConnectionResult

# Load .env.local first (takes precedence), then .env
load_dotenv(dotenv_path=".env.local")
load_dotenv()

# --- Layout Configuration ---
PROBLEM_X_RANGE = (0, 400)
SOLUTION_X_RANGE = (600, 1000)

CATEGORY_Y_MAP = {
    "Why":   0,
    "Who":   150,
    "What":  300,
    "How":   450,
    "When":  600,
    "Where": 750
}

# ---- Pydantic model for AI structured output ----
class AIAnalysisResult(BaseModel):
    # 인풋에서 추출한 6하원칙 노드 목록 (1~4개)
    user_nodes: List[UserNode]

    # AI가 생성하는 제안 노드 1개 (가장 핵심 user_node 기반)
    suggestion_label: str
    suggestion_content: str
    suggestion_category: Category
    suggestion_phase: Phase

    # user_nodes 중 제안 노드와 연결될 노드의 인덱스 (0-based)
    suggestion_connects_to_index: int

    # 제안 노드 연결 레이블
    connection_label: str

    # 기존 노드와의 cross-connection
    cross_connections: List[CrossConnectionResult]


class ThinkingAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def calculate_position(self, phase: Phase, category: Category, offset_x: int = 0, offset_y: int = 0) -> Dict[str, float]:
        x_range = PROBLEM_X_RANGE if phase == "Problem" else SOLUTION_X_RANGE
        mid_x = (x_range[0] + x_range[1]) / 2
        jitter_x = random.randint(-40, 40)
        base_y = CATEGORY_Y_MAP.get(category, 300)
        jitter_y = random.randint(-10, 10)
        return {
            "x": mid_x + jitter_x + offset_x,
            "y": base_y + jitter_y + offset_y
        }

    def build_history_context(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return "기존 노드 없음."
        lines = []
        for node in history:
            node_id = node.get("id", "unknown")
            data = node.get("data", {})
            title = data.get("title", "")
            category = data.get("category", "")
            phase = data.get("phase", "")
            if not isinstance(title, str):
                title = "(unknown)"
            lines.append(f"- ID: {node_id} | [{phase}/{category}] {title}")
        return "\n".join(lines)

    def process_idea(self, user_input: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        history_context = self.build_history_context(history)

        system_prompt = f"""
너는 사용자의 아이디어를 구조화하고 확장하는 자율형 에이전트다.
사용자의 한 문장 인풋을 받아 6하원칙(Who/What/When/Where/Why/How) 관점으로 분해하고,
관련된 노드들을 추출한 뒤 JSON으로 응답하라.

---

## STEP 1. 인풋 분해 → user_nodes 생성

사용자의 입력에서 **명확하게 존재하는 6하원칙 요소**만 노드로 추출하라.
- 최소 1개, 최대 4개
- 문장에 명시되거나 강하게 내포된 요소만 포함할 것. 억지로 만들지 마라.
- 각 노드는 label(동사형 짧은 제목), content(한 문장 상세), category, phase로 구성

**카테고리 선택 기준 (엄격히 준수):**
| Category | 선택 조건 |
|----------|----------|
| Who      | 사용자·대상·이해관계자·주체가 핵심 |
| What     | 구체적 결과물·기능·서비스·제품이 핵심 |
| When     | 시간·타이밍·순서·빈도가 핵심 |
| Where    | 장소·공간·채널·환경이 핵심 |
| Why      | 목적·이유·동기·문제의식이 핵심 |
| How      | 방법·프로세스·수단·전략이 핵심 |

**Phase 선택 기준:**
- Problem: 현재 문제/니즈/현상 파악 관점
- Solution: 해결책/구현/실행 관점

**예시:**
입력: "일상에 지친 사람들이 진정한 휴식을 즐길 수 있는 광장을 만들고 싶다"
→ user_nodes:
  [0] Who / Problem: "지친 현대인 정의" / 일상에 지쳐 진정한 휴식이 필요한 사람들
  [1] What / Solution: "휴식 광장 조성" / 진정한 휴식을 제공하는 도심 광장을 만든다
  [2] Why / Problem: "휴식 부재 문제" / 현대인이 일상에서 진정한 휴식을 취하지 못하고 있다

## STEP 2. AI 제안 노드 (1개)

user_nodes 전체를 보고 아이디어를 확장하는 날카로운 질문이나 제안을 하나 만들어라.
- suggestion_connects_to_index: 제안 노드가 직접 연결될 user_nodes의 인덱스 (가장 핵심적인 노드)

## STEP 3. 기존 노드 연결 (cross_connections)

아래 기존 노드 목록을 보고, 새로 만든 user_nodes 중 **의미적으로 관련된** 것과 연결하라.
- existing_node_id: 기존 노드 ID
- new_node_index: 연결될 user_nodes 인덱스
- connection_label: 관계 설명 한 구절
- 관련 없으면 빈 배열. 최대 3개.

## 기존 노드 목록
{history_context}
"""

        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            response_format=AIAnalysisResult,
        )

        result = completion.choices[0].message.parsed

        # ── 1. Create user nodes ──
        created_nodes = []
        created_node_ids = []

        for i, un in enumerate(result.user_nodes):
            node_id = str(uuid.uuid4())
            # 같은 카테고리/페이즈 노드가 겹치지 않도록 인덱스 기반 오프셋
            pos = self.calculate_position(un.phase, un.category, offset_x=i * 30, offset_y=i * 30)
            node = Node(
                id=node_id,
                type="default",
                data=NodeData(
                    label=un.label,
                    content=un.content,
                    category=un.category,
                    phase=un.phase,
                    is_ai_generated=False
                ),
                position=pos
            )
            created_nodes.append(node)
            created_node_ids.append(node_id)

        # ── 2. Create suggestion node ──
        suggestion_id = str(uuid.uuid4())
        suggest_pos = self.calculate_position(
            result.suggestion_phase,
            result.suggestion_category,
            offset_x=60,
            offset_y=0
        )
        suggestion_node = Node(
            id=suggestion_id,
            type="default",
            data=NodeData(
                label=result.suggestion_label,
                content=result.suggestion_content,
                category=result.suggestion_category,
                phase=result.suggestion_phase,
                is_ai_generated=True
            ),
            position=suggest_pos
        )

        all_nodes = created_nodes + [suggestion_node]
        edges = []

        # ── 3. Connect user nodes sequentially (같은 인풋 내 노드들 연결) ──
        for i in range(len(created_node_ids) - 1):
            edges.append(Edge(
                id=f"e-input-{created_node_ids[i]}-{created_node_ids[i+1]}",
                source=created_node_ids[i],
                target=created_node_ids[i + 1],
                label="관련"
            ))

        # ── 4. Connect main user node → suggestion ──
        idx = result.suggestion_connects_to_index
        if idx >= len(created_node_ids):
            idx = 0
        main_node_id = created_node_ids[idx]
        edges.append(Edge(
            id=f"e-suggest-{main_node_id}-{suggestion_id}",
            source=main_node_id,
            target=suggestion_id,
            label=result.connection_label
        ))

        # ── 5. Cross-connections to existing nodes ──
        existing_ids = {node.get("id") for node in history}
        for cross in result.cross_connections:
            if cross.existing_node_id not in existing_ids:
                continue
            new_idx = cross.new_node_index
            if new_idx >= len(created_node_ids):
                new_idx = 0
            target_id = created_node_ids[new_idx]
            edges.append(Edge(
                id=f"e-cross-{cross.existing_node_id}-{target_id}",
                source=cross.existing_node_id,
                target=target_id,
                label=cross.connection_label
            ))

        return {
            "nodes": all_nodes,
            "edges": edges
        }
