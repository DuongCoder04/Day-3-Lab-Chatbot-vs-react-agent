# Kế Hoạch Nhóm — Lab 3: Chatbot Gợi Ý Phòng Học

## Tổng quan

Xây dựng hệ thống **ReAct Agent** hỗ trợ sinh viên tìm kiếm và đề xuất phòng học phù hợp dựa trên sức chứa, thời gian và tiện ích.

**Output cần nộp:**
```
lab3/
    chatbot.py        # System prompt + 1 LLM call
    agent.py          # ReAct loop + tools
    tools.py          # Tool definitions (mock)
    test_cases.md     # 5 test cases + expected vs actual
    trace.md          # 1 full ReAct trace
    flowchart.png     # Lưu đồ xử lý agent
```

---

## Phân công công việc

### 👤 Người 1 — Tools Engineer → `tools.py`

**Ưu tiên: Làm trước tiên** (cả team phụ thuộc vào file này)

Implement 3 mock tools:

```python
search_rooms(capacity: int, amenities: list) -> list[dict]
check_availability(room_id: str, time_slot: str) -> bool
rank_rooms(rooms: list, criteria: dict) -> list[dict]
```

Yêu cầu:
- Dữ liệu mock đủ đa dạng (ít nhất 10 phòng)
- Mỗi phòng có: `id`, `capacity`, `amenities`, `building`
- Có docstring mô tả rõ input/output
- Không kết nối database thật, dùng dữ liệu hardcode

---

### 👤 Người 2 — Chatbot Developer → `chatbot.py`

Xây dựng chatbot đơn giản (baseline, **không dùng ReAct**):

- Thiết kế system prompt cho Classroom Recommendation Agent
- Chỉ 1 LLM call duy nhất
- Nhận input từ user, trả về gợi ý phòng
- Mục đích: so sánh với agent để thấy hạn chế của chatbot thuần

Yêu cầu:
- Dùng provider từ `src/core/` có sẵn trong project
- Ghi chú rõ điểm yếu của approach này trong comment

---

### 👤 Người 3 — Agent Developer → `agent.py`

Implement **ReAct loop** hoàn chỉnh:

- Vòng lặp: `Thought → Action → Observation` (tối đa 5 bước)
- Parse output LLM để xác định tool cần gọi
- Gọi đúng tool từ `tools.py`
- Dừng khi gặp `Final Answer`
- Xử lý lỗi: tool không tồn tại, thiếu thông tin, timeout

Format LLM output cần parse:
```
Thought: ...
Action: tool_name(args)
Observation: ...
Final Answer: ...
```

---

### 👤 Người 4 — QA / Test Engineer → `test_cases.md`

Viết **5 test cases** đa dạng và chạy thực tế:

| # | Loại | Input mẫu |
|---|------|-----------|
| 1 | Happy path | "Tôi cần phòng cho 30 người lúc 9h sáng" |
| 2 | Multi-constraint | "Cần phòng 50 người, có máy chiếu, buổi chiều" |
| 3 | Ambiguous input | "Tôi cần phòng học" (thiếu thông tin) |
| 4 | Edge case | Tất cả phòng phù hợp đều đã bị đặt |
| 5 | Error case | Thời gian sai định dạng |

Với mỗi test case ghi rõ: `Input` / `Expected` / `Actual` / `PASS/FAIL`

---

### 👤 Người 5 — Docs & Flowchart → `trace.md` + `flowchart.png`

**Phần 1 — `trace.md`:** Ghi lại 1 full ReAct trace mẫu

```
User: "Tôi cần phòng cho 30 người lúc 9h sáng thứ 2"

Thought: Người dùng cần phòng sức chứa 30 người vào 9h sáng.
         Tôi cần tìm các phòng phù hợp trước.
Action: search_rooms(capacity=30, amenities=[])
Observation: [{"id": "A301", "capacity": 35}, {"id": "B205", "capacity": 40}]

Thought: Có 2 phòng phù hợp. Cần kiểm tra phòng A301 còn trống không.
Action: check_availability(room_id="A301", time_slot="Mon 09:00")
Observation: true

Thought: A301 còn trống. Xếp hạng để chọn phòng tốt nhất.
Action: rank_rooms(rooms=[...], criteria={"capacity_fit": true})
Observation: [{"id": "A301", "score": 0.95}, ...]

Final Answer: Tôi gợi ý phòng A301 (sức chứa 35 người, còn trống lúc 9h sáng thứ 2).
```

**Phần 2 — `flowchart.png`:** Vẽ lưu đồ kiến trúc hệ thống

Gợi ý dùng: [draw.io](https://draw.io) hoặc Mermaid

```
User Input
    ↓
Requirement Extractor
    ↓
ReAct Agent Loop ──────────────────────┐
    ↓                                  │
search_rooms() → check_availability() → rank_rooms()
    ↓
Final Answer → User
```

---

## Timeline

```
Buổi chiều — Cả 5 người làm song song:

  [0:00 - 0:30] Người 1: Hoàn thiện tools.py → share cho cả nhóm
                Người 2, 3, 4, 5: Đọc Problem.md, setup môi trường

  [0:30 - 2:00] Người 1: Hỗ trợ team, review code, bổ sung mock data
                Người 2: Code chatbot.py
                Người 3: Code agent.py
                Người 4: Viết draft test_cases.md (expected output)
                Người 5: Vẽ flowchart.png + viết draft trace.md

  [2:00 - 2:30] Người 4: Chạy test thực tế, cập nhật Actual + PASS/FAIL
                Người 5: Cập nhật trace.md từ output agent thực tế

  [2:30 - 3:00] Cả nhóm: Review chéo, fix bug, hoàn thiện docs, nộp bài
```

---

## Dependency Map

```
tools.py (P1)  ← làm trước
    ├── chatbot.py (P2)
    ├── agent.py (P3)
    └── test_cases.md (P4)  ← cần agent.py chạy được
         └── trace.md (P5)  ← lấy output từ agent chạy thực tế
```

---

## Lưu ý chung

- Dùng `venv` đã có sẵn: `source venv/bin/activate`
- Không commit API key lên git (đã có `.gitignore`)
- Nếu không có API key, dùng **local provider** (Phi-3 đã có trong `models/`)
- Mọi tool phải trả về dữ liệu **mock** — không bịa trong LLM response
