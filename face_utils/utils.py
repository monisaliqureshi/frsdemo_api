import base64
from PIL import Image
import cv2
import numpy as np
import  io
import face_recognition as fr
import math
from config.db import conn
from model.index import users
import json
import uuid

def face_distance_to_conf(face_distance, face_match_threshold=0.6):
    """
    * This function is used for convert face distance to confidance value
    * It gets face distace and face match threshold (by default: 0.6)
    * Convert face distance to confidance value
    * Return confidance value
    """
    if face_distance > face_match_threshold:
        range = (1.0 - face_match_threshold)
        linear_val = (1.0 - face_distance) / (range * 2.0)
        return round(linear_val, 4)
    else:
        range = face_match_threshold
        linear_val = 1.0 - (face_distance / (range * 2.0))
        return round(linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2)), 4)

def stringToRGB(base64_string):
    """
    * This function is used for converting base64 string to RGB image
    * It gets base64 string as argument
    * Decode it into image data
    * Convert Image data to Image
    * Convert Image to RGB and return it
    """
    imgdata = base64.b64decode(str(base64_string))
    image = Image.open(io.BytesIO(imgdata))
    return cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)

def is_exist(encoding):

    all_enrolled = conn.execute(users.select()).fetchall()
    encodings = list()
    face_id = list()
    for user in all_enrolled:
        face_id.append(user[0])
        encodings.append(np.array(json.loads(user[3])))

    distance = fr.face_distance(encodings, encoding)
    matches = fr.compare_faces(encodings, encoding)
    try:
        best_match_index = np.argmin(distance)
        val = face_distance_to_conf(distance[best_match_index]) * 100
        if matches[best_match_index]:
            return True, face_id[best_match_index], val
        else:
            return False, "Unknown", val
    except:
        return False, "Unknown", ""

def numpy2String(face_image):
    face_image = cv2.resize(face_image, (200, 200))
    # file_name = save_img(face_image)
    base64_img_str = cv2.imencode('.jpg', face_image)[1].tostring()
    base64_img_str = "data:image/jpeg;base64," + base64.b64encode(base64_img_str).decode("utf-8")
    return base64_img_str

def get_enrolled(image, name):

    faces = fr.face_locations(image)
    if len(faces)>1:
        return {"res": False, "msg": "More than one faces are detected in the image..."}

    elif len(faces)==0:
        return {"res": False, "msg": "No face is detected in the image"}
    else:
        try:
            top, right, bottom, left = faces[0]
            face_image = cv2.resize(image[top:bottom, left:right], (200, 200))
            # file_name = save_img(face_image)
            base64_img_str = cv2.imencode('.jpg', face_image)[1].tostring()
            base64_img_str = "data:image/jpeg;base64," + base64.b64encode(base64_img_str).decode("utf-8")
            face_encoding = fr.face_encodings(image, known_face_locations=faces)[0]
            check, _id, _= is_exist(face_encoding)
            if not check:
                sql_as_text = json.dumps(list(face_encoding))
                conn.execute(users.insert().values(
                    name = name,
                    img = base64_img_str,
                    encoding = sql_as_text
                ))
                return {"res": True, "msg": "Enrolled."}
            else:
                return {"res": False, "msg": "Already Enrolled with ID : {id}".format(id=_id)}
        except Exception as e:
            return {"res": False, "msg": str(e)}

def save_img(image):
    file_name = "./Images/" + str(uuid.uuid4()) + ".jpg"
    cv2.imwrite(file_name, image)
    return file_name

def get_image(user_id):

    data = conn.execute(users.select().where(users.c.id == user_id)).fetchall()

def search_image(image):
    faces = fr.face_locations(image)
    face1_size = list()
    face_images = list()
    for (top, right, bottom, left) in faces:
        face = image[top:bottom, left:right]
        dim = face.shape
        size = dim[0] * dim[1]
        face1_size.append(size)
        face_images.append(face)
    encoding = fr.face_encodings(image, known_face_locations=[faces[np.argmax(face1_size)]])[0]
    check, face_id, val = is_exist(encoding)
    face_detected = numpy2String(face_images[np.argmax(face1_size)])
    if check:
        # data = conn.execute(users.select().where(users.c.id == face_id))
        return {"res": True, "face_id": face_id, "face_detected": face_detected, "accuracy": val}
    else:
        return {"res": False, "face_id": "Unknown", "face_detected": face_detected, "accuracy": val}

def verify_images(image_1, image_2):
    try:
        face1_loc = fr.face_locations(image_1)
        face2_loc = fr.face_locations(image_2)
        face1_size = list()
        face2_size = list()
        face1_images = list()
        face2_images = list()
        for (top, right, bottom, left) in face1_loc:
            face = image_1[top:bottom, left:right]
            dim = face.shape
            size = dim[0] * dim[1]
            face1_size.append(size)
            face1_images.append(face)
        for (top, right, bottom, left) in face2_loc:
            face = image_2[top:bottom, left:right]
            dim = face.shape
            size = dim[0] * dim[1]
            face2_size.append(size)
            face2_images.append(face)
        face1_encoding = fr.face_encodings(image_1, known_face_locations=[face1_loc[np.argmax(face1_size)]], model='large')[0]
        face2_encoding = fr.face_encodings(image_2, known_face_locations=[face2_loc[np.argmax(face2_size)]], model='large')[0]
        match = fr.compare_faces([face1_encoding], face2_encoding, tolerance=0.515)
        face_distance = fr.face_distance([face1_encoding], face2_encoding)
        val = face_distance_to_conf(face_distance[0]) * 100
        face1 = numpy2String(face1_images[np.argmax(face1_size)])
        face2 = numpy2String(face2_images[np.argmax(face2_size)])
        if match[0]:
            result = {'res': True, "msg": 'Matched', 'accuracy': val, "face1": face1, "face2": face2}
            return result
        else:
            result = {'res': False, "msg": 'Not Matched', 'accuracy': val, "face1": face1, "face2": face2}
            return result
        
    except Exception as e:
        result = {'res': False, "msg": 'Unable to verify, please try again', 'accuracy' : '0 %'}
        return result

def byte2numpy(contents):
    nparr = np.fromstring(contents, np.uint8)
    img_np = cv2.imdecode(nparr, flags=1)
    return img_np
def update_enrollment(image, name):
    faces = fr.face_locations(image)
    if len(faces)>1:
        return {"res": False, "msg": "More than one faces are detected in the image..."}
    elif len(faces)==0:
        return {"res": False, "msg": "No face is detected in the image"}
    else:
        try:
            top, right, bottom, left = faces[0]
            face_image = image[top:bottom, left:right]
            face_img_b64 = numpy2String(face_image)
            file_name = save_img(face_image)
            face_encoding = fr.face_encodings(image, known_face_locations=faces)[0]
            check, _id, _= is_exist(face_encoding)
            sql_as_text = json.dumps(list(face_encoding))
            if not check:
                conn.execute(users.insert().values(
                    name = name,
                    img = face_img_b64,
                    encoding = sql_as_text
                ))
                return {"res": False, "msg": "Enrolled."}
            else:
                return {"res": True, "image_path": file_name, "encoding": sql_as_text}
        except Exception as e:
            return {"res": False, "msg": str(e)}