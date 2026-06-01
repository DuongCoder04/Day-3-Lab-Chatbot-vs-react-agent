# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: 42
- **Team Members**: 
    - Nguyễn Quang Minh - 2A202600816
    - Nguyễn Văn Dưỡng - 2A202600967
    - Phùng Hữu Uy - 2A202600886
    - Nguyễn Nhật Quang-2A202600813
    - Nguyễn Tuấn Dũng - 2A202600848
- **Deployment Date**: 01/06/2005

---

## 1. Executive Summary

This project builds a classroom recommendation system in two layers: a baseline chatbot and a ReAct agent.

- **Success Rate**: 75% on 20 test cases
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

---

## 3. Telemetry & Performance Dashboard

Telemetry hooks are present in the agent flow, but this repository snapshot does not include a full benchmark export.

- **Average Latency (P50)**: [e.g., 1200ms]
- **Max Latency (P99)**: [e.g., 4500ms]
- **Average Tokens per Task**: [e.g., 350 tokens]
- **Total Cost of Test Suite**: Effectively $0 for the local model path, excluding hardware cost.

Observed operational note: the local-provider path avoids API spend, while OpenAI/Gemini remain plug-compatible if the team wants cloud benchmarking later.
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

---

## 6. Production Readiness Review

*Considerations for taking this system to a real-world environment.*

- **Security**: Sanitize tool inputs, reject unsupported argument shapes, and avoid executing arbitrary code from LLM output.
- **Guardrails**: Keep the 5-step loop cap, enforce timeouts, and return a structured failure when the model cannot converge.
- **Scaling**: Move to a more formal orchestration layer such as LangGraph if branching logic, retries, or multi-agent coordination becomes necessary.
- **Data Governance**: Treat `data/classroom.json` as the single source of truth for classroom metadata until a real datastore is introduced.

---