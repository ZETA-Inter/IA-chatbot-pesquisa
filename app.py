from flask import Flask, request, jsonify
from programs_agent import programs_agent as run_programs_agent
from search_agent import search_agent as run_search_agent
import os

app = Flask(__name__)

# Example agent functions (replace with your actual logic)
def programs_agent_response(prompt: str) -> str:
    return run_programs_agent(prompt)

def search_agent_response(prompt: str) -> str:
    return run_search_agent(prompt)

# Endpoint for Agent 1
@app.route('/programs_agent', methods=['POST'])
def programs_agent():
    data = request.get_json()
    prompt = data.get("prompt", "")
    response = programs_agent_response(prompt)
    return {"agent": "programs_agent", "response": response}

# Endpoint for Agent 2
@app.route('/search_agent', methods=['POST'])
def search_agent():
    data = request.get_json()
    prompt = data.get("prompt", "")
    response = search_agent_response(prompt)
    return {"agent": "search_agent", "response": response}

if __name__ == '__main__':
    # Get the port from the environment variable, default to 5000 if not set
    port = int(os.environ.get("PORT", 5000))
    # Run the app, binding to all public interfaces and using the specified port
    app.run(host="0.0.0.0", port=port)
