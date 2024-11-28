import cv2 as cv
import numpy as np
from sface import SFace
from yunet import YuNet
from fastapi import FastAPI, File, UploadFile
import  uvicorn
import base64
from utils import get_passport_info
from fastapi.responses import HTMLResponse

# Define backend and target
backend_id = cv.dnn.DNN_BACKEND_OPENCV
target_id = cv.dnn.DNN_TARGET_CPU

# Initialize the face recognizer
recognizer = SFace(modelPath="ai_models/face_recognition_sface_2021dec.onnx",
                   disType=1,
                   backendId=backend_id,
                   targetId=target_id)

# Initialize the face detector
detector = YuNet(modelPath='ai_models/face_detection_yunet_2023mar.onnx',
                 inputSize=[320, 320],
                 confThreshold=0.7,
                 nmsThreshold=0.3,
                 topK=5000,
                 backendId=backend_id,
                 targetId=target_id)

app = FastAPI(title="KYC Solution SpandsSPS",
              )

def detect_face(image):
    detector.setInputSize([image.shape[1], image.shape[0]])
    faces = detector.infer(image)
    if len(faces) > 1 or len(faces) == 0:
        return [], False
    return faces[0], True

def crop_face(image, face):
    x, y, w, h = face[:4].astype(int)
    cropped_face = image[y:y+h, x:x+w]
    _, buffer = cv.imencode('.jpg', cropped_face)
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    base64_uri = f"data:image/jpeg;base64,{jpg_as_text}"
    return base64_uri

def convert_byte_to_numpy(content):
    nparr = np.frombuffer(content, np.uint8)
    image = cv.imdecode(nparr, cv.IMREAD_COLOR)
    return image

def verify_faces(passport, profile):
    result = {}
    face1, is_face_in_passport = detect_face(passport)
    face2, is_face_in_profile = detect_face(profile)
    result['is_passport_has_valid_face'] = is_face_in_passport
    result['is_profile_has_valid_face'] = is_face_in_profile
    if is_face_in_passport and is_face_in_profile:
        _, result['matched'] = recognizer.match(passport, face1, profile, face2)
    else:
        result['matched'] = False
    return result


@app.post("/is_passport_valid")
async def is_passport_valid(passport_file : UploadFile = File(...)):
    content = await passport_file.read()
    nparr = np.frombuffer(content, np.uint8)
    passport = cv.imdecode(nparr, cv.IMREAD_COLOR)
    _, is_valid = detect_face(passport)
    return {"is_passport_has_valid_face": is_valid}

@app.post("/is_profile_valid")
async def is_profile_valid(profile_file : UploadFile = File(...)):
    content = await profile_file.read()
    nparr = np.frombuffer(content)
    profile = cv.imencode(nparr, cv.IMREAD_COLOR)
    _, is_valid = detect_face(profile)
    return {"is_profile_has_valid_face": is_valid}

@app.post("/verify_both_faces")
async def verify(passport_file : UploadFile = File(...), profile_file : UploadFile = File(...)):
    passport_content = await passport_file.read()
    profile_content = await profile_file.read()
    passport = convert_byte_to_numpy(content=passport_content)
    profile = convert_byte_to_numpy(content=profile_content)
    return verify_faces(passport, profile)

@app.post("/read_passport_info")
async def read_passport(passport_file : UploadFile = File(...)):
    content = await passport_file.read()
    passport_info = get_passport_info(passport=content)
    passport = convert_byte_to_numpy(content)
    face, is_face = detect_face(passport)
    if is_face:
        face_base64 = crop_face(passport, face)
        passport_info['is_face'] = is_face
        passport_info['base64_face'] = face_base64
    return passport_info

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def documentation():
    with open("README.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

if __name__=="__main__":
    uvicorn.run(app=app, host='127.0.0.1', port=8000)