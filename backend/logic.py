import random
import re
from typing import List
from .models import Node, Edge, Category, Phase

# Layout Constants
# Canvas dimensions or relative positions
# X_PROBLEM = 0 # Removed
# X_SOLUTION = 600 # Removed

# Y_TOP = 0      # Why (Problem), Who (Problem/Solution?) -> Adjusted below # Removed
# Y_MIDDLE = 300 # What, How # Removed
# Y_BOTTOM = 600 # When, Where # Removed

# Phase Mapping
PHASE_X_OFFSET = {
    "Problem": 0,
    "Solution": 800
}

# Category Y Mapping (approximate vertical levels)
CATEGORY_Y_OFFSET = {
    "Why": 0,
    "Who": 150,
    "What": 300,
    "How": 450,
    "When": 600,
    "Where": 750
}

def determine_phase(text: str) -> Phase:
    text = text.lower()
    problem_keywords = ["problem", "issue", "hard", "difficult", "slow", "pain", "need", "wish", "bad", 
                       "문제", "어려움", "불편", "힘들", "필요", "부족"]
    solution_keywords = ["solution", "idea", "feature", "app", "website", "create", "build", "make", "fix", 
                        "해결", "아이디어", "기능", "앱", "웹", "만들", "제작", "서비스"]
    
    p_score = sum(1 for k in problem_keywords if k in text)
    s_score = sum(1 for k in solution_keywords if k in text)
    
    if s_score > p_score:
        return "Solution"
    return "Problem"

def extract_5w1h_components(text: str) -> List[dict]:
    """
    Extracts components from text based on 5W1H keywords/particles.
    Uses a 'Backward Capture' heuristic to include modifiers (e.g., "tired people" instead of "people").
    """
    phase = determine_phase(text)
    components = []
    
    # 1. Define Pivot Patterns (Trigger words/particles)
    # Each tuple: (Category, Regex Pattern for the TRIGGER word)
    pivots = [
        ("Who", r"(.*?)(누구|사람|사용자|고객|유저|팀|파트너|client|user|people|customer|who|이|가|은|는)$"), # Subject markers prone to over-matching, be careful
        ("Where", r"(.*?)(에서|안에서|집|회사|학교|사무실|home|office|where)$"),
        ("When", r"(.*?)(에|언제|주말|아침|점심|저녁|평일|시간|날짜|during|when|time|weekend)$"),
        ("Why", r"(.*?)(왜|이유|때문|목적|목표|위해|why|reason|because)$"),
        ("How", r"(.*?)(어떻게|방법|방식|솔루션|how|way|method|로)$"),
        ("What", r"(.*?)(을|를|무엇|제품|서비스|기능|앱|웹|사이트|what|product|service|app)$") # Object markers
    ]
    
    # Specific exclusion list to prevent common particles acting as false positives if needed
    # But for now, we'll try to be inclusive.
    
    words = text.split()
    n_words = len(words)
    
    # We will iterate and claim words.
    used_indices = set()
    extracted_items = []

    # Priority: Specific Nouns > Particles
    # Actually, we should scan for triggers.
    
    for i, word in enumerate(words):
        best_cat = None
        
        # Check against patterns
        for cat, pattern in pivots:
            # We match the word against endpoints
            # Simple check: does the word END with the particle/keyword?
            # Or contains it?
            if re.search(pattern, word):
                # Filter trivial matches for particles if needed (e.g. '가' inside '가방')
                # Korean particles usually at end.
                
                # Refined check for Korean particles: strictly at end
                is_particle_match = False
                if cat in ["Who", "What", "Where", "When", "How", "Why"]:
                     # Check specific particle endings
                     if cat == "Who" and re.search(r"(이|가|은|는)$", word): is_particle_match = True
                     elif cat == "Where" and re.search(r"(에서)$", word): is_particle_match = True
                     elif cat == "When" and re.search(r"(에)$", word): is_particle_match = True
                     elif cat == "What" and re.search(r"(을|를)$", word): is_particle_match = True
                     elif cat == "Why" and re.search(r"(때문|위해)$", word): is_particle_match = True
                
                # Also accept keyword matches (noun hits)
                is_keyword_match = False
                noun_keywords = {
                    "Who": ["사람", "사용자", "고객", "유저"],
                    "Where": ["집", "회사", "학교"],
                    "What": ["제품", "서비스", "앱", "기능"],
                    "How": ["방법", "솔루션"],
                    "Why": ["이유", "목적"]
                }
                
                for k in noun_keywords.get(cat, []):
                    if k in word:
                        is_keyword_match = True
                        break

                if is_particle_match or is_keyword_match:
                    best_cat = cat
                    break # Prioritize order in 'pivots'
        
        if best_cat:
            # CAPTURE PHASE: Grab this word AND previous words until we hit a "limit" or "used" word.
            # Heuristic: Grab up to 2 context words before.
            start_idx = i
            context_limit = 2
            
            for j in range(i-1, -1, -1):
                if j in used_indices:
                    break
                if i - j > context_limit:
                    break
                start_idx = j
            
            # Mark these as used
            current_phrase_indices = range(start_idx, i+1)
            
            # Form phrase
            phrase_words = [words[k] for k in current_phrase_indices]
            phrase = " ".join(phrase_words)
            
            # Update used
            for k in current_phrase_indices:
                used_indices.add(k)
            
            extracted_items.append({
                "category": best_cat,
                "content": phrase,
                "phase": phase,
                "index": i # Store index to sort/dedup roughly?
            })

    # Post-processing: Remove overlaps or duplicates if any (indices set handles overlap)
    # Also, "Using a specialized set" might capture "Target User" better.
    
    final_components = []
    
    title_map = {
        "Who": "Target User / Persona",
        "Where": "Context / Environment",
        "When": "Time / Frequency",
        "Why": "Core Problem / Motivation",
        "How": "Method / Solution",
        "What": "Product / Feature"
    }

    for item in extracted_items:
        # Cleanup regex artifacts if needed
        # Clean phrases: remove trailing particles? 
        # Actually keeping particles is often more natural for reading in Korean ("사용자가")
        
        # Deduplicate categories? 
        # If multiple "Who", maybe combine?
        # For now, append all.
        
        final_components.append({
            "title": title_map.get(item['category'], item['category']),
            "content": item['content'],
            "category": item['category'],
            "phase": phase 
        })

    # Fallback: if no components found, use the whole text as What/Problem
    if not final_components:
        final_components.append({
            "title": "Main Idea",
            "content": text,
            "category": "What", # Default
            "phase": phase
        })
        
    return final_components

