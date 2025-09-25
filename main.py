import cv2
import easyocr
from ultralytics import YOLO
import firebase_admin
from firebase_admin import credentials, db, storage
import time
import uuid
import os

# Firebase Info
SERVICE_KEY_PATH = "serviceAccountKey.json"
DATABASE_URL = "https://kahseng-9092f-default-rtdb.firebaseio.com"
STORAGE_BUCKET = "kahseng-9092f.appspot.com"
UID = "Lr1lvepjRRRwLM0Jqi7DixmAf62"
CAMERA_ID = "laptop_cam"
MODEL_PATH = "custon_data.pt"

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_KEY_PATH)
    firebase_admin.initialize_app(cred, {
        "databaseURL": DATABASE_URL,
        "storageBucket": STORAGE_BUCKET
    })

bucket = storage.bucket()

def upload_frame_to_storage(frame, label):
    """Save a frame locally and upload it to Firebase Storage"""
    filename = f"{label}_{uuid.uuid4().hex}.jpg"
    cv2.imwrite(filename, frame)

    blob = bucket.blob(f"{UID}/{CAMERA_ID}/{filename}")
    blob.upload_from_filename(filename)
    blob.make_public()  

    os.remove(filename)
    return blob.public_url


def run_food_recognition(video_path=0, model_path=MODEL_PATH):
    model = YOLO(model_path)
    reader = easyocr.Reader(['en'], gpu=False)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video source.")
        return

    threshold = 0.8 

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, stream=True)
        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                if conf >= threshold:
                    cls = int(box.cls[0])
                    label = model.names[cls]
                    xyxy = box.xyxy[0].cpu().numpy().astype(int)
                    x1, y1, x2, y2 = xyxy

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{label} {conf:.2f}",
                                (x1, y1 - 5),
                                cv2.FONT_HERSHEY_COMPLEX, 0.65, (0, 255, 0), 2)

        # --- EasyOCR text detection ---
        text_results = reader.readtext(frame)
        for bbox, text, score in text_results:
            if score >= threshold:
                top_left = tuple(map(int, bbox[0]))
                bottom_right = tuple(map(int, bbox[2]))

                cv2.rectangle(frame, top_left, bottom_right, (255, 0, 0), 2)
                cv2.putText(frame, f"{text} {score:.2f}",
                            top_left,
                            cv2.FONT_HERSHEY_COMPLEX, 0.65, (255, 0, 0), 2)

                # --- Save results to Firebase ---
                timestamp = int(time.time())
                image_url = upload_frame_to_storage(frame, text)

                ref = db.reference(f"users/{UID}/food_detections/{CAMERA_ID}")
                ref.push({
                    "text": text,
                    "confidence": round(score, 2),
                    "timestamp": timestamp,
                    "image_url": image_url
                })

        cv2.imshow("Food Recognition (YOLOv8 + EasyOCR)", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_food_recognition(video_path=0, model_path=MODEL_PATH)
