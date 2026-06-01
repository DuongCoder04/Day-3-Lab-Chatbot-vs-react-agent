import json
import os

def time_to_minutes(time_str: str) -> int:
    """Hàm phụ trợ: Chuyển đổi chuỗi HH:MM thành tổng số phút tính từ đầu ngày."""
    h, m = map(int, time_str.strip().split(':'))
    return h * 60 + m

def check_availability(day_of_week: str, time_slot: str, capacity: int) -> str:

    print(f"\n[Tool Execution] Gọi hàm Check_Availability(day_of_week='{day_of_week}', time_slot='{time_slot}', capacity={capacity})...")
    
    try:
        required_capacity = int(capacity)
    except ValueError:
        return "Lỗi: Tham số capacity phải là một con số nguyên."

    time_slot_clean = time_slot.replace(" ", "") # Biến "08:00 - 12:00" thành "08:00-12:00"
    try:
        req_start_str, req_end_str = time_slot_clean.split('-')
        req_start = time_to_minutes(req_start_str)
        req_end = time_to_minutes(req_end_str)
    except Exception:
        return "Lỗi: Khung giờ time_slot sai định dạng. Vui lòng dùng chuẩn HH:MM-HH:MM (vd: 08:00-10:00)."

    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "../../data/classroom.json")
    
    try:
        with open(db_path, 'r', encoding='utf-8') as file:
            rooms_db = json.load(file)
            if isinstance(rooms_db, dict):
                rooms_db = [rooms_db]
    except FileNotFoundError:
        return f"Lỗi hệ thống: Không tìm thấy DB tại {db_path}"
    except json.JSONDecodeError:
        return "Lỗi hệ thống: File classroom.json bị lỗi định dạng JSON."

    available_rooms = []
    
    #  Quét dữ liệu và so sánh khoảng thời gian
    for room_data in rooms_db:
        if room_data.get("capacity", 0) >= required_capacity:
            schedule = room_data.get("availability", {}).get(day_of_week, [])
            
            # Duyệt qua các khung giờ trống của phòng này
            for slot in schedule:
                slot_clean = slot.replace(" ", "")
                try:
                    avail_start_str, avail_end_str = slot_clean.split('-')
                    avail_start = time_to_minutes(avail_start_str)
                    avail_end = time_to_minutes(avail_end_str)
                    
                    if req_start >= avail_start and req_end <= avail_end:
                        room_info = f"{room_data['room']} ({room_data['building']})"
                        available_rooms.append(room_info)
                        break # Tìm thấy 1 khoảng thỏa mãn là đủ, dừng duyệt khung giờ khác
                except Exception:
                    continue # Bỏ qua nếu dữ liệu JSON có dòng bị lỗi định dạng giờ


    if available_rooms:
        return f"Tìm thấy các phòng trống phù hợp: {', '.join(available_rooms)}"
    else:
        return f"Kín lịch: Không có phòng trống nào chứa được {capacity} người vào khung giờ {time_slot} ngày {day_of_week}."

if __name__ == "__main__":
    # Ví dụ test nhanh
    print(check_availability("Monday", "08:00-12:00", 90))