def calculate_position(phase: Phase, category: Category, existing_nodes: List[Node]) -> dict:
    """
    Calculates x, y coordinates based on phase and category.
    Adds some random jitter to avoid exact overlap.
    """
    base_x = PHASE_X_OFFSET[phase]
    base_y = CATEGORY_Y_OFFSET[category]
    
    # Simple jitter
    jitter_x = random.randint(-20, 20)
    jitter_y = random.randint(-10, 10)
    
    return {"x": base_x + jitter_x + 100, "y": base_y + jitter_y}


def analyze_text(text: str, current_nodes: List[Node], current_edges: List[Edge]):
    """
    Analyzes text, extracts components, AND automatically generates suggestions.
    """
    components = extract_5w1h_components(text)
    
    new_nodes = []
    new_edges = []
    
    parent_node_id = None
    if current_nodes:
        parent_node_id = current_nodes[-1].id

    # 1. Create nodes from user input
    for comp in components:
        position = calculate_position(comp['phase'], comp['category'], current_nodes + new_nodes)
        
        # Adjust Y if multiple nodes in same category/batch to avoid exact overlap
        # Check against new_nodes
        for existing in new_nodes:
             if abs(existing.position['x'] - position['x']) < 50 and abs(existing.position['y'] - position['y']) < 50:
                 position['y'] += 100

        new_node_id = f"node_{len(current_nodes) + len(new_nodes) + 1}_{random.randint(1000,9999)}"
        
        new_node = Node(
            id=new_node_id,
            type="default",
            title=comp['title'],
            content=comp['content'],
            phase=comp['phase'],
            category=comp['category'],
            position=position,
            is_ai_suggestion=False
        )
        new_nodes.append(new_node)
        
        if parent_node_id:
             new_edges.append(Edge(
                id=f"edge_{parent_node_id}_{new_node.id}",
                source=parent_node_id,
                target=new_node.id,
                label="related"
            ))
            
    # 2. PROACTIVE EXPANSION: Automatically generate a suggestion
    # We pass the *combined* state (current + new) to the suggestion logic
    all_nodes_context = current_nodes + new_nodes
    all_edges_context = current_edges + new_edges
    
    suggestion_result = generate_suggestion(all_nodes_context, all_edges_context)
    
    if suggestion_result:
        new_nodes.extend(suggestion_result['new_nodes'])
        new_edges.extend(suggestion_result['new_edges'])
            
    return {
        "analysis": {
            "category": "Agentic Flow",
            "phase": components[0]['phase'] if components else "Problem",
            "summary": f"Extracted {len(components)} components + AI Suggestion"
        },
        "new_nodes": new_nodes,
        "new_edges": new_edges
    }

