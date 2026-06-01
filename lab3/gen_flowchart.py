"""Script tạo flowchart.png cho Classroom Recommendation Agent."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(10, 16))
ax.set_xlim(0, 10)
ax.set_ylim(0, 16)
ax.axis("off")
fig.patch.set_facecolor("#F8F9FA")

# ── Helpers ──────────────────────────────────────────────────────────────────

def box(ax, x, y, w, h, text, color="#4A90D9", text_color="white",
        shape="round,pad=0.1", fontsize=10):
    fancy = FancyBboxPatch((x - w/2, y - h/2), w, h,
                           boxstyle=shape, linewidth=1.5,
                           edgecolor="#2C3E50", facecolor=color, zorder=3)
    ax.add_patch(fancy)
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
            color=text_color, fontweight="bold", zorder=4,
            wrap=True, multialignment="center")

def diamond(ax, x, y, w, h, text, color="#F39C12", text_color="white", fontsize=9):
    dx, dy = w/2, h/2
    pts = [[x, y+dy], [x+dx, y], [x, y-dy], [x-dx, y]]
    poly = plt.Polygon(pts, closed=True, facecolor=color,
                       edgecolor="#2C3E50", linewidth=1.5, zorder=3)
    ax.add_patch(poly)
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
            color=text_color, fontweight="bold", zorder=4, multialignment="center")

def arrow(ax, x1, y1, x2, y2, label="", color="#2C3E50"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.5), zorder=2)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx+0.15, my, label, fontsize=8, color=color, va="center")

# ── Nodes ─────────────────────────────────────────────────────────────────────

# 1. User Input
box(ax, 5, 15.2, 4, 0.7, "👤  User Input", color="#2980B9")

# 2. Requirement Extractor
box(ax, 5, 13.8, 4.5, 0.8,
    "Requirement Extractor\n(số người · thời gian · tiện ích)",
    color="#8E44AD", fontsize=9)

# 3. Diamond: đủ thông tin?
diamond(ax, 5, 12.4, 3.6, 0.9, "Đủ thông tin?", color="#E67E22")

# 4. Hỏi lại
box(ax, 8.5, 12.4, 2.2, 0.65, "Hỏi lại\nngười dùng", color="#E67E22", fontsize=9)

# 5. search_rooms
box(ax, 5, 10.9, 4.5, 0.8,
    "🔍  search_rooms\n(capacity, amenities)",
    color="#8E44AD", fontsize=9)

# 6. Diamond: tìm thấy?
diamond(ax, 5, 9.5, 3.2, 0.9, "Tìm thấy\nphòng?", color="#E67E22")

# 7. Không có phòng
box(ax, 8.5, 9.5, 2.2, 0.65, "Không có\nphòng phù hợp", color="#E74C3C", fontsize=9)

# 8. check_availability
box(ax, 5, 8.0, 4.5, 0.8,
    "✅  check_availability\n(room_id, time_slot)",
    color="#8E44AD", fontsize=9)

# 9. Diamond: còn trống?
diamond(ax, 5, 6.6, 3.2, 0.9, "Phòng\ncòn trống?", color="#E67E22")

# 10. Diamond: còn phòng khác?
diamond(ax, 8.5, 6.6, 2.8, 0.9, "Còn phòng\nkhác?", color="#E67E22", fontsize=8)

# 11. Tất cả đã đặt
box(ax, 8.5, 5.2, 2.2, 0.65, "Tất cả phòng\nđã bị đặt", color="#E74C3C", fontsize=9)

# 12. rank_rooms
box(ax, 5, 5.1, 4.5, 0.8,
    "🏆  rank_rooms\n(xếp hạng theo tiêu chí)",
    color="#8E44AD", fontsize=9)

# 13. Recommendation Agent
box(ax, 5, 3.6, 4.5, 0.8,
    "Recommendation Agent\n(tổng hợp kết quả)",
    color="#27AE60", fontsize=9)

# 14. Final Answer
box(ax, 5, 2.2, 4.5, 0.8,
    "💬  Final Answer\n(đề xuất phòng cho user)",
    color="#27AE60")

# ── Arrows ────────────────────────────────────────────────────────────────────

arrow(ax, 5, 14.85, 5, 14.2)           # User → Extractor
arrow(ax, 5, 13.4,  5, 12.85)          # Extractor → diamond đủ TT
arrow(ax, 6.8, 12.4, 7.4, 12.4, "Không")  # diamond → hỏi lại
arrow(ax, 5, 11.95, 5, 11.3, "Có")    # diamond → search_rooms
arrow(ax, 5, 10.5,  5, 9.95)           # search_rooms → diamond tìm thấy
arrow(ax, 6.6, 9.5, 7.4, 9.5, "Không")    # diamond → không có phòng
arrow(ax, 5, 9.05,  5, 8.4, "Có")     # diamond → check_availability
arrow(ax, 5, 7.6,   5, 7.05)           # check_avail → diamond còn trống
arrow(ax, 6.6, 6.6, 7.1, 6.6, "Không")    # diamond → còn phòng khác
arrow(ax, 8.5, 6.15, 8.5, 5.55)        # còn phòng khác → đã đặt (Không)
# "Có" từ còn phòng khác → quay lại check_availability
ax.annotate("", xy=(6.75, 8.0), xytext=(8.5, 7.05),
            arrowprops=dict(arrowstyle="-|>", color="#2C3E50", lw=1.5,
                            connectionstyle="arc3,rad=0.3"), zorder=2)
ax.text(8.0, 7.6, "Có", fontsize=8, color="#2C3E50")

arrow(ax, 5, 6.15,  5, 5.5, "Có")     # diamond → rank_rooms
arrow(ax, 5, 4.7,   5, 4.0)            # rank_rooms → agent
arrow(ax, 5, 3.2,   5, 2.6)            # agent → final answer

# Hỏi lại → quay lại User Input
ax.annotate("", xy=(5, 15.2), xytext=(8.5, 12.73),
            arrowprops=dict(arrowstyle="-|>", color="#E67E22", lw=1.5,
                            connectionstyle="arc3,rad=-0.4"), zorder=2)

# ── Title & Legend ────────────────────────────────────────────────────────────

ax.set_title("Classroom Recommendation Agent — Flowchart",
             fontsize=13, fontweight="bold", pad=10, color="#2C3E50")

legend_items = [
    mpatches.Patch(color="#2980B9", label="User"),
    mpatches.Patch(color="#8E44AD", label="Tool call"),
    mpatches.Patch(color="#E67E22", label="Decision"),
    mpatches.Patch(color="#27AE60", label="Output"),
    mpatches.Patch(color="#E74C3C", label="Error path"),
]
ax.legend(handles=legend_items, loc="lower left", fontsize=8,
          framealpha=0.9, title="Legend")

plt.tight_layout()
plt.savefig("lab3/flowchart.png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print("✅ Saved: lab3/flowchart.png")
