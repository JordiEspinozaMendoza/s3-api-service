from flask import Flask, jsonify, request
import os
import io
import sys
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/notify/v1/health")
def health_check():
    return jsonify({"status": "UP"})
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
