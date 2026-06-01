# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Nhật Quang
- **Student ID**: 2A202600813
- **Date**: 01/06/2026

---

## I. Technical Contribution (15 Points)

My primary responsibility was implementing the `search_rooms` tool and the `rank_rooms` tool, as well as contributing to the flowchart documentation of the ReAct loop.

### Modules Implemented

| File | Description |
|------|-------------|
| `lab3/tools.py` — `search_rooms()` | Filter rooms by capacity and amenities from the mock DB |
| `lab3/tools.py` — `rank_rooms()` | Score and rank candidate rooms by fit quality |
| `lab3/flowchart.md` | Mermaid flowchart of the full ReAct loop |

### Code Highlights

**`search_rooms()`** — filters the room database by minimum capacity and required amenities:

```python
def search_rooms(capacity: int, amenities: Optional[List[str]] = None) -> List[Dict]:
    """
    Returns rooms with capacity >= requested and all required amenities present.
    Returns [] if no rooms match — caller must handle empty result gracefully.
    """
    if amenities is None:
        amenities = []
    results = []
    for room in ROOMS_DB:
        if room["capacity"] < capacity:
            continue
        if amenities and not all(a in room["amenities"] for a in amenities):
            continue
        results.append(room)
    return results
```

**`rank_rooms()`** — multi-criteria scoring (capacity fit 50%, amenity bonus 30%, slot count 20%):

```python
def rank_rooms(rooms: List[Dict], criteria: Dict) -> List[Dict]:
    needed_capacity = criteria.get("capacity", 0)
    scored = []
    for room in rooms:
        score = 0.0
        # Capacity fit: closer to needed = higher score
        if needed_capacity > 0:
            ratio = needed_capacity / room["capacity"]
            score += max(0.0, 1.0 - abs(1.0 - ratio)) * 0.5
        # Slot availability bonus
        score += min(len(room["available_slots"]) * 0.05, 0.2)
        scored.append({**room, "score": round(score, 3)})
    return sorted(scored, key=lambda r: r["score"], reverse=True)
```

### Documentation

The `search_rooms` → `check_availability` → `rank_rooms` pipeline forms the core tool chain of the ReAct agent. Each tool has a single responsibility:

1. **search_rooms**: Broad filter — "which rooms could work?"
2. **check_availability**: Hard constraint — "which of those are actually free?"
3. **rank_rooms**: Optimization — "which free room is the best fit?"

This separation of concerns makes each tool independently testable and replaceable.

---

## II. Debugging Case Study (10 Points)

### Problem Description

During early testing, `search_rooms` returned an empty list for queries like:

> "Tôi cần phòng lab máy tính cho 40 người"

Even though rooms B205 and D202 (both with `"lab"` amenity) existed in the database.

### Log Source

```
Action: search_rooms(40, ["lab máy tính"])
Observation: Không tìm thấy phòng nào phù hợp.
```

The agent received an empty result and either looped or gave up — even though valid rooms existed.

### Diagnosis

**Root cause: Vietnamese amenity names not mapped to English keys in the DB.**

The LLM naturally generated `"lab máy tính"` (Vietnamese) while the database stored `"lab"` (English). The `all(a in room["amenities"] for a in amenities)` check failed because `"lab máy tính" != "lab"`.

### Solution

Added a Vietnamese → English amenity mapping in the agent's argument parser:

```python
AMENITY_MAP = {
    "lab máy tính": "lab",
    "lab": "lab",
    "máy chiếu": "projector",
    "projector": "projector",
    "điều hòa": "ac",
    "ac": "ac",
    "micro": "mic",
    "mic": "mic",
    "quay phim": "recording",
    "recording": "recording",
    "bảng trắng": "whiteboard",
    "whiteboard": "whiteboard",
}

def _parse_search_rooms_args(self, args_str: str):
    # ... parse capacity ...
    amenities = []
    for item in raw_list:
        item_lower = str(item).lower().strip()
        mapped = AMENITY_MAP.get(item_lower)
        if mapped:
            amenities.append(mapped)
        else:
            # Partial match fallback
            for vn_key, en_val in AMENITY_MAP.items():
                if vn_key in item_lower or item_lower in vn_key:
                    amenities.append(en_val)
                    break
    return capacity, list(dict.fromkeys(amenities))  # dedup
```

