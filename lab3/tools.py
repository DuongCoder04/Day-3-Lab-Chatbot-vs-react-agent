"""
tools.py — Mock tools cho Classroom Recommendation Agent
Dữ liệu hardcode, không kết nối database thật.
"""

from typing import List, Dict, Any, Optional

# ---------------------------------------------------------------------------
# Mock database
# ---------------------------------------------------------------------------

ROOMS_DB: List[Dict[str, Any]] = [
    {"id": "A101", "building": "A", "capacity": 30,  "amenities": ["projector", "whiteboard"], "available_slots": ["Mon 08:00", "Mon 10:00", "Tue 14:00"]},
    {"id": "A201", "building": "A", "capacity": 50,  "amenities": ["projector", "whiteboard", "ac"], "available_slots": ["Mon 09:00", "Wed 13:00", "Fri 08:00"]},
    {"id": "A301", "building": "A", "capacity": 35,  "amenities": ["projector", "whiteboard", "ac"], "available_slots": ["Mon 09:00", "Tue 11:00", "Thu 15:00"]},
    {"id": "B101", "building": "B", "capacity": 20,  "amenities": ["whiteboard"], "available_slots": ["Mon 08:00", "Mon 14:00", "Wed 10:00"]},
    {"id": "B205", "building": "B", "capacity": 40,  "amenities": ["projector", "whiteboard", "ac", "lab"], "available_slots": ["Tue 09:00", "Thu 13:00"]},
    {"id": "B301", "building": "B", "capacity": 60,  "amenities": ["projector", "whiteboard", "ac", "mic"], "available_slots": ["Mon 09:00", "Wed 15:00", "Fri 10:00"]},
    {"id": "C102", "building": "C", "capacity": 25,  "amenities": ["whiteboard", "ac"], "available_slots": ["Tue 08:00", "Thu 09:00", "Fri 14:00"]},
    {"id": "C204", "building": "C", "capacity": 80,  "amenities": ["projector", "whiteboard", "ac", "mic", "recording"], "available_slots": ["Wed 09:00", "Fri 13:00"]},
    {"id": "D101", "building": "D", "capacity": 15,  "amenities": ["whiteboard"], "available_slots": ["Mon 10:00", "Tue 10:00", "Wed 10:00", "Thu 10:00", "Fri 10:00"]},
    {"id": "D202", "building": "D", "capacity": 45,  "amenities": ["projector", "whiteboard", "ac", "lab"], "available_slots": ["Mon 13:00", "Tue 15:00", "Thu 08:00"]},
]


# ---------------------------------------------------------------------------
# Tool 1: search_rooms
# ---------------------------------------------------------------------------

def search_rooms(capacity: int, amenities: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Tìm các phòng có sức chứa >= capacity và đủ tiện ích yêu cầu.

    Args:
        capacity:   Số người tối thiểu cần chứa.
        amenities:  Danh sách tiện ích cần có (vd: ["projector", "ac"]).
                    Nếu None hoặc [], bỏ qua điều kiện tiện ích.

    Returns:
        Danh sách các phòng phù hợp (list of dict).
        Mỗi dict gồm: id, building, capacity, amenities, available_slots.
        Trả về [] nếu không tìm thấy.
    """
    if amenities is None:
        amenities = []

    results = []
    for room in ROOMS_DB:
        if room["capacity"] < capacity:
            continue
        if amenities and not all(a in room["amenities"] for a in amenities):
            continue
        results.append(room)

    return results


# ---------------------------------------------------------------------------
# Tool 2: check_availability
# ---------------------------------------------------------------------------

def check_availability(room_id: str, time_slot: str) -> bool:
    """
    Kiểm tra phòng có trống vào khung giờ cho trước không.

    Args:
        room_id:    Mã phòng (vd: "A301").
        time_slot:  Khung giờ theo định dạng "Day HH:MM" (vd: "Mon 09:00").

    Returns:
        True nếu phòng còn trống, False nếu đã bị đặt hoặc không tồn tại.
    """
    for room in ROOMS_DB:
        if room["id"] == room_id:
            return time_slot in room["available_slots"]
    return False  # Phòng không tồn tại


# ---------------------------------------------------------------------------
# Tool 3: rank_rooms
# ---------------------------------------------------------------------------

def rank_rooms(rooms: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Xếp hạng danh sách phòng theo tiêu chí, trả về danh sách đã sắp xếp.

    Args:
        rooms:    Danh sách phòng (output từ search_rooms).
        criteria: Dict chứa các tiêu chí ưu tiên:
                  - "capacity"  (int): Số người thực tế cần → ưu tiên phòng vừa đủ
                  - "amenities" (list): Tiện ích mong muốn → thưởng điểm nếu có thêm
                  - "building"  (str): Tòa nhà ưu tiên (optional)

    Returns:
        Danh sách phòng đã sắp xếp theo score giảm dần.
        Mỗi dict có thêm trường "score" (float 0.0 - 1.0).
    """
    if not rooms:
        return []

    needed_capacity = criteria.get("capacity", 0)
    wanted_amenities = criteria.get("amenities", [])
    preferred_building = criteria.get("building", None)

    scored = []
    for room in rooms:
        score = 0.0

        # Điểm sức chứa: phòng vừa đủ được điểm cao hơn phòng quá rộng
        if needed_capacity > 0:
            ratio = needed_capacity / room["capacity"]  # 1.0 = vừa khít
            capacity_score = max(0.0, 1.0 - abs(1.0 - ratio))
            score += capacity_score * 0.5  # trọng số 50%

        # Điểm tiện ích: mỗi tiện ích thêm được +0.1 (tối đa 0.3)
        if wanted_amenities:
            extra = [a for a in room["amenities"] if a not in wanted_amenities]
            amenity_score = min(len(extra) * 0.1, 0.3)
            score += amenity_score

        # Điểm tòa nhà ưu tiên
        if preferred_building and room["building"] == preferred_building:
            score += 0.2

        # Điểm số slot trống: nhiều slot → linh hoạt hơn
        slot_score = min(len(room["available_slots"]) * 0.05, 0.2)
        score += slot_score

        scored.append({**room, "score": round(score, 3)})

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored
