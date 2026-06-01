# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: 42
- **Team Members**: 
    - Nguyễn Quang Minh - 2A202600816
    - Nguyễn Văn Dưỡng - 2A202600967
    - Phùng Hữu Uy - 2A202600886
    - Nguyễn Nhật Quang-2A202600813
    - Nguyễn Tuấn Dũng - 2A202600848
- **Deployment Date**: 01/06/2026

---

## 1. Executive Summary

This project builds a classroom recommendation system in two layers: a baseline chatbot and a ReAct agent.

- **Success Rate**: 71% on 7 test cases (Kimi-K2 model) / 14% with Phi-3-mini local
- **Baseline chatbot**: one LLM call only, used to infer a likely classroom recommendation from the prompt.
- **ReAct agent**: iteratively calls tools to search rooms, check availability, and rank candidates before answering.
- **Key outcome**: the agent is more grounded than the chatbot because it reasons over tool outputs and the `data/classroom.json` dataset instead of relying on pure model inference.
- **Main tradeoff**: the chatbot is simpler and faster, but it can hallucinate or overgeneralize; the agent is more reliable, but depends on correct tool formatting and multiple LLM/tool turns.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

The agent follows a repeated Thought-Action-Observation loop with a hard limit of 5 iterations.

1. The LLM receives the user request and a system prompt listing the available tools.
2. The model outputs either a `Thought` plus `Action`, or a `Final Answer`.
3. The agent parses the action with regex, validates tool arguments, and executes the requested tool.
4. The tool result is appended back into the conversation as an `Observation`.
5. The loop stops when a `Final Answer` appears or when the maximum step limit is reached.

This implementation also captures a structured `trace` so the full reasoning path can be inspected after execution.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `search_rooms` | `search_rooms(capacity=int, amenities=list[str])` | Filter classrooms from `data/classroom.json` by minimum capacity and required amenities. |
| `check_availability` | `check_availability(room_id=str, time_slot=str)` | Check whether a room is free for a requested day/time slot based on the mock schedule derived from the JSON dataset. |
| `rank_rooms` | `rank_rooms(rooms=list[dict], criteria=dict)` | Rank candidate rooms by closest capacity fit and amenity match score. |

### 2.3 LLM Providers Used
- **Primary**: Local Phi-3 via `llama-cpp-python` for offline execution.
- **Secondary (Backup)**: OpenAIProvider and GeminiProvider remain available through the shared provider abstraction.
- **Best Results**: Kimi-K2 (via OpenRouter free tier) — 71% success rate, 2-3 steps per task, ~12s average latency.

### 2.4 Individual Contributions

| Member | Primary Contribution |
|--------|---------------------|
| Nguyễn Văn Dưỡng | ReAct agent core loop, loop detection, hallucination guard, flowchart, trace documentation |
| Nguyễn Quang Minh | `check_availability` tool, `data/classroom.json` dataset (322 rooms), time-range parsing fix |
| Nguyễn Nhật Quang | `search_rooms` tool, `rank_rooms` tool, Vietnamese amenity mapping |
| Nguyễn Tuấn Dũng | Baseline chatbot (`chatbot.py`), provider abstraction, single-call architecture |
| Phùng Hữu Uy | ReAct agent system prompt engineering, few-shot examples, test suite (`tests/test_model.py`) |

---

## 3. Telemetry & Performance Dashboard

Telemetry hooks are present in the agent flow, but this repository snapshot does not include a full benchmark export.

Data extracted from `logs/2026-06-01.log` across 20 test runs:

| Metric | Phi-3-mini (local) | Kimi-K2 (cloud) |
|--------|-------------------|-----------------|
| Average Latency (P50) | ~97,000ms | ~12,000ms |
| Max Latency (P99) | ~176,692ms | ~27,000ms |
| Avg Tokens per Task | ~1,200 tokens | ~400 tokens |
| Avg Steps to Complete | 5.8 steps | 2.6 steps |
| Success Rate | 14% (1/7) | 71% (5/7) |
| Total Cost (20 runs) | $0 (local hardware) | ~$0.004 (free tier) |

**Key observations from telemetry:**
- Phi-3-mini: latency dominated by CPU inference (~30s/step). High token count due to repetitive loop behavior.
- Kimi-K2: consistent 6-14s per step. Tokens efficient — model follows ReAct format cleanly.
- Chatbot (Phi-3): single call but 51-176s latency, frequent hallucination of room data not in DB.
- Chatbot (Kimi-K2): 3.5-8s latency, correctly asks for missing info instead of hallucinating.
---

## 4. Root Cause Analysis (RCA) - Failure Traces

The clearest failure mode we observed was malformed action formatting from the model.

### Case Study: Malformed Tool Arguments
- **Input**: "Tôi cần phòng cho 30 người, có máy chiếu."
- **Observation**: The model produced action strings such as `search_rooms(capacity: 30, amenities: ['projector'])`, which did not match strict Python keyword syntax.
- **Root Cause**: The initial parser only accepted `key=value` arguments, so colon-based syntax and loose `args:` payloads caused parsing failures.
- **Fix**: We relaxed the agent parser to normalize loose action formats and aligned the tools with the JSON dataset so the search path became grounded and executable.

### Case Study: Data Source Mismatch
- **Input**: A classroom recommendation prompt that should have matched the repository data.
- **Observation**: The first tool version used hardcoded mock classrooms instead of `data/classroom.json`.
- **Root Cause**: The implementation did not yet read the provided dataset, so the tool output could diverge from the repository source of truth.
- **Fix**: `search_rooms` now loads and normalizes `data/classroom.json` directly.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2
- **Diff**: Added stricter tool instructions, explicit argument examples, and clearer boundaries between chatbot and ReAct agent behavior.
- **Result**: Reduced malformed action parsing errors and improved the likelihood that the model emits valid tool calls.

### Experiment 2 (Bonus): Chatbot vs Agent
| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Simple Q | Produces a plausible recommendation from a single prompt | Produces a grounded recommendation after tool use | **Agent** |
| Multi-step | Cannot verify availability or rank rooms with evidence | Uses search, availability, and ranking tools | **Agent** |
| Ambiguous input | Hallucinate rooms or ask for clarification | Correctly asks for missing info before calling tools | **Tie** |
| Local model (Phi-3) | Responds in ~51-176s, frequent hallucination | Loops 6-8 steps, often hits max_steps | **Chatbot** |
| Cloud model (Kimi-K2) | Responds in ~4-8s, accurate for simple queries | Responds in ~12-27s, grounded in real data | **Agent** |

**Conclusion**: The agent consistently outperforms the chatbot for multi-step tasks requiring real data verification. For simple queries with a capable cloud model, the chatbot is faster and sufficient. With weak local models (Phi-3-mini), neither approach performs reliably — the chatbot at least returns *something* while the agent often loops.

---

## 6. Production Readiness Review

*Considerations for taking this system to a real-world environment.*

- **Security**: Sanitize tool inputs, reject unsupported argument shapes, and avoid executing arbitrary code from LLM output.
- **Guardrails**: Keep the 5-step loop cap, enforce timeouts, and return a structured failure when the model cannot converge.
- **Scaling**: Move to a more formal orchestration layer such as LangGraph if branching logic, retries, or multi-agent coordination becomes necessary.
- **Data Governance**: Treat `data/classroom.json` as the single source of truth for classroom metadata until a real datastore is introduced.

---