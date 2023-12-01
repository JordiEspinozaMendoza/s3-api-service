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
from utils import file_generate_name

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
        filename = file_generate_name(filename)

        _id = uuid.uuid4().hex

        s3 = boto3.client("s3")

        response = s3.upload_fileobj(
            io.BytesIO(image),
            os.getenv("BUCKET_NAME"),
            filename,
            ExtraArgs={
                "ContentType": file.content_type,
                "Metadata": {"socketId": socketId},
            },
        )

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO images (id, filename, socketId) VALUES (%s, %s, %s)",
            (_id, filename, socketId),
        )

        # Commit changes
        conn.commit()

        # Close connection
        cur.close()
        conn.close()

        return jsonify({"message": "File uploaded successfully"})

    except Exception as e:
        error = str(e)

        print(e, sys.exc_info()[-1].tb_lineno)

        return jsonify({"error": error, "status": "error"})


@app.route("/api/image/", methods=["GET"])
def get_images():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM images;")
        images = cur.fetchall()

        cur.close()
        conn.close()

        images = [
            {
                "id": image[0],
                "filename": image[1],
                "socketId": image[2],
                "url": image[3],
            }
            for image in images
        ]

        return jsonify({"images": images})

    except Exception as e:
        error = str(e)

        print(e, sys.exc_info()[-1].tb_lineno)

        return jsonify({"error": error, "status": "error"})


@app.route("/api/image/uploaded/", methods=["POST"])
def uploadedImage():
    object_key = request.json["object_key"]
    s3_resource = boto3.client("s3")
    bucket = os.environ.get("BUCKET_NAME")
    response = s3_resource.get_object(Bucket=bucket, Key=object_key)
    ResponseMetadata = response["ResponseMetadata"]
    url = f"https://{bucket}.s3.amazonaws.com/{object_key}"

    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "UPDATE images SET url = %s WHERE filename = %s",
        (url, object_key),
    )

    conn.commit()

    cur.close()
    conn.close()

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
