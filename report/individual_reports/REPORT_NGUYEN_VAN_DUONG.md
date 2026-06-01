# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyen Van Duong — Docs & Flowchart
- **Student ID**: 2A202600967
- **Date**: June 1, 2026

---

## I. Technical Contribution (15 Points)

### Modules Implemented

| File | Mô tả |
|------|-------|
| `lab3/trace.md` | Full ReAct trace mẫu với phân tích từng bước |
| `lab3/flowchart.png` | Lưu đồ kiến trúc hệ thống (render bằng matplotlib) |
| `lab3/gen_flowchart.py` | Script Python tự động sinh `flowchart.png` |

### Code Highlights

**`gen_flowchart.py`** — tự động render flowchart từ code, không cần tool ngoài:

```python
# Vẽ node hình thoi cho decision point
def diamond(ax, x, y, w, h, text, color='#E67E22', fontsize=9):
    pts = [[x,y+h/2],[x+w/2,y],[x,y-h/2],[x-w/2,y]]
    poly = plt.Polygon(pts, closed=True, facecolor=color,
                       edgecolor='#2C3E50', lw=1.5, zorder=3)
    ax.add_patch(poly)
    ax.text(x, y, text, ha='center', va='center', ...)

plt.savefig('lab3/flowchart.png', dpi=150, bbox_inches='tight')
```

### Documentation

`trace.md` ghi lại toàn bộ vòng lặp Thought → Action → Observation của agent khi xử lý câu hỏi thực tế. File này phục vụ 2 mục đích:

1. **Minh họa** cách ReAct loop hoạt động cho người đọc chưa quen
2. **Debug reference** — so sánh trace mẫu với trace thực tế khi agent bị lỗi

`flowchart.png` thể hiện toàn bộ luồng xử lý từ User Input đến Final Answer, bao gồm các nhánh lỗi (phòng đầy, không tìm thấy phòng).

---

## II. Debugging Case Study (10 Points)

### Problem Description

Trong quá trình chạy thử, agent với model **Phi-3-mini-4k (local)** bị kẹt trong vòng lặp vô hạn — liên tục gọi `search_rooms` mà không chuyển sang `check_availability`:

```
Step 2: Action: search_rooms(capacity="30", amenities="thứ 2")
Step 3: Action: search_rooms(capacity="30", amenities="thứ 2")
Step 4: Action: search_rooms(capacity="30", amenities="thứ 2")
[LOOP DETECTED]
```

### Log Source

```json
{"timestamp": "2026-06-01T08:36:06", "event": "AGENT_STEP", "data": {"step": 4}}
{"timestamp": "2026-06-01T08:36:37", "event": "AGENT_STEP", "data": {"step": 5}}
{"timestamp": "2026-06-01T08:36:37", "event": "AGENT_NO_ACTION", "data": {
  "step": 5,
  "output": "Thought: Tôi cần tìm phòng có khoảng 3ran người..."
}}
```

### Diagnosis

Có 3 nguyên nhân kết hợp:

1. **Model quá nhỏ** — Phi-3-mini Q4 (2.2GB) không đủ khả năng reasoning để nhớ "đã làm bước này rồi". Mỗi lần generate, model chỉ thấy conversation history nhưng không thực sự "hiểu" trạng thái hiện tại.

2. **Observation không đủ rõ** — Kết quả `search_rooms` trả về danh sách dài, model không biết bước tiếp theo là gì vì system prompt không đủ directive.

3. **Amenity parsing sai** — Model truyền `amenities="thứ 2"` (ngày trong tuần) thay vì `amenities=[]`, khiến tool trả về kết quả không như mong đợi.

### Solution

Nhóm implement 3 cơ chế trong `agent.py`:

