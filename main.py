from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import io
import sys
from dotenv import load_dotenv
import boto3

load_dotenv()

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route("/api/notify/v1/health")
def health_check():
    return jsonify({"status": "UP"})

@app.route("/api/image/", methods=["POST"])
def upload_image():
    try:
        file = request.files["file"]
        image = file.read()
        filename = file.filename
        
        s3_resource = boto3.resource("s3")
        bucket = s3_resource.Bucket(os.environ.get("BUCKET_NAME"))
        bucket.Object(filename).put(Body=file)

        return jsonify({'message': 'File uploaded successfully'})
        
    except Exception as e:
        error = str(e)

        print(e, sys.exc_info()[-1].tb_lineno)

        return jsonify(
            {"error": error, "status": "error"}
        )

    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
