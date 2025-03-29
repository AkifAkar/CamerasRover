#!/usr/bin/python3

from flask import Flask, Response, render_template, request, jsonify
from picamera2 import Picamera2
import time
import io
from PIL import Image
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480), "format":"RGB888"},controls={"ScalerCrop": (0, 0, 4608, 2592)},))
picam2.start()

def generate_frames():
    while True:
        image = picam2.capture_array()
        image = image[:, :, ::-1]


        # Encode to JPEG
        buffer = io.BytesIO()
        Image.fromarray(image).save(buffer, format="JPEG", quality=75)
        frame = buffer.getvalue()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        #time.sleep(0.05)  # Reduce CPU usage

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/change_resolution', methods=['POST'])
def save_image():
    data = request.get_json()
    resolution = data.get('resolution')
    try:
        picam2.stop()
        if resolution =="1080p":
            print(resolution)
            picam2.configure(picam2.create_video_configuration(main={"size": (1920, 1080), "format":"RGB888"},controls={"ScalerCrop": (0, 0, 4608, 2592)},))
        elif resolution == "720p":
            print(resolution)
            picam2.configure(picam2.create_video_configuration(main={"size": (1280, 720), "format":"RGB888"},controls={"ScalerCrop": (0, 0, 4608, 2592)},))
        elif resolution == "480p":
            print(resolution)
            picam2.configure(picam2.create_video_configuration(main={"size": (720, 480), "format":"RGB888"},controls={"ScalerCrop": (0, 0, 4608, 2592)},))
        else:
            return jsonify(success=False, error="resolution sent was not in correct format!!")
        picam2.start()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))

if __name__ == "__main__":
    app.run(host='10.42.0.137', port=5000)
