from flask import Flask, request, jsonify
from programs_pipeline import run_programs as run_programs_agent
from search_pipeline import run_search as run_search_agent
import os
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)


def programs_agent_response(prompt: str, session_id: str = None) -> str:
    return run_programs_agent(prompt, session_id)


def search_agent_response(prompt: str, session_id: str = None) -> str:
    return run_search_agent(prompt, session_id)


@app.route('/programs_agent', methods=['POST'])
def programs_agent():
    data = request.get_json()
    prompt = data.get("prompt", "")
    session_id = data.get("session", "")
    if not session_id:
        response = programs_agent_response(prompt=prompt)
    else:
        response = programs_agent_response(
            prompt=prompt, session_id=session_id)

    return jsonify({"agent": "programs_agent", "response": str(response)})


@app.route('/search_agent', methods=['POST'])
def search_agent():
    data = request.get_json()
    prompt = data.get("prompt", "")
    session_id = data.get("session", "")
    if not session_id:
        response = search_agent_response(prompt=prompt)
    else:
        response = search_agent_response(prompt=prompt, session_id=session_id)

    return jsonify({"agent": "search_agent", "response": str(response)})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
