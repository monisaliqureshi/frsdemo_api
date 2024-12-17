import cv2 as cv
import numpy as np
from sface import SFace
from yunet import YuNet
from fastapi import FastAPI, File, UploadFile
import base64
import asyncpg
import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from datetime import datetime

async def log_action(action: str, status: str):
    """Log an action to the database."""
    now = datetime.now()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO logs (date, time, action, status) VALUES ($1, $2, $3, $4);",
            now.date(), now.time(), action, status
        )


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

# Initialize FastAPI app
app = FastAPI(title="Face Management System with PostgreSQL")


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Database connection pool
pool = None
DATABASE_URL = "postgresql://monisaliqureshi:IEwi8B7ZaAfH@ep-wispy-night-a5bp95el.us-east-2.aws.neon.tech/frsapi?sslmode=require"  # Replace with your Neon connection string

async def init_db():
    """Initialize the database."""
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS faces (
                id SERIAL PRIMARY KEY,
                face_id TEXT UNIQUE NOT NULL,
                features BYTEA NOT NULL,
                image BYTEA NOT NULL
            );

            CREATE TABLE IF NOT EXISTS logs (
                log_id SERIAL PRIMARY KEY,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL
            );
        """)

@app.on_event("startup")
async def startup_event():
    """Initialize the connection pool and database."""
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Close the connection pool."""
    if pool:
        await pool.close()

def detect_face(image):
    detector.setInputSize([image.shape[1], image.shape[0]])
    faces = detector.infer(image)
    if len(faces) != 1:
        return None, False
    return faces[0], True

def extract_features(image, face):
    x, y, w, h = face[:4].astype(int)
    cropped_face = image[y:y+h, x:x+w]
    features = recognizer.infer(cropped_face)  # Ensure `feature` is the correct method
    return features

def convert_byte_to_numpy(content):
    nparr = np.frombuffer(content, np.uint8)
    image = cv.imdecode(nparr, cv.IMREAD_COLOR)
    return image

@app.post("/enroll_face")
async def enroll_face(face_id: str, file: UploadFile = File(...)):
    content = await file.read()
    image = convert_byte_to_numpy(content)
    face, has_face = detect_face(image)
    if not has_face:
        return {"error": "No valid face detected or multiple faces found."}
    
    features = extract_features(image, face)
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO faces (face_id, features, image) VALUES ($1, $2, $3);",
                face_id,
                features.tobytes(),
                content
            )
            await log_action("enroll", "success")
            return {"message": f"Face with ID '{face_id}' successfully enrolled."}
        except asyncpg.UniqueViolationError:
            await log_action("enroll", "error")
            return {"error": f"Face with ID '{face_id}' already exists."}

@app.get("/view_enrolled_faces")
async def view_enrolled_faces(page: int = 1, limit: int = 10):
    """
    Retrieve enrolled faces and their images with pagination.
    - `page`: Page number (default = 1).
    - `limit`: Number of faces per page (default = 10).
    """
    offset = (page - 1) * limit
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT face_id, image FROM faces ORDER BY id ASC LIMIT $1 OFFSET $2;", 
            limit, offset
        )
        total = await conn.fetchval("SELECT COUNT(*) FROM faces;")
    
    # Encode images to base64
    faces = [
        {
            "face_id": row["face_id"],
            "image_base64": base64.b64encode(row["image"]).decode("utf-8")
        }
        for row in rows
    ]
    
    return {
        "page": page,
        "limit": limit,
        "total_faces": total,
        "faces": faces
    }

@app.get("/view_enrolled_face/{face_id}")
async def view_enrolled_face(face_id: str):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT image FROM faces WHERE face_id = $1;", face_id)
        if not row:
            return {"error": f"Face with ID '{face_id}' not found."}
        image_base64 = base64.b64encode(row["image"]).decode("utf-8")
        return {"face_id": face_id, "image_base64": image_base64}

@app.delete("/delete_face/{face_id}")
async def delete_face(face_id: str):
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM faces WHERE face_id = $1;", face_id)
        if result == "DELETE 0":
            await log_action("delete", "error")
            return {"error": f"Face with ID '{face_id}' not found."}
        await log_action("delete", "success")
        return {"message": f"Face with ID '{face_id}' successfully deleted."}

@app.post("/search_face")
async def search_face(file: UploadFile = File(...)):
    content = await file.read()
    image = convert_byte_to_numpy(content)
    face, has_face = detect_face(image)
    if not has_face:
        await log_action("search", "error")
        return {"error": "No valid face detected or multiple faces found."}
    
    features = extract_features(image, face)
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT face_id, features FROM faces;")
        for row in rows:
            stored_features = np.frombuffer(row["features"], dtype=np.float32)
            match_list, conf_list = recognizer.n_match_norml2(features, stored_features)
            index = np.argmax(match_list)
            if match_list[index]:
                await log_action("search", "matched")
                return {"matched_face_id": row["face_id"], "confidence": conf_list[index]*100}
        await log_action("search", "not matched")
        return {"message": "No match found."}

@app.post("/verify_faces")
async def verify_faces(file1: UploadFile = File(...), file2: UploadFile = File(...)):
    content1 = await file1.read()
    content2 = await file2.read()
    image1 = convert_byte_to_numpy(content1)
    image2 = convert_byte_to_numpy(content2)
    face1, has_face1 = detect_face(image1)
    face2, has_face2 = detect_face(image2)
    if not (has_face1 and has_face2):
        await log_action("verify", "error")
        return {"error": "Both images must contain exactly one valid face."}
    
    features1 = extract_features(image1, face1)
    features2 = extract_features(image2, face2)
    score, matched = recognizer.match(image1, face1, image2, face2)
    status = "matched" if matched else "not matched"
    await log_action("verify", status)
    return {"matched": matched, "confidence": score*100}

@app.get("/logs")
async def get_logs(page: int = 1, limit: int = 10):
    """
    Retrieve logs with pagination.
    - `page`: Page number (default = 1).
    - `limit`: Number of logs per page (default = 10).
    """
    offset = (page - 1) * limit
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM logs ORDER BY log_id DESC LIMIT $1 OFFSET $2;", 
            limit, offset
        )
        total = await conn.fetchval("SELECT COUNT(*) FROM logs;")
    return {
        "page": page,
        "limit": limit,
        "total_logs": total,
        "logs": [dict(row) for row in rows]
    }
    
@app.get("/logs/data/action_frequency")
async def action_frequency():
    """
    Get the frequency of each action in logs.
    """
    query = """
        SELECT action, COUNT(*) AS count
        FROM logs
        GROUP BY action
        ORDER BY count DESC;
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
    data = [{"action": row["action"], "count": row["count"]} for row in rows]
    return {"action_frequency": data}


@app.get("/logs/data/status_distribution")
async def status_distribution():
    """
    Get the distribution of statuses in logs.
    """
    query = """
        SELECT status, COUNT(*) AS count
        FROM logs
        GROUP BY status
        ORDER BY count DESC;
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
    data = [{"status": row["status"], "count": row["count"]} for row in rows]
    return {"status_distribution": data}


@app.get("/logs/data/actions_over_time")
async def actions_over_time():
    """
    Get the number of actions logged per date.
    """
    query = """
        SELECT date, COUNT(*) AS count
        FROM logs
        GROUP BY date
        ORDER BY date ASC;
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
    data = [{"date": str(row["date"]), "count": row["count"]} for row in rows]
    return {"actions_over_time": data}



if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000)
