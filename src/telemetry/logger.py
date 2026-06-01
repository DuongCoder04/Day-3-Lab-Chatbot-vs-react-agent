import logging
import json
import os
from datetime import datetime
from typing import Any, Dict

# ANSI color codes
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_CYAN   = "\033[36m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_RED    = "\033[31m"
_BLUE   = "\033[34m"
_MAGENTA = "\033[35m"

# Màu theo event type
EVENT_COLORS = {
    "CHATBOT_REQUEST":  _CYAN,
    "CHATBOT_RESPONSE": _GREEN,
    "AGENT_START":      _BLUE,
    "AGENT_STEP":       _YELLOW,
    "AGENT_END":        _GREEN,
    "AGENT_NO_ACTION":  _YELLOW,
    "ERROR":            _RED,
}

# Các field cần hiển thị nổi bật theo event
EVENT_HIGHLIGHTS = {
    "CHATBOT_REQUEST":  ["input", "model"],
    "CHATBOT_RESPONSE": ["output", "latency_ms"],
    "AGENT_START":      ["input", "model"],
    "AGENT_STEP":       ["step"],
    "AGENT_END":        ["steps", "result"],
}


class PrettyConsoleFormatter(logging.Formatter):
    """Format đẹp cho terminal, JSON cho file."""

    def __init__(self, pretty: bool = True):
        super().__init__()
        self.pretty = pretty

    def format(self, record: logging.LogRecord) -> str:
        if not self.pretty:
            return record.getMessage()

        try:
            payload = json.loads(record.getMessage())
        except (json.JSONDecodeError, TypeError):
            return f"{_DIM}{record.getMessage()}{_RESET}"

        event = payload.get("event", "INFO")
        data  = payload.get("data", {})
        ts    = payload.get("timestamp", "")[:19].replace("T", " ")  # "2026-06-01 08:22:18"

        color = EVENT_COLORS.get(event, _RESET)
        highlights = EVENT_HIGHLIGHTS.get(event, list(data.keys()))

        # Header
        lines = [f"{color}{_BOLD}[{event}]{_RESET} {_DIM}{ts}{_RESET}"]

        # Các field quan trọng
        for key in highlights:
            if key not in data:
                continue
            value = data[key]
            # Cắt output dài — chỉ cắt trong console, file log giữ nguyên
            if isinstance(value, str) and len(value) > 300:
                value = value[:300] + "..."
            lines.append(f"  {_BOLD}{key}{_RESET}: {value}")

        # Các field còn lại (mờ hơn)
        extra_keys = [k for k in data if k not in highlights]
        if extra_keys:
            extras = ", ".join(f"{k}={data[k]}" for k in extra_keys)
            lines.append(f"  {_DIM}{extras}{_RESET}")

        return "\n".join(lines)


class IndustryLogger:
    """
    Structured logger:
    - Console: format đẹp có màu
    - File: JSON thuần để parse sau
    """
    def __init__(self, name: str = "AI-Lab-Agent", log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Tránh add handler trùng khi import nhiều lần
        if self.logger.handlers:
            return

        os.makedirs(log_dir, exist_ok=True)

        # File handler — JSON thuần
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(PrettyConsoleFormatter(pretty=False))

        # Console handler — đẹp có màu
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(PrettyConsoleFormatter(pretty=True))

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_event(self, event_type: str, data: Dict[str, Any]):
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": data
        }
        self.logger.info(json.dumps(payload, ensure_ascii=False))

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str, exc_info=True):
        self.logger.error(msg, exc_info=exc_info)


# Global logger instance
logger = IndustryLogger()
