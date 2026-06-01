# Individual Report: Lab 3 - Chatbot vs ReAct Agent

* **Student Name**: Phùng Hữu Uy
* **Student ID**: 2A202600886
* **Date**: 01/06/2026

---

# I. Technical Contribution (15 Points)

Trong bài lab này, tôi phụ trách xây dựng và triển khai phần **ReAct Agent**.

Các công việc chính tôi thực hiện bao gồm:

* Thiết kế luồng hoạt động của agent theo mô hình **Thought → Action → Observation → Final Answer**.
* Xây dựng system prompt để agent có thể suy luận từng bước trước khi đưa ra câu trả lời.
* Tích hợp các tool cần thiết để agent có thể thực hiện hành động thay vì chỉ trả lời như chatbot thông thường.
* Kiểm tra và điều chỉnh prompt nhằm giảm lỗi hallucination và tăng tính chính xác của kết quả.
* Thực hiện testing với nhiều tình huống khác nhau để đánh giá khả năng reasoning của agent.

Thông qua quá trình này, tôi hiểu rõ hơn cách một AI Agent đưa ra quyết định và sử dụng công cụ để hoàn thành nhiệm vụ phức tạp.

---

# II. Debugging Case Study (10 Points)

### Vấn đề gặp phải

Trong quá trình phát triển, agent thường gặp lỗi:

* Không gọi tool khi cần thiết.
* Trả lời trực tiếp thay vì thực hiện reasoning theo quy trình ReAct.
* Một số trường hợp lặp lại vòng suy luận nhiều lần trước khi đưa ra kết quả cuối cùng.

### Nguyên nhân

Sau khi kiểm tra prompt và log thực thi, tôi nhận thấy:

* System prompt chưa mô tả rõ khi nào agent phải gọi tool.
* Định dạng output giữa các bước Thought, Action và Observation chưa được chuẩn hóa.

### Cách khắc phục

Tôi đã:

1. Bổ sung hướng dẫn chi tiết trong system prompt.
2. Chuẩn hóa format đầu ra của từng bước.
3. Thêm các ví dụ mẫu (few-shot examples) để agent học cách thực hiện reasoning đúng quy trình.

### Kết quả

Sau khi chỉnh sửa, agent hoạt động ổn định hơn, tỷ lệ gọi tool chính xác tăng lên và số lần lặp reasoning không cần thiết giảm đáng kể.

---

# III. Personal Insights: Chatbot vs ReAct Agent (10 Points)

Sau khi thực hiện bài lab, tôi nhận thấy sự khác biệt chính giữa Chatbot và ReAct Agent như sau:

### Chatbot

* Trả lời dựa trên kiến thức có sẵn trong mô hình.
* Tốc độ phản hồi nhanh.
* Dễ triển khai.
* Phù hợp với các câu hỏi đơn giản hoặc mang tính hội thoại.

### ReAct Agent

* Có khả năng suy luận từng bước trước khi đưa ra câu trả lời.
* Có thể sử dụng các công cụ bên ngoài để tìm kiếm hoặc xử lý thông tin.
* Thích hợp với các bài toán nhiều bước và yêu cầu độ chính xác cao hơn.
* Dễ mở rộng thành các hệ thống AI Agent thực tế.

Theo tôi, ReAct Agent mạnh hơn chatbot truyền thống vì không chỉ "biết" mà còn có thể "hành động". Tuy nhiên, việc thiết kế prompt và quản lý tool cũng phức tạp hơn đáng kể.

---

# IV. Future Improvements (5 Points)

Trong tương lai, tôi muốn cải thiện hệ thống bằng cách:

* Bổ sung thêm nhiều tool để agent có thể xử lý đa dạng nhiệm vụ hơn.
* Tối ưu prompt nhằm giảm số bước reasoning không cần thiết.
* Thêm cơ chế memory để agent ghi nhớ ngữ cảnh giữa các cuộc hội thoại.
* Cải thiện khả năng xử lý lỗi và fallback khi tool không phản hồi.
* Đánh giá hiệu năng trên nhiều bộ dữ liệu và tình huống thực tế hơn.

---

## Conclusion

Thông qua Lab 3, tôi đã hiểu rõ hơn sự khác biệt giữa Chatbot và ReAct Agent. Việc trực tiếp xây dựng agent giúp tôi nắm được quy trình reasoning, tool calling và cách thiết kế hệ thống AI Agent trong thực tế. Đây là một trải nghiệm hữu ích giúp tôi hiểu sâu hơn về AI Engineering và các ứng dụng của Agentic AI.