def generate_suggestion(current_nodes: List[Node], current_edges: List[Edge]):
    """
    Generates a suggestion node based on the current graph state.
    """
    if not current_nodes:
        return None

    # Logic: Look for missing 5W1H categories or suggest the next step
    problem_nodes = [n for n in current_nodes if n.phase == "Problem"]
    solution_nodes = [n for n in current_nodes if n.phase == "Solution"] # Check solution nodes too
    
    target_phase = "Problem"
    target_category = "What"
    suggestion_title = "AI Insight"
    suggestion_content = ""

    # Strategy 1: Completing the Problem Space
    if problem_nodes:
        existing_categories = set(n.category for n in problem_nodes)
        missing = []
        for cat in ["Who", "Why", "When", "Where"]:
            if cat not in existing_categories:
                missing.append(cat)
        
        if missing:
            target_category = missing[0]
            if target_category == "Who":
                suggestion_title = "Missing Persona"
                suggestion_content = "Who exactly is experiencing this issue?"
            elif target_category == "Why":
                suggestion_title = "Root Cause Analysis"
                suggestion_content = "Why does this problem exist? What is the core reason?"
            elif target_category == "Where":
                suggestion_title = "Context Check"
                suggestion_content = "Where does this usually happen?"
            elif target_category == "When":
                suggestion_title = "Timing Check"
                suggestion_content = "When does this pain point occur?"
        else:
             # Problem space full -> Move to Solution
             target_phase = "Solution"
             target_category = "How"
             suggestion_title = "Ideation"
             suggestion_content = "The problem is clear. How might we solve it?"
    
    # Strategy 2: Extending Solution Space
    elif solution_nodes:
         # If we are already in solution, suggest implementation details or missing aspects
         target_phase = "Solution"
         existing_sol_cats = set(n.category for n in solution_nodes)
         if "How" not in existing_sol_cats:
             target_category = "How"
             suggestion_title = "Implementation"
             suggestion_content = "How will this be implemented technically?"
         else:
             target_category = "What" # Validated features?
             suggestion_title = "Feature Refinement"
             suggestion_content = "What specific features define this solution?"

    # Create suggestion node
    position = calculate_position(target_phase, target_category, current_nodes)
    # Offset to be distinct
    position["x"] += 60
    position["y"] += 60
    
    new_node_id = f"ai_suggestion_{random.randint(1000,9999)}"
    
    new_node = Node(
        id=new_node_id,
        type="default", 
        title=suggestion_title,
        content=suggestion_content,
        phase=target_phase,
        category=target_category,
        position=position,
        is_ai_suggestion=True 
    )
    
    # Connect to relevant parent
    parent_node = current_nodes[-1]
    if target_phase == "Solution" and problem_nodes and not solution_nodes:
         parent_node = problem_nodes[-1]
        
    new_edge = Edge(
        id=f"edge_suggest_{parent_node.id}_{new_node.id}",
        source=parent_node.id,
        target=new_node.id,
        label="suggestion"
    )
    
    return {
        "new_nodes": [new_node],
        "new_edges": [new_edge]
    }
