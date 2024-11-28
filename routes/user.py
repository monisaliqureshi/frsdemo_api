from fastapi import APIRouter, File, UploadFile, Form
from config.db import conn
from model.index import users
from face_utils.utils import get_enrolled, search_image, verify_images, byte2numpy, update_enrollment


user = APIRouter()


@user.get("/enrolled_persons")
async def read_data():
    return conn.execute(users.select()).fetchall()

@user.get("/enrolled_persons/{id}")
async def read_data(
                id
                ):
    return conn.execute(users.select().where(users.c.id == id)).fetchall()


@user.post("/enroll_person")
async def enrollment(
                image: UploadFile = File(...), 
                name: str = Form(...), 
                ):
    try:
        contents = image.file.read()
        image = byte2numpy(contents)
    except Exception as e:
        return {"message": "There was an error uploading the file"}
    finally:
        # image.file.close()
        pass
    # image = stringToRGB(user.img_b64.split(",")[-1])
    return get_enrolled(image, name)

@user.put("/enrolled_persons/{id}")
async def update_data(
            id:int, name: str = Form(...), 
            file: UploadFile = File(...), 
            ):
    try:
        contents = file.file.read()
        image = byte2numpy(contents)
    except Exception as e:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()
    data = update_enrollment(image, name)
    if data['res']:
        image_path = data['image_path']
        encoding = data['encoding']
        conn.execute(users.update().values(
            name=name,
            img=image_path,
            encoding=encoding
        ).where(users.c.id == id))

    return conn.execute(users.select()).fetchall()

@user.delete("/enrolled_persons/{id}")
async def delete_user(
                id: int, 
                ):
    conn.execute(users.delete().where(users.c.id == id))
    return conn.execute(users.select()).fetchall()

@user.post("/search_by_img")
async def one_to_many(
                file: UploadFile = File(...), 
                ):
    try:
        contents = file.file.read()
        image = byte2numpy(contents)
    except Exception as e:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()
    # image = stringToRGB(query.img_b64.split(",")[-1])
    return search_image(image)

@user.post("/verify")
async def one_to_one(
                file1: UploadFile = File(...), 
                file2: UploadFile = File(...), 
                ):
    try:
        contents1 = file1.file.read()
        image1 = byte2numpy(contents1)
    except Exception as e:
        return {"message": "There was an error uploading the file"}
    finally:
        file1.file.close()
    
    try:
        contents2 = file2.file.read()
        image2 = byte2numpy(contents2)
    except Exception as e:
        return {"message": "There was an error uploading the file"}
    finally:
        file2.file.close()
    # image_1 = stringToRGB(query.img1_b64.split(",")[-1])
    # image_2 = stringToRGB(query.img2_b64.split(",")[-1])
    return verify_images(image1, image2)
