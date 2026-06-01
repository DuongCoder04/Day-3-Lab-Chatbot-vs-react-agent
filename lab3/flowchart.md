# Flowchart — Classroom Recommendation Agent

Dùng file này để render ra `flowchart.png`.

**Cách render:**
- Online: paste vào [mermaid.live](https://mermaid.live) → Export PNG
- VS Code: cài extension "Markdown Preview Mermaid Support" → preview → screenshot

---

```mermaid
flowchart TD
    A([👤 User Input]) --> B[Requirement Extractor\nPhân tích yêu cầu:\nsố người, thời gian, tiện ích]

    B --> C{Đủ thông tin?}
    C -- Không --> D[/Hỏi lại người dùng/]
    D --> A

    C -- Có --> E[🔍 search_rooms\ncapacity, amenities]
    E --> F{Tìm thấy\nphòng?}

    F -- Không --> G[/Thông báo:\nKhông có phòng phù hợp/]

    F -- Có --> H[✅ check_availability\nroom_id, time_slot]
    H --> I{Phòng\ncòn trống?}

    I -- Không --> J{Còn phòng\nkhác?}
    J -- Có --> H
    J -- Không --> K[/Thông báo:\nTất cả phòng đã bị đặt/]

    I -- Có --> L[🏆 rank_rooms\nxếp hạng theo tiêu chí]
    L --> M[Recommendation Agent\nTổng hợp kết quả]
    M --> N([💬 Final Answer\nĐề xuất phòng cho user])

    style A fill:#4A90D9,color:#fff
    style N fill:#27AE60,color:#fff
    style D fill:#E67E22,color:#fff
    style G fill:#E74C3C,color:#fff
    style K fill:#E74C3C,color:#fff
    style E fill:#8E44AD,color:#fff
    style H fill:#8E44AD,color:#fff
    style L fill:#8E44AD,color:#fff
```
