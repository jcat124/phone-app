#!/usr/bin/env python3

# https://developers.google.com/web/fundamentals/media/capturing-images
# https://github.com/jhuckaby/webcamjs
# https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toBlob
# https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toDataURL
# https://developer.mozilla.org/en-US/docs/Web/API/FileReader/readAsDataURL

# https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Client-side_web_APIs/Fetching_data
# https://developer.mozilla.org/en-US/docs/Web/API/Body/blob

from flask import Flask, render_template_string, request, make_response
from scipy.spatial import distance
from imutils import face_utils
import imutils
import dlib
import cv2
import numpy as np
import datetime


def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear


thresh = 0.25
frame_check = 20
detect = dlib.get_frontal_face_detector()
# Dat file is the crux of the code
predict = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]
cap = cv2.VideoCapture(0)
flag = 0

app = Flask(__name__)


@app.route('/')
def index():
    return render_template_string('''
<table>
<tr>
    <td>VIDEO</td>
    <td>CANVAS</td>
    <td>SERVER</td>
    <td>SCREENSHOT (CANVAS)</td>
    <td>SCREENSHOT (SERVER)</td>
</tr>
<tr>
    <td>- assign camera (media device)<br>- play stream</td>
    <td>- draw video on context 2d,<br>- convert to jpg file (Blob)<br>- upload to server as POST</td>
    <td>- get jpg file (Blob) from server<br>- convert to BASE64 url<br>- assign to img</td>
    <td>- get canvas as BASE64 url<br>- assign to img</td>
    <td>- copy BASE64 url<br>- assign to img</td>
</tr>
<tr>
    <td><video  id="video"  swidth="{{ width }}" height="{{ height }}" autoplay style="background-color: grey"></video></td>
    <td><canvas id="canvas" width="{{ width }}" height="{{ height }}" style="background-color: grey"></canvas></td>
    <td><img id="server"     src="" width="{{ width }}" height="{{ height }}" style="background-color: grey" /></td>
    <td><img id="screenshot_canvas" src="" width="{{ width }}" height="{{ height }}" style="background-color: grey" /></td>
    <td><img id="screenshot_server" src="" width="{{ width }}" height="{{ height }}" style="background-color: grey" /></td>
</tr>
<tr>
    <td></td>
    <td></td>
    <td></td>
    <td><button id="send_canvas">Take Photo (from Canvas)</button></td>
    <td><button id="send_server">Take Photo (from Server)</button></td>
</tr>
</table>

<script>

// Element to take the snapshot
var video = document.getElementById('video');

// Element to display snapshot
    // you need canvas to get image - canvas can be hidden using `createElement("canvas")`

var canvas = document.getElementById('canvas');
var context = canvas.getContext('2d');

var server     = document.getElementById('server');

var screenshot_canvas = document.getElementById('screenshot_canvas');
var screenshot_server = document.getElementById('screenshot_server');

console.log("before get camera");
console.log(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);

// Get access to the camera!
if(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    // Not adding `{ audio: true }` since we only want video now
    navigator.mediaDevices.getUserMedia({ video: true, audio: true }).then(function(stream) {
        //video.src = window.URL.createObjectURL(stream);
        video.srcObject = stream;
        video.play();

        //console.log('setInterval')
        window.setInterval(function() {
            context.drawImage(video, 0, 0, {{ width }}, {{ height }}); // better use size because camera may gives data in different size then <video> is displaying
            canvas.toBlob(upload, "image/jpeg");
        }, 100);
    });
}

// Trigger to take photo from canvas

document.getElementById("send_canvas").addEventListener("click", function() {
    // copy frame from video to canvas as context 2d
    context.drawImage(video, 0, 0, {{ width }}, {{ height }}); // better use size because camera may gives data in different size then <video> is displaying
    
    // convert to BASE64 url and assign to <img> to display it
    screenshot_canvas.src = canvas.toDataURL();  
});

// Trigger to take photo from canvas

document.getElementById("send_server").addEventListener("click", function() {
    // convert to BASE64 url and assign to <img> to display it
    screenshot_server.src = server.src;  
});

// get image from canvas, send to server as POST, get result image, display image as IMG
function upload(file) {

    // create form and add file
    var formdata = new FormData();
    formdata.append("snap", file);

    // create AJAX connection
    fetch("{{ url_for('upload') }}", {
        method: 'POST',
        body: formdata,
        //headers: {"Content-type": "application/x-www-form-urlencoded; charset=UTF-8"}  // makes only problem
    }).then(function(response) {
        return response.blob();
    }).then(function(blob) {
        //console.log(blob);  // it slow down video from server
        server.src = URL.createObjectURL(blob);
    }).catch(function(err) {
        console.log('Fetch problem: ' + err.message);
    });
    
}

</script>
''', width=320, height=240)


