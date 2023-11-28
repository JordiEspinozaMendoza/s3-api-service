from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS
import os
import io
import sys
from dotenv import load_dotenv
import boto3
import psycopg2
import json
import uuid

load_dotenv()

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")


def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_DATABASE"),
        user=os.environ.get("DB_USERNAME"),
        password=os.environ.get("DB_PASSWORD"),
    )

    return conn


@app.route("/api/notify/v1/health")
def health_check():
    return jsonify({"status": "UP"})


@app.route("/api/image/", methods=["POST"])
def upload_image():
    try:
        file = request.files["file"]
        socketId = request.form.get("socketId")
        image = file.read()
        filename = file.filename
        _id = uuid.uuid4().hex

        cur = get_db_connection().cursor()

        s3_resource = boto3.resource("s3")
        bucket = s3_resource.Bucket(os.environ.get("BUCKET_NAME"))
        response = bucket.Object(filename).put(
            Body=file, Metadata={"socketId": socketId}
        )

        # Create table images if not exists
        cur.execute("DROP TABLE IF EXISTS images;")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS images (id varchar PRIMARY KEY, filename varchar, socketId varchar, url varchar);"
        )

        # Insert image into table
        cur.execute(
            "INSERT INTO images (id, filename, socketId) VALUES (%s, %s, %s)",
            (_id, filename, socketId),
        )

        # Commit changes
        get_db_connection().commit()

        # Close connection
        cur.close()

        return jsonify({"message": "File uploaded successfully"})

    except Exception as e:
        error = str(e)

        print(e, sys.exc_info()[-1].tb_lineno)

        return jsonify({"error": error, "status": "error"})


@app.route("/api/image/", methods=["GET"])
def get_images():
    try:
        cur = get_db_connection().cursor()

        cur.execute("SELECT * FROM images;")
        images = cur.fetchall()

        cur.close()

        return jsonify({"images": images})

    except Exception as e:
        error = str(e)

        print(e, sys.exc_info()[-1].tb_lineno)

        return jsonify({"error": error, "status": "error"})


@app.route("/api/image/uploaded/", methods=["POST"])
def uploadedImage():
    object_key = request.json["object_key"]
    s3_resource = boto3.client("s3")

    response = s3_resource.get_object(
        Bucket=os.environ.get("BUCKET_NAME"), Key=object_key
    )
    ResponseMetadata = response["ResponseMetadata"]

    socketId = ResponseMetadata.get("HTTPHeaders").get("x-amz-meta-socketid")
    socketio.emit(
        "image_uploaded",
        {"object_key": object_key, "message": "File uploaded successfully"},
        to=socketId,
    )

    return jsonify({"message": "Message emmited succesfully"})


@socketio.on("file_uploaded")
def handleUpload(data):
    print(data)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
