#!/usr/bin/python3

import io
import logging
import socketserver
from http import server
from threading import Condition
import time
import json

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()
        return len(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle preflight requests for CORS"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/stream.mjpg')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                start_time = time.time()
                count = 0
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
                    #time.sleep(0.04)
                    count+=1
                    if (time.time() - start_time) > 4 :
                        print(time.time()-start_time)
                        print("FPS: ", count / (time.time() - start_time))
                        count = 0
                        start_time = time.time()
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()
    def do_POST(self):
        """Handles POST requests based on the path"""
        if self.path == "/change_resolution":
            self.change_resolution()
        elif self.path == "/change_fps":
            self.change_fps()
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def change_resolution(self):
        """Handles POST requests for /submit"""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")

        try:
            data = json.loads(post_data)
            print("Received on /cahnge_resolution:", data)
            resolution = data.get("resolution", str)
            picam2.stop_recording()
            
            if resolution =="1080p":
                self.resolution = (1920, 1080)
            elif resolution == "720p":
                self.resolution = (1280, 720)
            elif resolution == "480p":
                self.resolution = (720,480)
            picam2.configure(picam2.create_video_configuration(main={"size": self.resolution,},raw={"size":(4608, 2592)},controls={"ScalerCrop": (0, 0, 4608, 2592),"FrameDurationLimits": (int(1000000/self.fps),int(1000000/self.fps))},))
            picam2.start_recording(MJPEGEncoder(), FileOutput(output))
            response = {"message": f"Changing resolution to {resolution}"}
            self.send_response(200)
        except json.JSONDecodeError:
            response = {"error": "Invalid JSON"}
            self.send_response(400)

        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))
    def send_cors_headers(self):
        """Adds necessary CORS headers to allow cross-origin requests"""
        self.send_header("Access-Control-Allow-Origin", "*")  # Allow all origins (*)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")  # Allowed methods
        self.send_header("Access-Control-Allow-Headers", "Content-Type")  # Allowed headers

    def change_fps(self):
        """Handles POST requests for /upload"""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")

        try:
            data = json.loads(post_data)
            print("Received on /upload:", data)
            fpsValue = data.get("fpsValue", str)
            resolution = data.get("resolution", str)
            picam2.stop_recording()
            self.fps = int(fpsValue)
            if resolution =="1080p":
                self.resolution = (1920, 1080)
            elif resolution == "720p":
                self.resolution = (1280, 720)
            elif resolution == "480p":
                self.resolution = (720,480)
            print("geldi")
            picam2.configure(picam2.create_video_configuration(main={"size": self.resolution},raw={"size":(4608, 2592)},controls={"ScalerCrop": (0, 0, 4608, 2592),"FrameDurationLimits": (int(1000000/self.fps),int(1000000/self.fps))},))
            picam2.start_recording(MJPEGEncoder(), FileOutput(output))

            response = {"message": "Upload successful", "data": data}
            self.send_response(201)
        except json.JSONDecodeError:
            response = {"error": "Invalid JSON"}
            self.send_response(400)

        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# Initialize the camera
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (1920, 1080)}))

# Setup output
output = StreamingOutput()
picam2.start_recording(MJPEGEncoder(), FileOutput(output))
try:
    address = ('', 8000)  # Change port if needed
    server = StreamingServer(address, StreamingHandler)
    print(f"Server started at http://[YOUR_PI_IP]:8000")
    server.serve_forever()
finally:
    picam2.stop_recording()