def send_file_data(data, mimetype='image/jpeg', filename='output.jpg'):
    # https://stackoverflow.com/questions/11017466/flask-to-return-image-stored-in-database/11017839

    response = make_response(data)
    response.headers.set('Content-Type', mimetype)
    response.headers.set('Content-Disposition',
                         'attachment', filename=filename)

    return response


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # print(request.files)  # it slowdown video
        # print(request.data)   # it slowdown video
        # fs = request.files['snap'] # it raise error when there is no `snap` in form
        fs = request.files.get('snap')
        if fs:
            img = cv2.imdecode(np.frombuffer(
                fs.read(), np.uint8), cv2.IMREAD_UNCHANGED)
            # #print('FileStorage:', fs)
            while True:
                #ret, frame = cap.read()
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                subjects = detect(gray, 0)
                for subject in subjects:
                    shape = predict(gray, subject)
                    shape = face_utils.shape_to_np(
                        shape)  # converting to NumPy Array
                    leftEye = shape[lStart:lEnd]
                    rightEye = shape[rStart:rEnd]
                    leftEAR = eye_aspect_ratio(leftEye)
                    rightEAR = eye_aspect_ratio(rightEye)
                    ear = (leftEAR + rightEAR) / 2.0
                    leftEyeHull = cv2.convexHull(leftEye)
                    rightEyeHull = cv2.convexHull(rightEye)
                    cv2.drawContours(img, [leftEyeHull], -1, (0, 255, 0), 1)
                    cv2.drawContours(img, [rightEyeHull], -1, (0, 255, 0), 1)
                    if ear < thresh:
                        flag += 1
                        print(flag)
                        if flag >= frame_check:
                            cv2.putText(img, "ALERT! ALERT! ALERT! ALERT! ALERT!", (10, 30),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            cv2.putText(img, "ALERT! ALERT! ALERT! ALERT! ALERT!", (10, 325),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            #print ("Drowsy")
                    else:
                        flag = 0
                #cv2.imshow("Frame", frame)
                #key = cv2.waitKey(1) & 0xFF
                # if key == ord("q"):
                    break
            # cv2.destroyAllWindows()
            # img.release()
            # # https://stackoverflow.com/questions/27517688/can-an-uploaded-image-be-loaded-directly-by-cv2
            # # https://stackoverflow.com/a/11017839/1832058
            # height, width = img.shape[:2]
            # #print('Shape:', img.shape)
            # # rectangle(image, start_point, end_point, color, thickness)
            # img = cv2.rectangle(
            #     img, (20, 20), (width-20, height-20), (0, 0, 255), 2)

            # text = datetime.datetime.now().strftime('%Y.%m.%d %H.%M.%S.%f')
            # img = cv2.putText(img, text, (5, 15), cv2.FONT_HERSHEY_SIMPLEX,
            #                   0.5, (255, 255, 255), 1, cv2.LINE_AA)
            # #cv2.imshow('image', img)
            # # cv2.waitKey(1)

            # # https://jdhao.github.io/2019/07/06/python_opencv_pil_image_to_bytes/
            # ret, buf = cv2.imencode('.jpg', img)

            # return f'Got Snap! {img.shape}'
            return send_file_data(buf.tobytes())
        else:
            #print('You forgot Snap!')
            return 'You forgot Snap!'

    return 'Hello World!'


if __name__ == '__main__':
    # camera can work with HTTP only on 127.0.0.1
    # for 0.0.0.0 it needs HTTPS so it needs `ssl_context='adhoc'` (and in browser it need to accept untrusted HTTPS
    # app.run(host='127.0.0.1', port=5000)#, debug=True)
    app.run(debug=False)