After this fix, `search_rooms(40, ["lab máy tính"])` correctly mapped to `search_rooms(40, ["lab"])` and returned B205 and D202.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning — Thought as a Planning Layer

The `Thought` block serves as the agent's planning layer — it forces the model to decompose the problem before acting. This is fundamentally different from how a chatbot works:

- **Chatbot**: Input → single LLM call → Output. No intermediate state.
- **ReAct Agent**: Input → Thought (plan) → Action (execute) → Observation (update state) → repeat.

The key insight is that **Thought externalizes the model's reasoning**, making it inspectable and debuggable. When the agent fails, you can read the Thought trace and identify exactly where the reasoning went wrong — something impossible with a chatbot's black-box response.

### 2. Reliability — When Agent Fails

The agent is only as reliable as its tools. I observed three failure modes:

| Failure Mode | Example | Impact |
|-------------|---------|--------|
| Tool returns empty (no match) | `search_rooms(40, ["lab máy tính"])` → `[]` | Agent loops or gives up |
| Tool argument format mismatch | LLM generates `"lab máy tính"` vs DB key `"lab"` | Silent wrong result |
| Model too weak to follow format | Phi-3-mini generates free text instead of `Action: tool(args)` | Parser fails, loop |

The chatbot avoids all three failure modes — but only because it doesn't use tools at all. It trades reliability for accuracy: always returns *something*, but that something may be fabricated.

### 3. Observation — Grounding the Agent

Without Observations, the agent would be no better than a chatbot — it would just be generating text that *looks like* tool calls without actually using real data. The Observation step is what closes the loop between the agent's reasoning and the real world:

```
Thought: I need to find rooms for 30 people.
Action: search_rooms(30)
Observation: [A101, A201, A301, B205, B301, C204, D202]  ← REAL DATA
Thought: Now I need to check which ones are free on Monday 9am.
Action: check_availability("A101", "Mon 09:00")
Observation: A101 is booked.                              ← REAL DATA
Thought: Try A301.
...
Final Answer: A301 is available.                          ← GROUNDED CONCLUSION
```

Each Observation narrows the solution space using real data. The chatbot skips all of this and guesses — which works for simple cases but fails for anything requiring current, accurate information.

---

## IV. Future Improvements (5 Points)

### Scalability

The current `ROOMS_DB` is a hardcoded Python list. For a production system:

```python
# Replace with database-backed search
import sqlite3

def search_rooms_db(capacity: int, amenities: list[str]) -> list[dict]:
    conn = sqlite3.connect("rooms.db")
    placeholders = ",".join("?" * len(amenities))
    query = f"""
        SELECT r.* FROM rooms r
        JOIN room_amenities ra ON r.id = ra.room_id
        WHERE r.capacity >= ?
        GROUP BY r.id
        HAVING COUNT(CASE WHEN ra.amenity IN ({placeholders}) THEN 1 END) = ?
    """
    return conn.execute(query, [capacity] + amenities + [len(amenities)]).fetchall()
```

### Safety

- **Hallucination guard**: Already implemented in `_clean_final_answer()` — reject Final Answers containing room IDs not in the database
- **Tool input validation**: Add Pydantic schemas to validate tool arguments before execution
- **Rate limiting**: Prevent the agent from calling the same tool more than 3 times per session

### Performance

- **Parallel availability checks**: After `search_rooms` returns N candidates, check all N rooms in parallel using `asyncio.gather()` instead of sequentially
- **Result caching**: Cache `search_rooms` results for identical queries within a session — the room database doesn't change during a conversation
- **Smarter ranking**: Incorporate user preference history (preferred building, typical group size) into the `rank_rooms` scoring function
