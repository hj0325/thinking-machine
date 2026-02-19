import os
import random
import uuid
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from .models import Node, Edge, NodeData, Category, Phase

# Load .env.local first (takes precedence), then .env
load_dotenv(dotenv_path=".env.local")
load_dotenv()

# --- Configuration ---
# Layout Zones
PROBLEM_X_RANGE = (0, 400)
SOLUTION_X_RANGE = (600, 1000)

# Vertical Layout (Fixed Y positions)
CATEGORY_Y_MAP = {
    "Why": 0,
    "Who": 150,
    "What": 300,
    "How": 450,
    "When": 600,
    "Where": 750
}

class AIAnalysisResult(BaseModel):
    user_label: str
    user_content: str
    user_category: Category
    user_phase: Phase
    suggestion_label: str
    suggestion_content: str
    suggestion_category: Category
    suggestion_phase: Phase
    connection_label: str

class ThinkingAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def calculate_position(self, phase: Phase, category: Category) -> Dict[str, float]:
        x_range = PROBLEM_X_RANGE if phase == "Problem" else SOLUTION_X_RANGE
        
        # Center X in the range + jitter
        mid_x = (x_range[0] + x_range[1]) / 2
        jitter_x = random.randint(-50, 50)
        
        base_y = CATEGORY_Y_MAP.get(category, 300)
        jitter_y = random.randint(-10, 10)
        
        return {
            "x": mid_x + jitter_x,
            "y": base_y + jitter_y
        }

    def process_idea(self, user_input: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_prompt = """
        너는 사용자의 아이디어를 구조화하고 확장하는 자율형 에이전트다.
        사용자의 입력을 받으면 아래 단계를 거쳐 단 하나의 JSON으로 응답하라.
        
        1. 분류: 문장 전체의 의도를 파악해 6하원칙(Who, What, When, Where, Why, How) 중 하나와 Phase[Problem/Solution] 중 하나를 골라라.
        2. 요약: 입력 내용을 '동사형'의 짧은 제목(label)과 한 문장의 상세 내용(content)으로 요약하라.
        3. 제안: 이 아이디어를 확장할 수 있는 날카로운 질문이나 추가 아이디어를 하나 생성하라. (suggestion_label, suggestion_content)
        4. 연결: 사용자 노드와 제안 노드의 관계(connection_label)를 정의하라.
        
        절대로 문장을 단어 단위로 쪼개어 여러 노드를 만들지 마라.
        """
        
        # Use gpt-4o-mini for speed and cost effectiveness, or gpt-4o for quality. 
        # Using gpt-4o-2024-08-06 as per common practice for structured output.
        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            response_format=AIAnalysisResult,
        )
        
        result = completion.choices[0].message.parsed
        
        # Create User Node
        user_node_id = str(uuid.uuid4())
        user_pos = self.calculate_position(result.user_phase, result.user_category)
        
        user_node = Node(
            id=user_node_id,
            type="default",
            data=NodeData(
                label=result.user_label,
                content=result.user_content,
                category=result.user_category,
                phase=result.user_phase,
                is_ai_generated=False
            ),
            position=user_pos
        )
        
        # Create Suggestion Node
        suggest_node_id = str(uuid.uuid4())
        
        # Suggestion position
        suggest_pos = self.calculate_position(result.suggestion_phase, result.suggestion_category)
        
        # Ensure they don't overlap too much if same category/phase
        if result.user_phase == result.suggestion_phase and result.user_category == result.suggestion_category:
             suggest_pos["x"] += 50
             suggest_pos["y"] += 50

        suggest_node = Node(
            id=suggest_node_id,
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
        
        # Create Edge
        edge = Edge(
            id=f"e-{user_node_id}-{suggest_node_id}",
            source=user_node_id,
            target=suggest_node_id,
            label=result.connection_label
        )
        
        return {
            "nodes": [user_node, suggest_node],
            "edges": [edge]
        }
