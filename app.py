"""
app.py — Flask web server cho Classroom Recommendation Chatbot
Chạy: venv/bin/python app.py
Mở:  http://localhost:5000
"""

import os
import sys
import threading
import queue
import json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from flask import Flask, render_template, request, Response, stream_with_context
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from lab3.chatbot import ClassroomChatbot, create_provider as create_chatbot_provider
from lab3.agent import ClassroomReActAgent, create_provider as create_agent_provider
from src.core.openrouter_provider import OpenRouterProvider

app = Flask(__name__, template_folder="templates", static_folder="static")

# ── Khởi tạo providers (lazy, chỉ load 1 lần) ────────────────────────────────
_chatbot = None
_agent   = None
_lock    = threading.Lock()

def get_chatbot():
    global _chatbot
    if _chatbot is None:
        with _lock:
            if _chatbot is None:
                _chatbot = ClassroomChatbot(create_chatbot_provider())
    return _chatbot

def get_agent():
    global _agent
    if _agent is None:
        with _lock:
            if _agent is None:
                _agent = ClassroomReActAgent(create_agent_provider(), max_steps=10)
    return _agent

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/favicon.ico")
def favicon():
    return "", 204

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Chatbot endpoint — trả về 1 response."""
    data = request.get_json()
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return {"error": "Empty message"}, 400

    try:
        response = get_chatbot().chat(user_msg)
        return {"response": response, "mode": "chatbot"}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/agent", methods=["POST"])
def agent():
    """Agent endpoint — streaming SSE để hiển thị từng step."""
    data = request.get_json()
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return {"error": "Empty message"}, 400

    def generate():
        q = queue.Queue()
        def run_agent():
            def on_step(text):
                q.put(json.dumps({"type": "step", "content": text}, ensure_ascii=False))

            # Tạo agent mới mỗi request với callback
            from lab3.agent import ClassroomReActAgent
            ag = ClassroomReActAgent(
                provider=create_agent_provider(),
                max_steps=10,
                on_step=on_step
            )
            try:
                result = ag.run(user_msg)
                q.put(json.dumps({"type": "final", "content": result}, ensure_ascii=False))
            except Exception as e:
                q.put(json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False))
            finally:
                q.put(None)

        t = threading.Thread(target=run_agent, daemon=True)
        t.start()

        while True:
            try:
                item = q.get(timeout=120)  # 2 phút timeout
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'error', 'content': 'Timeout'})}\n\n"
                break
            if item is None:
                break
            yield f"data: {item}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )

if __name__ == "__main__":
    print("🚀 Starting Classroom Chatbot UI...")
    print("📌 Open: http://localhost:5000")
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
