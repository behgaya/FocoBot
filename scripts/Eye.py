import cv2
import mediapipe as mp
import os

# Paths
input_dir = "data/calibracao/calib_faces"
output_dir = "data/calibracao/calib_eyes"
os.makedirs(output_dir, exist_ok=True)

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1)

# Landmark indices for eyes (from MediaPipe)
LEFT_EYE = [33, 133, 160, 159, 158, 153, 144, 145, 153]  # approximate
RIGHT_EYE = [362, 263, 387, 386, 385, 380, 373, 374, 380]

def crop_eyes(image, landmarks):
    h, w, _ = image.shape
    # Get all eye points
    eye_points = []
    for idx in LEFT_EYE + RIGHT_EYE:
        lm = landmarks[idx]
        x, y = int(lm.x * w), int(lm.y * h)
        eye_points.append((x, y))
    # Compute bounding box
    xs, ys = zip(*eye_points)
    x_min, x_max = max(min(xs) - 5, 0), min(max(xs) + 5, w)
    y_min, y_max = max(min(ys) - 5, 0), min(max(ys) + 5, h)
    return image[y_min:y_max, x_min:x_max]

# Process all images
for filename in os.listdir(input_dir):
    if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
        continue
    img_path = os.path.join(input_dir, filename)
    image = cv2.imread(img_path)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    
    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark
        eyes_img = crop_eyes(image, landmarks)
        out_path = os.path.join(output_dir, filename)
        cv2.imwrite(out_path, eyes_img)
        print(f"Saved eyes-only image: {out_path}")
    else:
        print(f"No face detected in {filename}")
