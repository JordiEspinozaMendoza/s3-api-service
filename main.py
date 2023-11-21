from flask import Flask, jsonify, request
import os
import io
import sys
from dotenv import load_dotenv
import boto3

load_dotenv()

app = Flask(__name__)

@app.route("/notify/v1/health")
def health_check():
    return jsonify({"status": "UP"})
    
@app.route("/api/image/", methods=["POST"])
def upload_image():
    try:
        image = request.files["file"].read()
        return jsonify(
            {
                "status": "success",
            }
        )
    except Exception as e:
        error = str(e)

        print(e, sys.exc_info()[-1].tb_lineno)

        return jsonify(
            {"error": error, "status": "error"}
        )

    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
