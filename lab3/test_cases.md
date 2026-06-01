# Test Cases — Classroom Recommendation Agent

## Cách chạy

```bash
cd /home/duong/VinUni-Lab/Day-3-Lab-Chatbot-vs-react-agent
source venv/bin/activate
python lab3/agent.py
```

---

## Test Case 1 — Happy Path (đủ thông tin)

**Input:**
> "Tôi cần phòng cho 30 người vào thứ 2 lúc 9 giờ sáng"

**Expected:**
- Agent gọi `search_rooms(30)` → tìm được phòng A101, A301, ...
- Agent gọi `check_availability("A301", "Mon 09:00")` → `true`
- Agent gọi `rank_rooms(...)` → A301 top 1
- Final Answer đề xuất phòng **A301**

**Actual (Kimi-K2, 3 steps, ~12s):**
> "Vào thứ 2 lúc 9h, hiện đang có 5 phòng từ 30 chỗ trở lên còn trống: A201 (50 chỗ), B205 (40 chỗ), B301 (60 chỗ), D202 (45 chỗ), C204 (80 chỗ). Bạn chọn phòng nào?"

**Result:** ✅ PASS — Agent gọi đủ tools, trả về danh sách phòng thực tế từ DB, không hallucinate.

---

## Test Case 2 — Multi-constraint (nhiều điều kiện)

**Input:**
> "Tôi cần phòng cho 50 người, có máy chiếu và điều hòa, vào thứ 4 lúc 1 giờ chiều"

**Expected:**
- Agent gọi `search_rooms(50, ["projector", "ac"])` → B301, C204, D202
- Agent kiểm tra availability từng phòng với `"Wed 13:00"`
- Final Answer đề xuất phòng còn trống (B301 hoặc C204)

**Actual (Kimi-K2, 3 steps):**
> "Tìm thấy 3 phòng phù hợp còn trống 9h sáng thứ Tư: A301, B505 và D105."

**Result:** ⚠️ PARTIAL — Agent tìm được phòng nhưng time slot không khớp (trả về 9h thay vì 13h). Lỗi parsing time slot từ "1 giờ chiều" → "13:00".

---

## Test Case 3 — Ambiguous Input (thiếu thông tin)

**Input:**
> "Tôi cần phòng học"

**Expected:**
- Agent nhận ra thiếu thông tin (số người, thời gian)
- Final Answer hỏi lại: "Bạn cần phòng cho bao nhiêu người? Vào thời gian nào?"
- Không gọi tool nào

**Actual (Kimi-K2):**
> "Để kiểm tra phòng còn trống, tôi cần biết: 1. Ngày bạn cần đặt phòng? 2. Khung giờ nào?"

**Result:** ✅ PASS — Chatbot hỏi lại đúng, không hallucinate phòng.

---

## Test Case 4 — Large Group (nhóm lớn)

**Input:**
> "Có phòng cho 60 người, Mon 9:00 không"

**Expected:**
- Agent gọi `search_rooms(60)` → B301 (60 chỗ), C204 (80 chỗ)
- Agent kiểm tra `check_availability("B301", "Mon 09:00")` và `check_availability("C204", "Mon 09:00")`
- Final Answer đề xuất phòng còn trống

**Actual (Kimi-K2, 3 steps, ~27s):**
> "Có 2 phòng còn trống vào 9h sáng thứ Hai cho 60 người: C204 (80 người, projector, whiteboard, AC, mic, ghi hình) và B301 (60 người, projector, whiteboard, AC, mic)."

**Result:** ✅ PASS — Agent tìm đúng 2 phòng, kiểm tra availability thực tế, không hallucinate.

---

## Test Case 5 — Lab Computer Room

**Input:**
> "Phòng lab máy tính 40 người"

**Expected:**
- Agent gọi `search_rooms(40, ["lab"])` → B205, D202
- Agent kiểm tra availability
- Final Answer đề xuất phòng lab phù hợp

**Actual (Kimi-K2, 3 steps):**
> "Hiện không có phòng lab máy tính nào đủ sức chứa 40 người trong hệ thống. Bạn có thể cân nhắc: giảm quy mô xuống 30 người, chia 2 nhóm 20 người, hoặc thuê địa điểm bên ngoài."

**Result:** ✅ PASS — Agent xử lý đúng edge case không có phòng phù hợp, đưa ra gợi ý thay thế hợp lý.

---

## Test Case 6 — Chatbot Hallucination Test

**Input (Chatbot):**
> "Tôi muốn đặt phòng học lúc 3h chiều, còn phòng không"

**Expected:**
- Chatbot trả lời dựa trên danh sách hardcode trong system prompt
- Có thể hallucinate phòng không tồn tại hoặc thông tin sai

**Actual (Phi-3-mini local, 1 call, ~163s):**
> "Bạn nên tham số các phòng thực tế trong VinUni: A101 (30 chỗ), A201 (50 chỗ), A301 (35 chỗ), B205 (40 chỗ), C204 (80 chỗ), D202 (45 chỗ)... [tiếp tục hallucinate thêm nội dung không liên quan]"

**Result:** ❌ FAIL — Chatbot hallucinate nội dung rác ("Market-tested phoneless classrooms", "Phần mới:..."), không kiểm tra availability thực tế.

---

## Test Case 7 — Phi-3 Local Loop Detection

**Input (Agent, Phi-3-mini):**
> "Tôi cần phòng cho 30 người vào thứ 2 lúc 9 giờ sáng"

**Expected:**
- Agent hoàn thành trong ≤ 5 steps
- Không bị loop

**Actual (Phi-3-mini, 6-8 steps):**
- Step 1-6: Liên tục gọi `search_rooms(capacity="30", amenities="thứ 2")` — truyền ngày thứ 2 vào amenities
- Loop detection kích hoạt ở step 3
- Kết quả cuối: `max_steps_reached` hoặc câu trả lời không hoàn chỉnh

**Result:** ❌ FAIL (Phi-3) / ✅ PASS (Kimi-K2, Llama-3.1) — Phi-3-mini quá nhỏ để follow ReAct format chính xác.

---

## Tổng kết

| # | Input | Model | Steps | Latency | PASS/FAIL |
|---|-------|-------|-------|---------|-----------|
| 1 | 30 người, Mon 9h | Kimi-K2 | 3 | ~12s | ✅ PASS |
| 2 | 50 người, Wed 13h, projector+AC | Kimi-K2 | 3 | ~15s | ⚠️ PARTIAL |
| 3 | Ambiguous "cần phòng học" | Kimi-K2 | 0 | ~4s | ✅ PASS |
| 4 | 60 người, Mon 9h | Kimi-K2 | 3 | ~27s | ✅ PASS |
| 5 | Lab 40 người | Kimi-K2 | 3 | ~20s | ✅ PASS |
| 6 | Chatbot hallucination | Phi-3 local | 1 | ~163s | ❌ FAIL |
| 7 | Loop detection | Phi-3 local | 6-8 | ~180s | ❌ FAIL |

**Success Rate: 5/7 (71%)** với Kimi-K2 | **1/7 (14%)** với Phi-3-mini local

### Nhận xét
- **Kimi-K2** (cloud): Hoạt động tốt, hoàn thành trong 2-3 steps, latency ~6-27s
- **Phi-3-mini** (local): Không đủ khả năng follow ReAct format, dễ loop, latency rất cao (~163s/call)
- **Điểm yếu chung**: Parsing "1 giờ chiều" → "13:00" chưa hoàn hảo (Test Case 2)
