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

**Actual:** *(điền sau khi chạy)*

**Result:** *(PASS / FAIL)*

---

## Test Case 2 — Multi-constraint (nhiều điều kiện)

**Input:**
> "Tôi cần phòng cho 50 người, có máy chiếu và điều hòa, vào thứ 4 lúc 1 giờ chiều"

**Expected:**
- Agent gọi `search_rooms(50, ["projector", "ac"])` → B301, C204, D202
- Agent kiểm tra availability từng phòng với `"Wed 13:00"`
- Final Answer đề xuất phòng còn trống (B301 hoặc C204)

**Actual:** *(điền sau khi chạy)*

**Result:** *(PASS / FAIL)*

---

## Test Case 3 — Ambiguous Input (thiếu thông tin)

**Input:**
> "Tôi cần phòng học"

**Expected:**
- Agent nhận ra thiếu thông tin (số người, thời gian)
- Final Answer hỏi lại: "Bạn cần phòng cho bao nhiêu người? Vào thời gian nào?"
- Không gọi tool nào

**Actual:** *(điền sau khi chạy)*

**Result:** *(PASS / FAIL)*

---

## Test Case 4 — Edge Case (tất cả phòng phù hợp đã bị đặt)

**Input:**
> "Tôi cần phòng cho 70 người vào thứ 4 lúc 9 giờ sáng"

**Expected:**
- Agent gọi `search_rooms(70)` → chỉ có C204 (80 chỗ)
- Agent gọi `check_availability("C204", "Wed 09:00")` → `true` (C204 có slot Wed 09:00)
- Final Answer đề xuất C204

*(Nếu đổi time_slot sang "Wed 10:00" → C204 không có → Final Answer báo không có phòng trống)*

**Actual:** *(điền sau khi chạy)*

**Result:** *(PASS / FAIL)*

---

## Test Case 5 — Lab Computer Room

**Input:**
> "Nhóm tôi cần phòng lab máy tính cho 40 người vào thứ 3 lúc 9 giờ"

**Expected:**
- Agent gọi `search_rooms(40, ["lab"])` → B205, D202
- Agent kiểm tra `check_availability("B205", "Tue 09:00")` → `true`
- Final Answer đề xuất **B205**

**Actual:** *(điền sau khi chạy)*

**Result:** *(PASS / FAIL)*

---

## Tổng kết

| # | Loại | PASS/FAIL |
|---|------|-----------|
| 1 | Happy path | |
| 2 | Multi-constraint | |
| 3 | Ambiguous input | |
| 4 | Edge case (phòng đầy) | |
| 5 | Lab computer | |
