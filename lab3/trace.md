# ReAct Trace Mẫu — Classroom Recommendation Agent

## Kịch bản

**User input:** "Tôi cần phòng cho 30 người vào thứ 2 lúc 9 giờ sáng, cần có máy chiếu"

---

## Full Trace

```
User: Tôi cần phòng cho 30 người vào thứ 2 lúc 9 giờ sáng, cần có máy chiếu

Thought: Người dùng cần phòng cho 30 người, có máy chiếu, vào thứ 2 lúc 9:00.
         Trước tiên tôi cần tìm các phòng đáp ứng sức chứa và tiện ích.

Action: search_rooms(30, ["projector"])

Observation: Tìm thấy 7 phòng: A101 (sức chứa 30, tiện ích: projector, whiteboard) |
             A201 (sức chứa 50, tiện ích: projector, whiteboard, ac) |
             A301 (sức chứa 35, tiện ích: projector, whiteboard, ac) |
             B205 (sức chứa 40, tiện ích: projector, whiteboard, ac, lab) |
             B301 (sức chứa 60, tiện ích: projector, whiteboard, ac, mic) |
             C204 (sức chứa 80, tiện ích: projector, whiteboard, ac, mic, recording) |
             D202 (sức chứa 45, tiện ích: projector, whiteboard, ac, lab)

Thought: Có 7 phòng phù hợp. Tôi nên ưu tiên phòng có sức chứa vừa đủ (30-40 người).
         Các ứng viên tốt nhất: A101 (30), A301 (35), B205 (40).
         Cần kiểm tra phòng A101 trước vì sức chứa vừa khít nhất.

Action: check_availability("A101", "Mon 09:00")

Observation: Phòng A101 đã được đặt hoặc không tồn tại vào lúc Mon 09:00.

Thought: A101 đã bị đặt. Thử kiểm tra A301 — sức chứa 35, có AC thêm.

Action: check_availability("A301", "Mon 09:00")

Observation: Phòng A301 còn trống lúc Mon 09:00.

Thought: A301 còn trống và đáp ứng đủ yêu cầu (35 chỗ, có projector, AC).
         Tôi sẽ xếp hạng để xác nhận đây là lựa chọn tốt nhất.

Action: rank_rooms(rooms, {"capacity": 30, "amenities": ["projector"]})

Observation: Top phòng: A301 (score: 0.85, sức chứa: 35) |
             B205 (score: 0.72, sức chứa: 40) |
             A201 (score: 0.65, sức chứa: 50)

Final Answer: Tôi gợi ý phòng **A301** (tòa A, sức chứa 35 người).
              Phòng có đầy đủ máy chiếu, bảng trắng và điều hòa.
              Phòng còn trống vào thứ 2 lúc 9:00 sáng. Chúc bạn học tốt!
```

---

## Phân tích Trace

| Bước | Loại | Mô tả |
|------|------|-------|
| 1 | Thought | Xác định yêu cầu: 30 người, projector, Mon 09:00 |
| 2 | Action | `search_rooms` → lọc theo capacity + amenity |
| 3 | Observation | 7 phòng phù hợp |
| 4 | Thought | Ưu tiên phòng vừa đủ, chọn A101 kiểm tra trước |
| 5 | Action | `check_availability("A101", "Mon 09:00")` |
| 6 | Observation | A101 đã bị đặt |
| 7 | Thought | Thử A301 |
| 8 | Action | `check_availability("A301", "Mon 09:00")` |
| 9 | Observation | A301 còn trống |
| 10 | Thought | Xếp hạng để xác nhận |
| 11 | Action | `rank_rooms(...)` |
| 12 | Observation | A301 score cao nhất |
| 13 | Final Answer | Đề xuất A301 với đầy đủ thông tin |

**Tổng số bước:** 4 (trong giới hạn max_steps = 6) ✅

---

## So sánh: Chatbot vs ReAct Agent

| Tiêu chí | Chatbot (`chatbot.py`) | ReAct Agent (`agent.py`) |
|----------|----------------------|--------------------------|
| Số LLM call | 1 | 4 (trong trace này) |
| Kiểm tra availability | ❌ Không | ✅ Có |
| Dữ liệu chính xác | ❌ Có thể hallucinate | ✅ Từ tool thực tế |
| Xử lý multi-step | ❌ Không | ✅ Có |
| Latency | Thấp | Cao hơn |
| Độ tin cậy | Thấp | Cao |