```python
# 1. Loop detection
if current_action == last_action:
    repeat_count += 1
    if repeat_count >= 2:
        # Buộc chuyển sang check_availability
        forced_tool, forced_args = self._get_forced_next_action(tool_name, tool_results)
        forced_obs = self._execute_tool(forced_tool, forced_args)
        conversation += f"Observation: {forced_obs}\n"

# 2. Hint injection — nhắc model bước tiếp theo
def _build_hint(self, tool_results, step):
    if "search_rooms" in tool_results and "check_availability" not in tool_results:
        return "[Hệ thống nhắc: Đã có danh sách phòng. Bước TIẾP THEO: check_availability(...)]"

# 3. Amenity mapping tiếng Việt → tiếng Anh
AMENITY_MAP = {
    "lab máy tính": "lab", "máy chiếu": "projector",
    "điều hòa": "ac", "micro": "mic", ...
}
```

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning — Thought block giúp gì?

`Thought` block buộc model phải **externalize reasoning** — viết ra suy luận trước khi hành động. Điều này tạo ra 2 lợi ích:

- **Traceability**: Developer có thể đọc Thought để hiểu tại sao agent chọn action đó, thay vì chỉ thấy output cuối
- **Grounding**: Khi model viết *"A101 đã bị đặt, thử A301"*, nó buộc phải dựa vào Observation thực tế thay vì generate từ prior knowledge

Chatbot không có bước này — nó trả lời trực tiếp từ training data, dễ hallucinate phòng không tồn tại.

### 2. Reliability — Khi nào Agent tệ hơn Chatbot?

| Tình huống | Chatbot | ReAct Agent |
|-----------|---------|-------------|
| Câu hỏi đơn giản ("Phòng nào lớn nhất?") | ✅ Nhanh, đủ dùng | ❌ Chậm hơn 5-10x |
| Model yếu (Phi-3 local) | ✅ Trả lời được | ❌ Dễ loop, hallucinate format |
| Không có time slot cụ thể | ✅ Gợi ý chung | ❌ Không biết check availability slot nào |
| Latency quan trọng | ✅ 1 LLM call | ❌ 3-8 LLM calls |

**Kết luận**: Agent chỉ vượt trội khi task cần **multi-step verification** với dữ liệu thực tế. Với câu hỏi đơn giản, chatbot đủ dùng và nhanh hơn nhiều.

### 3. Observation — Feedback ảnh hưởng thế nào?

Observation đóng vai trò **ground truth injection** — mỗi lần tool trả kết quả, model được "cập nhật" trạng thái thế giới thực. Ví dụ từ trace thực tế:

```
Action: check_availability("A101", "Mon 09:00")
Observation: Phòng A101 đã được đặt       ← model nhận thông tin mới
Thought: A101 bị đặt, thử A301            ← model điều chỉnh kế hoạch
Action: check_availability("A301", "Mon 09:00")
```

Nếu không có Observation (chatbot), model sẽ đoán A101 còn trống dựa trên prior — sai 50% trường hợp.

---

## IV. Future Improvements (5 Points)

### Scalability

Hiện tại agent xử lý tuần tự từng phòng. Với 10+ phòng, latency tăng tuyến tính. Cải thiện:

```python
# Parallel tool calls với asyncio
import asyncio

async def check_all_rooms(rooms, time_slot):
    tasks = [check_availability_async(r['id'], time_slot) for r in rooms]
    results = await asyncio.gather(*tasks)
    return dict(zip([r['id'] for r in rooms], results))
```

### Safety

Thêm **Hallucination Guard** đã implement — reject Final Answer nếu chứa room_id không có trong DB:

```python
def _clean_final_answer(self, text):
    valid_ids = {r["id"] for r in ROOMS_DB}
    mentioned = set(re.findall(r'\b([A-Z]\d{3})\b', text))
    if mentioned and not mentioned.issubset(valid_ids):
        return None  # trigger synthesize từ tool data thật
```

Mở rộng thêm: **Supervisor LLM** review Final Answer trước khi trả về user, kiểm tra consistency với Observation.

### Performance

- **Caching**: Cache kết quả `search_rooms` trong session — cùng capacity + amenities không cần gọi lại
- **Vector DB**: Khi số tool tăng lên 50+, dùng embedding để retrieve đúng tool thay vì liệt kê hết trong prompt
- **Streaming UI**: Đã implement SSE streaming trong `app.py` — user thấy từng step real-time thay vì chờ toàn bộ

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
