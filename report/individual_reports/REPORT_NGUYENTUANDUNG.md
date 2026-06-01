# Individual Report: Lab 3 - Chatbot vs ReAct Agent

* **Student Name**: Nguyễn Tuấn Dũng
* **Student ID**: 2A202600848
* **Date**: 01/06/2026

---

## I. Technical Contribution (15 Points)

My primary responsibility in the project was developing the baseline chatbot system (`chatbot.py`) used as a comparison benchmark against the ReAct Agent.

### Modules Implemented

#### `chatbot.py`

* Designed the system prompt for the Classroom Recommendation Chatbot.
* Implemented the single-call chatbot workflow.
* Integrated the chatbot with the provider abstraction in `src/core/`.
* Added documentation and comments explaining the limitations of a non-agentic approach.

### Code Highlights

The chatbot was intentionally designed as a simple baseline system that performs exactly one LLM call per user request.

#### Provider Abstraction

The chatbot supports multiple LLM providers through the shared provider interface:

```python
def build_provider() -> LLMProvider:
    provider_name = os.getenv("DEFAULT_PROVIDER", "local").strip().lower()

    if provider_name == "openai":
        ...
    if provider_name == "gemini":
        ...
    return LocalProvider(model_path=model_path)
```

This design allows the same chatbot implementation to run on Local Phi-3, OpenAI, or Gemini without modifying the application logic.

#### Single-Call Architecture

The core chatbot workflow consists of a single inference request:

```python
def generate_response(provider: LLMProvider, user_prompt: str) -> str:
    result = provider.generate(
        prompt=user_prompt,
        system_prompt=SYSTEM_PROMPT
    )

    return result.get("content", "").strip()
```

Unlike the ReAct Agent, the chatbot does not execute tools, maintain a reasoning trace, or perform multiple reasoning steps.

#### Prompt Engineering

A dedicated system prompt was created to explicitly communicate the chatbot's limitations:

```python
SYSTEM_PROMPT = """
Important limitations:
- You cannot verify availability.
- You cannot search actual rooms.
- You cannot execute tools or query external systems.
"""
```

This helps reduce unsupported claims and encourages the model to express uncertainty when appropriate.

### Documentation

The chatbot does not directly interact with the ReAct loop. Instead, it serves as a baseline system used to compare against the ReAct Agent.

#### Chatbot Workflow

```text
User Request
      ↓
System Prompt
      ↓
Single LLM Call
      ↓
Final Answer
```

#### ReAct Agent Workflow

```text
User Request
      ↓
Thought
      ↓
Action
      ↓
Observation
      ↓
Thought
      ↓
Action
      ↓
Observation
      ↓
Final Answer
```

Unlike the ReAct Agent, the chatbot cannot access:

* `search_rooms`
* `check_availability`
* `rank_rooms`

As a result, all recommendations are generated purely from the model's internal reasoning and prompt instructions. The chatbot serves as a baseline to evaluate the benefits of tool-augmented reasoning.

---

## II. Debugging Case Study (10 Points)

### Problem Description

During testing, the chatbot occasionally generated recommendations that appeared reasonable but could not be verified against the classroom dataset.

Example input:

> "Tôi cần phòng học cho 40 người có máy chiếu vào chiều thứ Hai."

The chatbot sometimes suggested rooms without considering actual room availability or the contents of `data/classroom.json`.

### Log Source

Observed during manual comparison testing between:

* `chatbot.py`
* `agent.py`

using the team's shared evaluation test cases.

### Diagnosis

The issue was not caused by parsing errors or tool failures.

The root cause was the chatbot architecture itself:

* The chatbot performs only one LLM call.
* It cannot access external classroom data.
* It cannot verify room availability.
* It cannot perform multi-step reasoning.

Therefore, the model relied entirely on probabilistic text generation and occasionally produced recommendations unsupported by the dataset.

### Solution

Since this behavior is an inherent limitation of a pure chatbot, no direct fix was implemented.

Instead, the ReAct Agent architecture was introduced to:

1. Search classrooms from the dataset.
2. Check room availability.
3. Rank suitable candidates.
4. Generate recommendations grounded in actual data.

This comparison became one of the key motivations for adopting the agent-based approach.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning

The `Thought` block significantly improves the reasoning process.

In the chatbot architecture, the model directly generates an answer without exposing intermediate reasoning steps.

In contrast, the ReAct Agent explicitly breaks the task into smaller steps:

* Search matching rooms.
* Check availability.
* Compare candidate rooms.
* Produce a final recommendation.

This decomposition allows the agent to solve more complex classroom requests more reliably.

### 2. Reliability

The Agent does not always outperform the chatbot.

For simple requests such as:

> "Gợi ý phòng học cho 20 người."

the chatbot is often faster and can provide a reasonable answer immediately with a single LLM call.

The Agent may perform worse when:

* Tool calls fail.
* Tool outputs are malformed.
* The model generates invalid actions.
* Additional reasoning steps increase latency.

However, for requests involving availability checks, ranking, or multiple constraints, the Agent consistently provides more grounded and reliable answers.

### 3. Observation

The Observation step is the most important difference between the two systems.

Example:

```text
Thought: Need rooms with projector.

Action:
search_rooms(capacity=30, amenities=["projector"])

Observation:
Room A
Room B
Room C
```

The Observation provides external evidence that influences the next reasoning step.

Without observations, the chatbot cannot update its reasoning based on real-world information. This makes it more prone to hallucination and unsupported assumptions.

---

## IV. Future Improvements (5 Points)

### Scalability

* Replace the JSON dataset with a database-backed service.
* Support asynchronous tool execution.
* Add caching for frequently requested classroom searches.
* Deploy the system behind an API gateway to support concurrent users.

### Safety

* Validate user constraints before processing.
* Reject malformed tool arguments.
* Add guardrails for unsupported classroom requests.
* Introduce a supervisor model to audit agent actions and outputs.

### Performance

* Use a vector database for semantic classroom retrieval.
* Optimize prompt size and tool descriptions.
* Cache frequent retrieval results.
* Improve ranking efficiency for larger classroom inventories.

### Additional Improvement

A hybrid architecture could be used in production:

* Use the chatbot path for simple classroom recommendation requests.
* Automatically switch to the ReAct Agent for complex multi-step tasks involving room search, availability checking, and ranking.

This approach would balance response speed and answer reliability while minimizing computational cost.
