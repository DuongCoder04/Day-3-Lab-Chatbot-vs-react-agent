# Chatbot Gợi Ý Phòng Học

## 1. Giới thiệu

Mục tiêu của dự án là xây dựng chatbot hỗ trợ sinh viên tìm kiếm và đề xuất phòng học phù hợp dựa trên sức chứa, thời gian sử dụng và các tiện ích cần thiết.

---

## 2. Kiến trúc hệ thống

User
→ Requirement Extractor
→ Room Search Tool
→ Availability Checker
→ Ranking Engine
→ Recommendation Agent

---

## 3. Thiết kế Agent

### Vai trò

Classroom Recommendation Agent

### Công cụ

* search_rooms()
* check_availability()
* rank_rooms()

### Quy tắc

* Không bịa dữ liệu
* Chỉ sử dụng dữ liệu từ tool
* Luôn kiểm tra tình trạng phòng trước khi đề xuất

---

## 4. Flowchart

(Chèn flowchart)

---

## 5. Test Cases

### Test 1

Input:
"Tôi cần phòng cho 30 người"

Expected:
"A301"

Result:
PASS

### Test 2

...

---

## 6. ReAct Trace

Thought
Action
Observation
Final

(Chèn trace mẫu)

---

## 7. Error Handling

* Database timeout
* Tool failure
* Missing information

---

## 8. Kết luận

Hệ thống đáp ứng yêu cầu tìm kiếm và đề xuất phòng học dựa trên nhu cầu người dùng, đồng thời hỗ trợ xử lý lỗi và các trường hợp đặc biệt.


## 9. Cấu trúc file khi nộp bài
lab3/
    chatbot.py              # System prompt + 1 LLM call
    agent.py                # ReAct loop + tools
    tools.py                # Tool definition (mock or real API)
    test_cases.md           # 5 test cases + expected vs actual
    trace.md                # 1 full trace Thought/Action/Obervation
    flowchart.png           # Luong xu ly agent
