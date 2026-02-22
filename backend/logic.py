import os
import random
import uuid
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from .models import Node, Edge, NodeData, Category, Phase, UserNode, CrossConnectionResult, ChatMessage

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

    def calculate_position(self, phase: Phase, category: Category, slot_index: int = 0) -> Dict[str, float]:
        """
        같은 (phase, category) 조합의 노드들은 열(column) 단위로 배치.
        slot_index=0 → 중앙, 1 → 오른쪽, 2 → 왼쪽, 3 → 더 오른쪽 ...
        """
        x_range = PROBLEM_X_RANGE if phase == "Problem" else SOLUTION_X_RANGE
        base_x = (x_range[0] + x_range[1]) / 2
        base_y = CATEGORY_Y_MAP.get(category, 300)

        NODE_STRIDE_X = 230  # 노드 너비(200) + 간격(30)
        NODE_STRIDE_Y = 160  # 노드 높이(120) + 간격(40)

        # 0 → 0, 1 → +1, 2 → -1, 3 → +2, 4 → -2, ...
        if slot_index == 0:
            col_offset = 0
        elif slot_index % 2 == 1:
            col_offset = (slot_index + 1) // 2
        else:
            col_offset = -(slot_index // 2)

        row = slot_index // 4  # 4개마다 아래 줄로

        return {
            "x": base_x + col_offset * NODE_STRIDE_X,
            "y": base_y + row * NODE_STRIDE_Y
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

기존 노드 목록을 보고, 새로 만든 user_nodes 중 **의미적으로 관련된** 것과 연결하라.
- existing_node_id: 기존 노드 ID
- new_node_index: 연결될 user_nodes 인덱스
- connection_label: 관계 설명 한 구절
- **기존 노드가 존재하면 반드시 최소 1개는 연결할 것.** 같은 카테고리, 같은 phase, 또는 주제의 연장선상이면 반드시 연결하라.
- 최대 3개.

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

        # ── 1. Build slot_counts from history (기존 노드들이 각 슬롯을 몇 개 차지하는지) ──
        slot_counts: Dict[str, int] = {}
        for h_node in history:
            h_data = h_node.get("data", {})
            h_phase = h_data.get("phase", "")
            h_cat = h_data.get("category", "")
            if h_phase and h_cat:
                key = f"{h_phase}_{h_cat}"
                slot_counts[key] = slot_counts.get(key, 0) + 1

        # ── 2. Create user nodes ──
        created_nodes = []
        created_node_ids = []

        for i, un in enumerate(result.user_nodes):
            node_id = str(uuid.uuid4())
            key = f"{un.phase}_{un.category}"
            slot_idx = slot_counts.get(key, 0)
            pos = self.calculate_position(un.phase, un.category, slot_index=slot_idx)
            slot_counts[key] = slot_idx + 1  # 다음 노드를 위해 슬롯 증가

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

        # ── 3. Create suggestion node ──
        suggestion_id = str(uuid.uuid4())
        # 제안 노드는 해당 category/phase의 다음 슬롯에 배치
        s_key = f"{result.suggestion_phase}_{result.suggestion_category}"
        s_slot = slot_counts.get(s_key, 0)
        suggest_pos = self.calculate_position(
            result.suggestion_phase,
            result.suggestion_category,
            slot_index=s_slot
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
        cross_connected_new_ids = set()

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
            cross_connected_new_ids.add(target_id)

        # ── 6. Fallback: 기존 노드가 있지만 cross_connections가 없으면
        #       첫 번째 새 노드를 가장 가까운 기존 노드와 강제 연결 ──
        if history and created_node_ids and not cross_connected_new_ids:
            first_new_id = created_node_ids[0]
            first_new_cat = result.user_nodes[0].category if result.user_nodes else None

            # 같은 카테고리 기존 노드 우선, 없으면 가장 마지막 기존 노드
            best_existing = None
            for h_node in reversed(history):
                h_cat = h_node.get("data", {}).get("category", "")
                if h_cat == first_new_cat:
                    best_existing = h_node.get("id")
                    break
            if best_existing is None:
                best_existing = history[-1].get("id")

            if best_existing and best_existing in existing_ids:
                edge_id = f"e-cross-{best_existing}-{first_new_id}"
                # 중복 엣지 방지
                existing_edge_ids = {e.id for e in edges}
                if edge_id not in existing_edge_ids:
                    edges.append(Edge(
                        id=edge_id,
                        source=best_existing,
                        target=first_new_id,
                        label="관련"
                    ))

        return {
            "nodes": all_nodes,
            "edges": edges
        }

    # ─────────────────────────────────────────────
    # 2. AI 채팅: suggestion 카드 클릭 후 대화
    # ─────────────────────────────────────────────
    def chat_with_suggestion(
        self,
        suggestion_title: str,
        suggestion_content: str,
        suggestion_category: str,
        suggestion_phase: str,
        messages: List[ChatMessage],
        user_message: str,
    ) -> str:
        system_prompt = f"""너는 사용자의 아이디어를 함께 탐구하는 AI 대화 파트너다.

아래 제안 카드를 중심으로 사용자와 자유롭게 대화하라.
- 처음 대화(messages가 비어 있을 때)라면 제안의 핵심을 2~3문장으로 친절하게 설명하고, 사용자가 어떤 방향으로 발전시키고 싶은지 열린 질문으로 마무리하라.
- 이후 대화에서는 사용자의 답변을 토대로 아이디어를 구체화‧확장‧검증하라.
- 응답은 200자 내외로 간결하게 유지하라.
- 언어는 한국어.

[제안 카드]
카테고리: {suggestion_category} / {suggestion_phase}
제목: {suggestion_title}
내용: {suggestion_content}
"""
        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        chat_history.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                *chat_history,
            ],
        )
        return response.choices[0].message.content

    # ─────────────────────────────────────────────
    # 3. 대화 내용 → ReactFlow 노드+엣지 변환
    # ─────────────────────────────────────────────
    def chat_to_nodes(
        self,
        suggestion_title: str,
        suggestion_content: str,
        suggestion_category: str,
        suggestion_phase: str,
        messages: List[ChatMessage],
        existing_nodes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        history_context = self.build_history_context(existing_nodes)

        conversation_text = "\n".join(
            f"[{m.role.upper()}] {m.content}" for m in messages
        )

        system_prompt = f"""
너는 대화 내용을 6하원칙 노드로 구조화하는 에이전트다.

아래 대화를 분석해서 핵심 아이디어를 1~4개의 노드로 추출하라.
각 노드는 label(짧은 동사형 제목), content(한 문장), category(Who/What/When/Where/Why/How), phase(Problem/Solution)로 구성.

[제안 카드 원본]
{suggestion_category}/{suggestion_phase}: {suggestion_title} - {suggestion_content}

[대화 내용]
{conversation_text}

## 기존 노드 목록 (cross_connections 시 사용)
{history_context}
"""

        class ChatNodeResult(BaseModel):
            user_nodes: List[UserNode]
            cross_connections: List[CrossConnectionResult]

        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "대화를 노드로 구조화해줘."},
            ],
            response_format=ChatNodeResult,
        )
        result = completion.choices[0].message.parsed

        # 슬롯 카운트 (기존 노드 기반)
        slot_counts: Dict[str, int] = {}
        for h_node in existing_nodes:
            h_data = h_node.get("data", {})
            h_phase = h_data.get("phase", "")
            h_cat = h_data.get("category", "")
            if h_phase and h_cat:
                key = f"{h_phase}_{h_cat}"
                slot_counts[key] = slot_counts.get(key, 0) + 1

        created_nodes = []
        created_node_ids = []
        for un in result.user_nodes:
            node_id = str(uuid.uuid4())
            key = f"{un.phase}_{un.category}"
            slot_idx = slot_counts.get(key, 0)
            pos = self.calculate_position(un.phase, un.category, slot_index=slot_idx)
            slot_counts[key] = slot_idx + 1

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

        edges = []
        # 같은 대화에서 나온 노드들 순차 연결
        for i in range(len(created_node_ids) - 1):
            edges.append(Edge(
                id=f"e-chat-{created_node_ids[i]}-{created_node_ids[i+1]}",
                source=created_node_ids[i],
                target=created_node_ids[i + 1],
                label="이어서"
            ))

        # cross-connections to existing nodes
        existing_ids = {n.get("id") for n in existing_nodes}
        cross_connected = set()
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
            cross_connected.add(target_id)

        # fallback: 기존 노드가 있는데 아무 연결도 없으면 마지막 기존 노드에 연결
        if existing_nodes and created_node_ids and not cross_connected:
            first_id = created_node_ids[0]
            anchor = existing_nodes[-1].get("id")
            if anchor and anchor in existing_ids:
                edges.append(Edge(
                    id=f"e-cross-{anchor}-{first_id}",
                    source=anchor,
                    target=first_id,
                    label="대화에서 발전"
                ))

        return {"nodes": created_nodes, "edges": edges}
