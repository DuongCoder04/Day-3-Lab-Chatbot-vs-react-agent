"""
agent.py — ReAct Agent cho Classroom Recommendation
Vòng lặp: Thought → Action → Observation → Final Answer
"""

import os
import re
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from src.core.llm_provider import LLMProvider
from src.core.gemini_provider import GeminiProvider
from src.core.openai_provider import OpenAIProvider
from src.core.openrouter_provider import OpenRouterProvider
from src.core.local_provider import LocalProvider
from src.telemetry.logger import logger
from lab3.tools import search_rooms, check_availability, rank_rooms

load_dotenv()

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Bạn là agent đặt phòng học. Trả lời ngắn gọn bằng tiếng Việt.

Tools:
- search_rooms(capacity, amenities) → tìm phòng
- check_availability(room_id, time_slot) → kiểm tra trống (time_slot: "Mon 09:00")
- rank_rooms(rooms, criteria) → xếp hạng

Quy tắc: KHÔNG bịa dữ liệu. Chỉ dùng kết quả từ tool. Luôn check availability trước khi đề xuất.

Định dạng bắt buộc:
Thought: <suy luận>
Action: <tool_name>(<args>)
Observation: <do hệ thống điền>
Final Answer: <trả lời người dùng>"""

# ---------------------------------------------------------------------------
# ReAct Agent
# ---------------------------------------------------------------------------

class ClassroomReActAgent:
    def __init__(self, provider: LLMProvider, max_steps: int = 10,
                 on_step=None):
        self.provider = provider
        self.max_steps = max_steps
        self.on_step = on_step  # callback(text) để stream ra UI

    def _emit(self, text: str):
        """Gửi text ra UI (qua callback) hoặc terminal (print)."""
        if self.on_step:
            self.on_step(text)
        else:
            print(text)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, user_input: str) -> str:
        """
        Chạy vòng lặp ReAct cho đến khi có Final Answer hoặc hết max_steps.
        """
        logger.log_event("AGENT_START", {
            "input": user_input,
            "model": self.provider.model_name
        })

        conversation = f"User: {user_input}\n"
        steps = 0
        last_action = None        # phát hiện lặp
        repeat_count = 0          # đếm số lần lặp cùng action
        tool_results = {}         # lưu kết quả tool để inject hint

        while steps < self.max_steps:
            steps += 1
            logger.log_event("AGENT_STEP", {"step": steps})

            # Inject hint vào prompt nếu có kết quả tool trước đó
            hint = self._build_hint(tool_results, steps)
            prompt = conversation + hint if hint else conversation

            # 1. Gọi LLM
            llm_result = self.provider.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT
            )
            llm_output = llm_result["content"].strip()

            # Cắt nếu model tự thêm prompt mới vào output
            cutoff_markers = ["Phần mới:", "Lưu đọc", "User:", "<|system|>", "<|user|>",
                              "Written as", "research paper", "Note:", "---"]
            for marker in cutoff_markers:
                if marker in llm_output:
                    llm_output = llm_output[:llm_output.index(marker)].strip()

            # Cắt thêm: chỉ giữ đến hết dòng Action (bỏ text rác sau đó)
            lines = llm_output.split("\n")
            clean_lines = []
            for line in lines:
                clean_lines.append(line)
                # Dừng sau dòng Action để tránh text rác lẫn vào args
                if re.match(r"\s*Action\s*:", line, re.IGNORECASE):
                    break
            # Chỉ cắt nếu có Action (không cắt Final Answer)
            if any(re.match(r"\s*Action\s*:", l, re.IGNORECASE) for l in lines):
                if not any("Final Answer" in l for l in lines):
                    llm_output = "\n".join(clean_lines)

            conversation += llm_output + "\n"
            self._emit(f"\n--- Step {steps} ---\n{llm_output}")

            # 2. Kiểm tra Final Answer
            final = self._parse_final_answer(llm_output)
            if final:
                # Post-process: nếu vô nghĩa thì tự tổng hợp từ tool_results
                cleaned = self._clean_final_answer(final)
                if cleaned is None:
                    cleaned = self._synthesize_answer(tool_results)
                logger.log_event("AGENT_END", {"steps": steps, "result": cleaned})
                return cleaned

            # 3. Parse Action
            action = self._parse_action(llm_output)
            if not action:
                logger.log_event("AGENT_NO_ACTION", {"step": steps, "output": llm_output})
                break

            tool_name, tool_args_str = action
            current_action = f"{tool_name}({tool_args_str})"

            # 4. Loop detection — cùng action lặp >= 2 lần → inject hint mạnh hơn
            if current_action == last_action:
                repeat_count += 1
                if repeat_count >= 2:
                    # Thực thi forced action và thêm Observation thật
                    forced_tool, forced_args = self._get_forced_next_action(tool_name, tool_results)
                    if forced_tool:
                        forced_obs = self._execute_tool(forced_tool, forced_args)
                        tool_results[forced_tool] = {"args": forced_args, "result": forced_obs}
                        forced_line = (
                            f"\n[Hệ thống buộc chuyển bước]\n"
                            f"Thought: Đã có danh sách phòng, cần kiểm tra availability.\n"
                            f"Action: {forced_tool}({forced_args})\n"
                            f"Observation: {forced_obs}\n"
                        )
                        conversation += forced_line
                        self._emit(f"[LOOP DETECTED] Forced: {forced_tool}({forced_args})\nObservation: {forced_obs}")
                    repeat_count = 0
                    last_action = None
                    continue
            else:
                repeat_count = 0
                last_action = current_action

            # 5. Thực thi tool
            observation = self._execute_tool(tool_name, tool_args_str)

            # Lưu kết quả để dùng ở bước sau
            tool_results[tool_name] = {
                "args": tool_args_str,
                "result": observation
            }

            obs_line = f"Observation: {observation}\n"
            conversation += obs_line
            self._emit(obs_line)

        logger.log_event("AGENT_END", {"steps": steps, "result": "max_steps_reached"})
        return "Xin lỗi, tôi không thể hoàn thành yêu cầu trong số bước cho phép. Vui lòng thử lại với yêu cầu cụ thể hơn."

    # ------------------------------------------------------------------
    # Loop detection helpers
    # ------------------------------------------------------------------

    def _build_hint(self, tool_results: dict, step: int) -> str:
        """
        Tạo hint nhắc model dùng kết quả tool đã có thay vì gọi lại.
        Chỉ inject từ bước 2 trở đi.
        """
        if step < 2 or not tool_results:
            return ""

        hints = []

        # Đã có search_rooms nhưng chưa check_availability → nhắc mạnh
        if "search_rooms" in tool_results and "check_availability" not in tool_results:
            rooms_result = tool_results["search_rooms"]["result"]
            room_match = re.search(r'\b([A-Z]\d{3})\b', rooms_result)
            first_room = room_match.group(1) if room_match else "A301"
            hints.append(
                f"Đã có danh sách phòng. "
                f"Bước TIẾP THEO bắt buộc: check_availability(\"{first_room}\", \"Mon 09:00\")"
            )

        # Đã check_availability → nhắc đưa ra Final Answer
        elif "check_availability" in tool_results:
            avail_result = tool_results["check_availability"]["result"]
            hints.append(
                f"Đã kiểm tra: {avail_result}. "
                f"Bước TIẾP THEO: đưa ra Final Answer cho người dùng."
            )

        if hints:
            return "\n[Hệ thống nhắc: " + " | ".join(hints) + "]\n"
        return ""

    def _synthesize_answer(self, tool_results: dict) -> str:
        """Tự tổng hợp câu trả lời từ kết quả tool khi model sinh text vô nghĩa."""
        avail = tool_results.get("check_availability", {}).get("result", "")
        room_match = re.search(r'Phòng ([A-Z]\d{3}) còn trống lúc (.+?)\.', avail)
        if room_match:
            room_id = room_match.group(1)
            time_slot = room_match.group(2)
            # Lấy thông tin phòng từ search_rooms result
            search_result = tool_results.get("search_rooms", {}).get("result", "")
            info_match = re.search(rf'{room_id} \(sức chứa (\d+), tiện ích: ([^)]+)\)', search_result)
            if info_match:
                capacity = info_match.group(1)
                amenities = info_match.group(2)
                return (f"Tôi gợi ý phòng {room_id} (sức chứa {capacity} người, "
                        f"tiện ích: {amenities}). Phòng còn trống lúc {time_slot}.")
            return f"Tôi gợi ý phòng {room_id}. Phòng còn trống lúc {time_slot}."

        # Fallback: lấy phòng đầu tiên từ search
        search_result = tool_results.get("search_rooms", {}).get("result", "")
        room_match = re.search(r'([A-Z]\d{3}) \(sức chứa (\d+), tiện ích: ([^)]+)\)', search_result)
        if room_match:
            return (f"Tôi gợi ý phòng {room_match.group(1)} "
                    f"(sức chứa {room_match.group(2)} người, tiện ích: {room_match.group(3)}). "
                    f"Lưu ý: chưa xác nhận được lịch trống.")
        return "Xin lỗi, tôi không tìm được phòng phù hợp. Vui lòng thử lại."

    def _get_forced_next_action(self, stuck_tool: str, tool_results: dict):
        """Trả về (tool_name, args_str) cho bước tiếp theo khi bị loop."""
        if stuck_tool == "search_rooms" and "search_rooms" in tool_results:
            # Lấy room_id đầu tiên từ kết quả search
            rooms_result = tool_results["search_rooms"]["result"]
            room_match = re.search(r'\b([A-Z]\d{3})\b', rooms_result)
            first_room = room_match.group(1) if room_match else "A301"
            return "check_availability", f'"{first_room}", "Mon 09:00"'
        if stuck_tool == "check_availability" and "check_availability" in tool_results:
            return "rank_rooms", '{"capacity": 30}'
        return None, None

    def _clean_final_answer(self, text: str) -> str:
        """
        Hậu xử lý Final Answer:
        - Nếu text có nghĩa → giữ nguyên
        - Nếu quá ngắn hoặc vô nghĩa → tự tổng hợp từ tool_results
        """
        # Nếu quá ngắn hoặc không chứa tên phòng → coi là vô nghĩa
        has_room = bool(re.search(r'\b[A-Z]\d{3}\b', text))
        if len(text) < 20 or not has_room:
            return None  # caller sẽ tự tổng hợp
        return text

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_final_answer(self, text: str) -> Optional[str]:
        """Trích xuất nội dung sau 'Final Answer:', dừng trước Thought/Action tiếp theo."""
        match = re.search(r"Final Answer:\s*(.+?)(?:\nThought:|\nAction:|\Z)", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _parse_action(self, text: str) -> Optional[tuple]:
        """
        Trích xuất (tool_name, args_string) từ dòng 'Action: tool_name(args)'.
        Linh hoạt với output bị cắt hoặc có text rác sau args.
        """
        # Lấy dòng chứa Action:
        for line in text.split("\n"):
            line = line.strip()
            if not re.match(r"Action\s*:", line, re.IGNORECASE):
                continue

            # Match tool_name(args) — args có thể bị cắt ngang
            m = re.search(r"(\w+)\s*\(([^)]*)", line, re.IGNORECASE)
            if not m:
                continue

            tool_name = m.group(1).strip()
            args_raw  = m.group(2).strip()

            # Chỉ nhận tool hợp lệ
            if tool_name not in ("search_rooms", "check_availability", "rank_rooms"):
                continue

            # Cắt args nếu có text rác (chữ thường liên tục sau dấu phẩy/space)
            # Ví dụ: '"A101", "Mon 09:0 Written as...' → '"A101", "Mon 09:00"'
            args_clean = self._clean_args(tool_name, args_raw)
            return tool_name, args_clean

        return None

    def _clean_args(self, tool_name: str, args_raw: str) -> str:
        """Làm sạch args bị hallucinate, trả về args hợp lệ nhất có thể."""
        if tool_name == "check_availability":
            # Cần: "ROOM_ID", "Day HH:MM"
            # Lấy room_id
            room = re.search(r'"([A-Z]\d{3})"', args_raw)
            # Lấy time slot — Day HH:MM (chỉ lấy phần hợp lệ)
            time = re.search(r'"((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d{2}:\d{2})', args_raw)
            if room and time:
                return f'"{room.group(1)}", "{time.group(1)}"'
            if room:
                return f'"{room.group(1)}", "Mon 09:00"'  # fallback time
            return args_raw

        if tool_name == "search_rooms":
            # Cần: capacity (int), [amenities]
            num = re.search(r'\d+', args_raw)
            capacity = num.group() if num else "30"
            # Lấy list nếu có
            lst = re.search(r'\[.*?\]', args_raw)
            if lst:
                return f"{capacity}, {lst.group()}"
            return capacity

        return args_raw

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    def _execute_tool(self, tool_name: str, args_str: str) -> str:
        """
        Gọi tool tương ứng và trả về kết quả dạng string.
        """
        try:
            if tool_name == "search_rooms":
                capacity, amenities = self._parse_search_rooms_args(args_str)
                result = search_rooms(capacity=capacity, amenities=amenities)
                if not result:
                    return "Không tìm thấy phòng nào phù hợp."
                summary = [f"{r['id']} (sức chứa {r['capacity']}, tiện ích: {', '.join(r['amenities'])})" for r in result]
                return f"Tìm thấy {len(result)} phòng: " + " | ".join(summary)

            elif tool_name == "check_availability":
                room_id, time_slot = self._parse_check_availability_args(args_str)
                available = check_availability(room_id=room_id, time_slot=time_slot)
                if available:
                    return f"Phòng {room_id} còn trống lúc {time_slot}."
                else:
                    return f"Phòng {room_id} đã được đặt hoặc không tồn tại vào lúc {time_slot}."

            elif tool_name == "rank_rooms":
                rooms, criteria = self._parse_rank_rooms_args(args_str)
                result = rank_rooms(rooms=rooms, criteria=criteria)
                if not result:
                    return "Không có phòng nào để xếp hạng."
                top = result[:3]
                summary = [f"{r['id']} (score: {r['score']}, sức chứa: {r['capacity']})" for r in top]
                return "Top phòng: " + " | ".join(summary)

            else:
                return f"Tool '{tool_name}' không tồn tại."

        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return f"Lỗi khi gọi tool {tool_name}: {str(e)}"

    # ------------------------------------------------------------------
    # Argument parsers (đơn giản, đủ dùng cho mock)
    # ------------------------------------------------------------------

    def _parse_search_rooms_args(self, args_str: str):
        """Parse 'capacity, [amenities]' hoặc 'capacity'"""
        import ast
        parts = args_str.split(",", 1)
        capacity = int(re.search(r"\d+", parts[0]).group())
        amenities = []
        if len(parts) > 1:
            try:
                amenities = ast.literal_eval(parts[1].strip())
            except Exception:
                amenities = []
        return capacity, amenities

    def _parse_check_availability_args(self, args_str: str):
        """Parse '"A301", "Mon 09:00"' → ('A301', 'Mon 09:00')"""
        parts = re.findall(r'"([^"]+)"', args_str)
        if len(parts) >= 2:
            return parts[0], parts[1]
        # fallback: split by comma
        parts = [p.strip().strip("'\"") for p in args_str.split(",", 1)]
        return parts[0], parts[1] if len(parts) > 1 else ""

    def _parse_rank_rooms_args(self, args_str: str):
        """
        rank_rooms được gọi với rooms từ search_rooms trước đó.
        LLM thường truyền criteria dict, rooms lấy từ ROOMS_DB qua search.
        Fallback: trả về tất cả phòng với criteria từ args.
        """
        import ast
        from lab3.tools import ROOMS_DB
        try:
            # Thử parse criteria dict từ args
            dict_match = re.search(r"\{.*\}", args_str, re.DOTALL)
            criteria = ast.literal_eval(dict_match.group()) if dict_match else {}
        except Exception:
            criteria = {}

        # Lấy capacity từ criteria để filter rooms
        capacity = criteria.get("capacity", 1)
        rooms = search_rooms(capacity=capacity)
        return rooms, criteria


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_provider() -> LLMProvider:
    provider_name = os.getenv("DEFAULT_PROVIDER", "openrouter").lower()
    if provider_name == "openai":
        return OpenAIProvider(
            model_name=os.getenv("DEFAULT_MODEL", "gpt-4o"),
            api_key=os.getenv("OPENAI_API_KEY")
        )
    elif provider_name == "google":
        return GeminiProvider(
            model_name=os.getenv("DEFAULT_MODEL", "gemini-1.5-flash"),
            api_key=os.getenv("GEMINI_API_KEY")
        )
    elif provider_name == "openrouter":
        return OpenRouterProvider(
            model_name=os.getenv("OPENROUTER_MODEL", os.getenv("DEFAULT_MODEL", "meta-llama/llama-3.1-8b-instruct:free")),
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
    else:
        model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        return LocalProvider(model_path=model_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    provider = create_provider()
    agent = ClassroomReActAgent(provider=provider, max_steps=10)

    print("=== Classroom ReAct Agent ===")
    print("Gõ 'quit' để thoát.\n")

    while True:
        user_input = input("Bạn: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue

        answer = agent.run(user_input)
        print(f"\n✅ Kết quả: {answer}\n")
