# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Quang Minh
- **Student ID**: 2A202600816
- **Date**: 1/6/2004

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: [e.g., `src/tools/search_tool.py`,'data/classroom.json']
- **Code Highlights**:if req_start >= avail_start and req_end <= avail_end:
                        room_info = f"{room_data['room']} ({room_data['building']})"
                        available_rooms.append(room_info)
- **Documentation**: [Brief explanation of how your code interacts with the ReAct loop]

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Agent liên tục báo "Kín lịch" dù cơ sở dữ liệu vẫn còn phòng trống, khiến nó bị kẹt trong vòng lặp (loop) liên tục gợi ý người dùng đổi giờ khác.
- **Log Source**: [ACTION INPUT]: {"time_slot": "08:00-12:00"}
[OBSERVATION]: Kín lịch: Không có phòng trống...
- **Diagnosis**: Lỗi định dạng chuỗi (String Parsing Error). Code Python cũ so sánh chuỗi cứng nhắc, nên khi LLM sinh ra tham số không có dấu cách (08:00-12:00), hệ thống hiểu sai là hai khung giờ khác nhau. Đây là điểm yếu điển hình của LLM khi phải tuân thủ format khắt khe.
- **Solution**: Thay vì ép LLM bằng Prompt (kém ổn định), tôi thiết kế lại logic code công cụ (Tool Design Evolution):

Dùng replace(" ", "") để xóa mọi khoảng trắng thừa.

Chuyển đổi "HH:MM" thành tổng số phút (Integer) để so sánh bằng toán học (req_start >= avail_start) thay vì so sánh chuỗi.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. Reasoning (Thought)
Chatbot thường: Trả lời theo bản năng dựa trên xác suất từ ngữ, dễ bịa thông tin (hallucinate) với câu hỏi khó.

ReAct Agent: Dùng Thought làm "giấy nháp" để suy luận từng bước, lên kế hoạch và chia nhỏ vấn đề trước khi hành động, giúp kết quả chính xác và logic hơn.

2. Reliability (Khi nào Agent tệ hơn Chatbot?)
Câu hỏi quá đơn giản: Agent hay làm phức tạp hóa vấn đề bằng cách dùng tool (ví dụ: tìm kiếm web cho câu hỏi "1+1 bằng mấy"), gây chậm trễ không cần thiết.

Kẹt vòng lặp (Infinite Loops): Nếu công cụ (tool/API) báo lỗi liên tục do Agent truyền sai cú pháp, nó rất dễ bị kẹt trong vòng lặp thử đi thử lại mà không thoát ra được.

Phụ thuộc ngoại cảnh: Nếu API hỏng hoặc rớt mạng, Agent sẽ tê liệt, trong khi Chatbot vẫn có thể trả lời dựa trên kiến thức sẵn có.

3. Observation (Tác động của Phản hồi)
Sửa sai thực tế: Observation ép Agent phải nhìn vào kết quả thật. Nếu tìm kiếm trả về "Không có kết quả", nó nhận ra mình phải đổi từ khóa thay vì tự bịa ra dữ liệu.

Làm điểm tựa: Agent không thể đưa ra đáp án cuối cùng cho đến khi nhận được dữ liệu xác thực từ môi trường.

## IV. Future Improvements (5 Points)

Để mở rộng hệ thống AI Agent này lên cấp độ production, cần tối ưu các mặt sau:

**Scalability**: Sử dụng hàng đợi bất đồng bộ (Asynchronous Queue - ví dụ: Kafka, RabbitMQ) để xử lý các tool call tốn thời gian. Kết hợp kiến trúc Stateless (phi trạng thái) để dễ dàng nhân bản (scale ngang) số lượng Agent khi lưu lượng người dùng tăng vọt.

**Safety** : Triển khai một 'Supervisor LLM' (Mô hình giám sát) độc lập để kiểm duyệt luồng Thought/Action trước khi thực thi. Áp dụng phân quyền (RBAC) chặt chẽ cho các công cụ (ví dụ: Agent chỉ được phép Đọc dữ liệu, cấm Xóa/Sửa) để chống lại các lỗ hổng như Prompt Injection.

**Performance**: Sử dụng Cơ sở dữ liệu Vector (Vector DB) để Agent có thể tìm kiếm và truy xuất (Retrieve) linh hoạt đúng tool cần dùng từ một thư viện hàng nghìn tool, thay vì nhồi nhét tất cả vào system prompt. Áp dụng thêm Semantic Caching (Bộ nhớ đệm ngữ nghĩa) để trả lời ngay lập tức các câu hỏi tương tự nhau mà không cần suy luận lại.
---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
