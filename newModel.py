

# NEW VERSION: MediaPipe Tasks API
import cv2
import mediapipe as mp
import keyboard
import time
import numpy as np
import urllib.request
import os
import asyncio

# Download the hand landmark model if not present
MODEL_PATH = "hand_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-assets/hand_landmarker.task"
if not os.path.exists(MODEL_PATH):
    print("Downloading hand_landmarker.task model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision


def get_system_playback_state():
    """Return current system playback state as a string ('Playing'/'Paused') or None if unavailable."""
    try:
        # Import here so script still runs if winrt isn't installed; fallback to None
        from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as GSM
        op = GSM.request_async()
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        mgr = loop.run_until_complete(op)
        session = mgr.get_current_session()
        if not session:
            return None
        playback_info = session.get_playback_info()
        status = playback_info.playback_status
        # Try to return readable name
        try:
            return status.name
        except Exception:
            return str(status)
    except Exception:
        return None

def detect_gesture(landmarks):
    fingers_up = []
    # Thumb: Tip (4) vs IP joint (3)
    if landmarks[4].x < landmarks[3].x:
        fingers_up.append(1)
    else:
        fingers_up.append(0)
    # Index to pinky: Tip vs PIP joints
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    for tip, pip in zip(tips, pips):
        fingers_up.append(1 if landmarks[tip].y < landmarks[pip].y else 0)
    # Define gestures
    if fingers_up == [1, 1, 1, 1, 1]:      # Open hand
        return "play"
    elif fingers_up == [0, 0, 0, 0, 0]:   # Fist
        return "pause"
    elif fingers_up == [0, 1, 1, 0, 0]:   # V-shape
        return "fast_forward"
    elif fingers_up == [1, 1, 0, 0, 0]:   # Index & Thumb
        return "rewind"
    return "none"

def detect_gesture_left(landmarks):
    fingers_up = []
    # Thumb: Tip (4) vs IP joint (3) - mirrored for left hand
    if landmarks[4].x > landmarks[3].x:
        fingers_up.append(1)
    else:
        fingers_up.append(0)
    # Index to pinky: Tip vs PIP joints
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    for tip, pip in zip(tips, pips):
        fingers_up.append(1 if landmarks[tip].y < landmarks[pip].y else 0)
    # Define gestures
    if fingers_up == [1, 1, 1, 1, 1]:      # Open hand
        return "play"
    elif fingers_up == [0, 0, 0, 0, 0]:   # Fist
        return "pause"
    elif fingers_up == [0, 1, 1, 0, 0]:   # V-shape
        return "fast_forward"
    elif fingers_up == [1, 1, 0, 0, 0]:   # Index & Thumb
        return "rewind"
    return "none"

# No VLC setup needed; we'll send global media keys

# MediaPipe Tasks HandLandmarker setup
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = vision.HandLandmarker
HandLandmarkerOptions = vision.HandLandmarkerOptions
HandLandmarkerResult = vision.HandLandmarkerResult

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7,
)

detector = HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
cooldown = 2
last_time = 0
last_action = None

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    timestamp = int(time.time() * 1000)
    result = detector.detect_for_video(mp_image, timestamp)

    now = time.time()
    gesture = "none"

    if result.hand_landmarks:
        for i, hand_landmarks in enumerate(result.hand_landmarks):
            handedness = None
            if result.handedness and i < len(result.handedness):
                if result.handedness[i]:
                    handedness = result.handedness[i][0].category_name
            # Frame is mirrored, so swap handedness labels.
            if handedness == "Left":
                handedness = "Right"
            elif handedness == "Right":
                handedness = "Left"

            if handedness == "Left":
                gesture = detect_gesture_left(hand_landmarks)
            else:
                gesture = detect_gesture(hand_landmarks)
            if now - last_time > cooldown:
                send_key = False
                if gesture == "play":
                    state = get_system_playback_state()
                    if state is None:
                        # Fallback to previous behavior when system state is unavailable
                        if last_action != "play":
                            keyboard.send('play/pause media')
                            print("Play/Pause (media key)")
                            last_action = "play"
                            send_key = True
                    else:
                        # Only send play if current state is not Playing
                        if state.lower() != "playing":
                            keyboard.send('play/pause media')
                            print(f"▶️ Play (was {state})")
                            last_action = "play"
                            send_key = True
                elif gesture == "pause":
                    state = get_system_playback_state()
                    if state is None:
                        # Fallback to previous behavior when system state is unavailable
                        if last_action != "pause":
                            keyboard.send('play/pause media')
                            print("Play/Pause (media key)")
                            last_action = "pause"
                            send_key = True
                    else:
                        # Only send pause if current state is Playing
                        if state.lower() == "playing":
                            keyboard.send('play/pause media')
                            print(f"⏸️ Pause (was {state})")
                            last_action = "pause"
                            send_key = True
                elif gesture == "fast_forward":
                    keyboard.send('right')
                    print("Right Arrow (seek forward)")
                    last_action = "fast_forward"
                    send_key = True
                elif gesture == "rewind":
                    keyboard.send('left')
                    print("Left Arrow (seek backward)")
                    last_action = "rewind"
                    send_key = True
                if send_key:
                    last_time = now
            # Draw landmarks
            for lm in hand_landmarks:
                x, y = int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0])
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

    cv2.putText(frame, f"Gesture: {gesture}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Gesture Control (MediaPipe Tasks)", frame)
    if cv2.waitKey(10) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
