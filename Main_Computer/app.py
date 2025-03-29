import os
import requests
import base64
from flask import Flask, render_template, request, jsonify
from io import BytesIO
from PIL import Image
import datetime
import io
import cv2

app = Flask(__name__)

SAVE_FOLDER = 'saved_images'
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

@app.route('/')
def home():
    # URL of the video to be linked to
    #video1_url = "https://images.pexels.com/photos/1036623/pexels-photo-1036623.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"
    video1_url = "http://10.42.0.137:5000"
    video2_url = "http://10.42.0.18:8000"
    video3_url = "http://10.42.0.137:8000"
    video4_url = "https://10.42.0.122:8000"
    return render_template('trial3.html', video1_url=video1_url,video2_url=video2_url
    ,video3_url=video3_url,video4_url=video4_url,)


@app.route('/save-frame', methods=['POST'])
def save_frame():
    try:
        data = request.get_json()
        image_data = data['image_data']

        header, encoded = image_data.split(',', maxsplit=1)
        binary_data = base64.b64decode(encoded)
        now = datetime.datetime.now()
        filename = f'saved_image_{now.strftime("%Y-%m-%d %H:%M:%S")}.jpg'
        filepath = os.path.join(SAVE_FOLDER, filename)

        with open(filepath, 'wb') as f:
            f.write(binary_data)

        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))



"""@app.route('/save-image', methods=['POST'])
def save_image():
    data = request.get_json()
    image_url = data.get('image_url')

    # Fetch the image using requests
    try:
        
        
        
        cap = cv2.VideoCapture(image_url)
            
        if not cap.isOpened():
                print("Error: Could not open video stream.")
                exit()

            # Capture one frame
        ret, frame = cap.read()
        if ret:
            time = datetime.datetime.now()                # Save the image with a unique name (could also use timestamp or other logic)
            image_filename = os.path.join(SAVE_FOLDER, f'saved_image_{time.strftime("%Y-%m-%d %H:%M:%S")}.jpg')

            cv2.imwrite(image_filename, frame)  # Save the frame if needed
            cap.release()
        else:
            print("Error: Could not read frame.")
            return jsonify(success=False, error="Failed to retrieve image.")
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))"""

if __name__ == '__main__':
    app.run(debug=True)

