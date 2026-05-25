import asyncio
import websockets
import struct
import cv2
import mediapipe as mp
import numpy as np
import matplotlib.pyplot as plt
import time
import os
import pandas as pd
from collections import deque
from scipy.spatial.distance import euclidean
import seaborn as sns
from matplotlib.ticker import MaxNLocator
from datetime import datetime
from deepface import DeepFace
import dlib
from scipy.spatial import distance as dist
import firebase_operations as fo
import json
import time

latest_frame = None
frame_lock = asyncio.Lock()

async def receiver(websocket, analyzer):
    print("Receiver started")
    global latest_frame

    while True:
        try:
            msg = await websocket.recv()

            # 🔹 Try JSON (control message)
            try:
                data = json.loads(msg)
                msg_type = data.get("type")

                if msg_type == "start_session":
                    student = data.get("student_name", "unknown")
                    task = data.get("task_id", "t_00")

                    analyzer.current_student_name = student
                    analyzer.current_task_id = task

                    # ✅ RESET CALIBRATION
                    analyzer.eye_tracker.modified_ear_detector.is_calibrated = False
                    analyzer.eye_tracker.modified_ear_detector.calibration_data = []
                    analyzer.eye_tracker.modified_ear_detector.calibration_landmarks = []
                    analyzer.eye_tracker.modified_ear_detector.total_blinks = 0

                    # reset UI status
                    analyzer.calibration_status = "Not started yet"

                    print(f"START SESSION: {student} {task}")

                    analyzer.is_tracking = True
                    analyzer.start_time = time.time()
                    analyzer.next_save_time = 5
                    analyzer.data = {k: [] for k in analyzer.data}

                    analyzer.output_folder = analyzer.create_output_folder()
                    os.makedirs(analyzer.output_folder, exist_ok=True)

                elif msg_type == "end_session":
                    print("END SESSION")

                    analyzer.is_tracking = False
                    analyzer.save_results()

                continue

            except:
                pass

            # 🔹 Otherwise it's frame
            size = struct.unpack(">I", msg)[0]
            frame_data = await websocket.recv()

            if len(frame_data) != size:
                continue

            async with frame_lock:
                latest_frame = frame_data

        except Exception as e:
            print("Receiver error:", e)
            await asyncio.sleep(0.1)
            continue

async def sender(websocket, analyzer):

    print("Sender started")
    while True:
        try:
            if analyzer.is_tracking:
                data = {
                    "type": "metrics",
                    "overall": analyzer.data['overall'][-1] if analyzer.data['overall'] else 0,
                    "eye": analyzer.data['eye_attention'][-1] if analyzer.data['eye_attention'] else 0,
                    "face": analyzer.data['face_attention'][-1] if analyzer.data['face_attention'] else 0,
                    "emotion": analyzer.data['emotion'][-1] if analyzer.data['emotion'] else 0,
                    "calibration_status": analyzer.calibration_status,
                    "timestamp": time.time()
                    
                }

                await websocket.send(json.dumps(data))

            await asyncio.sleep(0.1)  # real-time but stable
            # await asyncio.sleep(0.02) # more real-time, may cause more fluctuations

        except Exception as e:
            print("Sender error:", e)
            await asyncio.sleep(0.1)
            continue

class ModifiedEARBlinkDetector:
    def __init__(self, calibration_frames=200, blink_consecutive_frames=3):
        """
        Initialize the Modified EAR Blink Detector
        
        Args:
            calibration_frames: Number of frames to use for calibration
            blink_consecutive_frames: Number of consecutive frames below threshold to count as blink
        """
        # Initialize dlib's face detector and facial landmark predictor
        self.detector = dlib.get_frontal_face_detector()
        try:
            self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
        except Exception as e:
            raise RuntimeError(
                "Could not load landmarks model at 'shape_predictor_68_face_landmarks.dat'. "
                "Please ensure the file is in your working directory."
            ) from e

        # Eye landmark indices (0-indexed)
        self.LEFT_EYE = list(range(36, 42))
        self.RIGHT_EYE = list(range(42, 48))

        # Calibration parameters
        self.calibration_frames = calibration_frames
        self.calibration_data = []
        self.calibration_landmarks = []
        self.is_calibrated = False
        self.modified_ear_threshold = 0.25

        # Blink detection parameters
        self.blink_consecutive_frames = blink_consecutive_frames
        self.eye_closed_frames = 0
        self.frame_counter = 0
        self.total_blinks = 0

        # Smoothing buffer for EAR
        self.recent_ears = deque(maxlen=10)

        # Timing and stats
        self.start_time = time.time()
        self.blink_times = []

    def extract_eye_landmarks(self, landmarks, eye_indices):
        """Extract eye landmarks from full-face landmarks."""
        points = []
        for i in eye_indices:
            pt = landmarks.part(i)
            points.append((pt.x, pt.y))
        return np.array(points, dtype="float")
    
    def calculate_ear(self, eye):
        """Compute Eye Aspect Ratio for one eye."""
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)

    def calculate_modified_ear_threshold(self):
        """
        Compute a tailored threshold based on calibration:
          EAR_closed = (min vertical) / (2 × max horizontal)
          EAR_open   = (max vertical) / (2 × min horizontal)
          Threshold  = (EAR_closed + EAR_open) / 2
        """
        if len(self.calibration_landmarks) < 10:
            return 0.25

        vertical = []
        horizontal = []
        for left, right in self.calibration_landmarks:
            for eye in (left, right):
                A = dist.euclidean(eye[1], eye[5])
                B = dist.euclidean(eye[2], eye[4])
                C = dist.euclidean(eye[0], eye[3])
                vertical.append(A + B)
                horizontal.append(C)

        v_min, v_max = np.min(vertical), np.max(vertical)
        h_min, h_max = np.min(horizontal), np.max(horizontal)

        ear_closed = v_min / (2 * h_max)
        ear_open = v_max / (2 * h_min)
        threshold = (ear_closed + ear_open) / 2
        return float(np.clip(threshold, 0.15, 0.35))

    def calibrate(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)
        if not faces:
            print("[Calibration] No face detected.")
            return None, "No face detected", 0, 0  # Added return values

        shape = self.predictor(gray, faces[0])
        left = self.extract_eye_landmarks(shape, self.LEFT_EYE)
        right = self.extract_eye_landmarks(shape, self.RIGHT_EYE)
        self.calibration_landmarks.append((left, right))

        left_ear = self.calculate_ear(left)
        right_ear = self.calculate_ear(right)
        self.calibration_data.append((left_ear + right_ear) / 2.0)

        current_frame = len(self.calibration_data)
        total_frames = self.calibration_frames
        
        if current_frame <= total_frames // 2:
            status = "Keep eyes OPEN"
            instruction = "Look straight at the camera"
        else:
            status = "Keep eyes CLOSED"
            instruction = "Keep eyes gently closed"

        if len(self.calibration_data) >= self.calibration_frames:
            self.modified_ear_threshold = self.calculate_modified_ear_threshold()
            self.is_calibrated = True
            self.start_time = time.time()
            print(f"[Calibration] Completed. Threshold = {self.modified_ear_threshold:.3f}")
            return True, "Calibration Complete", current_frame, total_frames
        
        return False, f"{status} ({current_frame}/{total_frames})", current_frame, total_frames
            
        
    def detect_blinks(self, frame):
        """Process a frame: compute EAR, detect blinks, and update counters."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)
        blinked = False
        ear_val = 0.0

        if faces:
            shape = self.predictor(gray, faces[0])
            left = self.extract_eye_landmarks(shape, self.LEFT_EYE)
            right = self.extract_eye_landmarks(shape, self.RIGHT_EYE)

            left_ear = self.calculate_ear(left)
            right_ear = self.calculate_ear(right)
            ear_val = (left_ear + right_ear) / 2.0

            self.recent_ears.append(ear_val)
            ear_smoothed = float(np.mean(self.recent_ears))

            if ear_smoothed < self.modified_ear_threshold:
                self.eye_closed_frames += 1
            else:
                if self.eye_closed_frames >= self.blink_consecutive_frames:
                    self.total_blinks += 1
                    self.blink_times.append(time.time())
                    blinked = True
                self.eye_closed_frames = 0

            ear_val = ear_smoothed

        self.frame_counter += 1
        return ear_val, blinked

    def draw_eye_landmarks(self, frame, left_eye, right_eye):
        """Draw eye landmarks on the frame."""
        cv2.polylines(frame, [left_eye.astype(np.int32)], True, (0, 255, 0), 1)
        cv2.polylines(frame, [right_eye.astype(np.int32)], True, (0, 255, 0), 1)

    def get_blink_rate(self):
        """Return blinks per minute since end of calibration."""
        elapsed = time.time() - self.start_time
        return (self.total_blinks / elapsed) * 60 if elapsed > 0 else 0.0
    

class EyeTracker:
    def __init__(self, min_blink_frames=3, max_blink_frames=20, fps=30):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=True,
            min_detection_confidence=0.6, min_tracking_confidence=0.6
        )

        self.LEFT_EYE_KEY = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_KEY = [362, 385, 387, 263, 373, 380]
        self.NOSE_TIP = 1
        self.LEFT_EYE_CENTER = 33
        self.RIGHT_EYE_CENTER = 362

        self.ear_threshold = 0.2
        self.calibrated = False
        self.custom_ear_threshold = None
        self.calibration_open_ear = None
        self.calibration_closed_ear = None
        
        self.gaze_history = deque(maxlen=30)
        self.blink_rate_history = deque(maxlen=30)
        self.ear_history = deque(maxlen=30)
        self.gaze_data = []
        self.blink_data = []
        
        # Initialize Modified EAR Blink Detector
        # In EyeTracker.__init__ and ModifiedEARBlinkDetector.__init__
        self.modified_ear_detector = ModifiedEARBlinkDetector(calibration_frames=200, blink_consecutive_frames=2)

    def extract_landmarks(self, landmarks, indices, img_w, img_h):
        return [
            [int(landmarks[i].x * img_w), int(landmarks[i].y * img_h)]
            for i in indices
        ]

    def calculate_ear(self, eye_points):
        if len(eye_points) < 6:
            return 0.25
        p = np.array(eye_points, dtype=np.float32)
        v1 = np.linalg.norm(p[1] - p[5])
        v2 = np.linalg.norm(p[2] - p[4])
        h = np.linalg.norm(p[0] - p[3])
        return (v1 + v2) / (2.0 * h) if h > 0 else 0.25

    def calculate_gaze_score(self, landmarks, img_w, img_h):
        try:
            nose = landmarks[self.NOSE_TIP]
            left = landmarks[self.LEFT_EYE_CENTER]
            right = landmarks[self.RIGHT_EYE_CENTER]

            nose_x = nose.x * img_w
            eye_center_x = (left.x + right.x) / 2 * img_w
            dx = abs((nose_x + eye_center_x) / 2 - img_w / 2)
            dy = abs(nose.y * img_h - img_h / 2)

            max_dx, max_dy = img_w * 0.3, img_h * 0.25
            gaze_score = max(0, 1 - (dx / max_dx)) * 0.7 + max(0, 1 - (dy / max_dy)) * 0.3

            self.gaze_history.append(gaze_score)
            return max(0.0, min(1.0, np.mean(self.gaze_history)))
        except Exception:
            return 0.5

    def calculate_attention_level(self, gaze_score, blink_rate, ear_value):
        gaze_sigmoid = 1 / (1 + np.exp(-8 * (gaze_score - 0.5)))
        gaze_component = gaze_sigmoid * 0.6

        if blink_rate == 0:
            blink_component = 0.5
        elif 14 <= blink_rate <= 18:
            blink_component = 1.0
        elif 10 <= blink_rate <= 22:
            blink_component = 0.9
        elif 8 <= blink_rate < 10 or 22 < blink_rate <= 28:
            blink_component = 0.7
        elif 6 <= blink_rate < 8 or 28 < blink_rate <= 35:
            blink_component = 0.4
        elif blink_rate < 6:
            blink_component = 0.3
        else:
            blink_component = max(0.1, 0.8 - ((blink_rate - 35) / 20))
        blink_component *= 0.25

        if ear_value < 0.12:
            normalized_ear = 0.1
        elif ear_value > 0.4:
            normalized_ear = 1.0
        else:
            normalized_ear = (ear_value - 0.12) / 0.23
        ear_component = normalized_ear * 0.15

        attention = gaze_component + blink_component + ear_component
        if gaze_score > 0.8:
            attention = min(1.0, attention * 1.1)
        elif gaze_score < 0.3:
            attention *= 0.8
            
        return max(0.0, min(1.0, attention))
    
    def update_eye_metrics(self, gaze_score, blink_rate, ear_value, timestamp):
        self.gaze_data.append({
            'timestamp': timestamp,
            'gaze_score': gaze_score * 100,
            'blink_rate': blink_rate,
            'ear_value': ear_value,
            'total_blinks': self.modified_ear_detector.total_blinks
        })
        self.gaze_history.append(gaze_score)
        self.blink_rate_history.append(blink_rate)
        self.ear_history.append(ear_value)

class EmotionAnalyzer:
    def __init__(self):
        self.attention_map = {
            "happy": 85, "surprise": 80, "neutral": 90,
            "fear": 50, "sad": 45, "angry": 50, "disgust": 50
        }
        self.emotion_buffer = deque(maxlen=15)
        casc_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(casc_path)
        self.last_emotion = "neutral"
        self.last_attention = 90

    def detect_emotion(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            return self.last_emotion, self.last_attention
        
        x, y, w, h = faces[0]
        face_roi = frame[y:y+h, x:x+w]
        
        try:
            analysis = DeepFace.analyze(face_roi, actions=["emotion"], enforce_detection=False)
            if isinstance(analysis, list):
                analysis = analysis[0]
            emotion = analysis["dominant_emotion"]
            attention = self.attention_map.get(emotion, 65)
            self.last_emotion = emotion
            self.last_attention = attention
            return emotion, attention
        except Exception:
            return self.last_emotion, self.last_attention

    def smooth_emotion(self, emotion):
        self.emotion_buffer.append(emotion)
        if len(self.emotion_buffer) < 3:
            return emotion
        return max(set(self.emotion_buffer), key=self.emotion_buffer.count)

class RealTimeAttentionAnalyzer:
    def __init__(self):

        self.current_student_name = "unknown"
        self.current_task_id = "t_00"

        self.calibration_status = "NIL"

        self.temp_emotions = []

        self.eye_tracker = EyeTracker()
        self.emotion_analyzer = EmotionAnalyzer()

        
        
        self.data = {
            'timestamp': [], 'eye_attention': [],
            'face_attention': [], 'overall': [],
            'emotion': [], 'gaze_score': [], 'blink_rate': [], 'total_blinks': []
        }
        
        self.start_time = time.time()
        self.next_save_time = 5
        self.is_tracking = False
      

    def create_output_folder(self):
        base = "output/attention_analysis"
        os.makedirs(base, exist_ok=True)

        name = self.current_student_name.replace(" ", "_").lower()
        task = self.current_task_id.replace(" ", "_").lower()

        folder_name = f"{name}_{task}"
        folder = os.path.join(base, folder_name)

        if os.path.exists(folder):
            from datetime import datetime
            timestamp = datetime.now().strftime("%H%M%S")
            folder = f"{folder}_{timestamp}"

        return folder
    
    def get_ear_threshold(self):
        """Get the calibrated EAR threshold from the blink detector"""
        if hasattr(self.eye_tracker, 'modified_ear_detector'):
            return self.eye_tracker.modified_ear_detector.modified_ear_threshold
        return None

    def process_frame(self, frame):
        if not self.is_tracking:
            return frame

        current_time = time.time() - self.start_time
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Initialize default values
        eye_attention = 0
        face_attention = 0
        overall = 0
        emotion = None
        gaze_score = 0
        blink_rate = 0
        ear_value = 0.25

        # Handle face processing
        face_results = self.eye_tracker.face_mesh.process(rgb)
        
        face_detected = False

        if face_results.multi_face_landmarks:
            face_detected = True
            landmarks = face_results.multi_face_landmarks[0].landmark
            h, w = frame.shape[:2]
            
            # Get face ROI for blink detection
            xs = [int(l.x * w) for l in landmarks]
            ys = [int(l.y * h) for l in landmarks]
            x_min, x_max = max(min(xs) - 20, 0), min(max(xs) + 20, w)
            y_min, y_max = max(min(ys) - 20, 0), min(max(ys) + 20, h)
            face_roi = frame[y_min:y_max, x_min:x_max].copy()
            if face_roi.size == 0:
                face_roi = frame

            # Handle calibration
            if not self.eye_tracker.modified_ear_detector.is_calibrated:
                # Get calibration status with more detailed info
                calibration_result = self.eye_tracker.modified_ear_detector.calibrate(face_roi)
                if calibration_result:
                    is_complete, status, current_frame, total_frames = calibration_result
                    self.calibration_status = status
                    
                    # Show calibration instructions on RIGHT side of screen
                    right_start_x = frame.shape[1] - 400
                    
                    # Calibration status box
                    cv2.rectangle(frame, (right_start_x, 10), (frame.shape[1]-10, 250), (0, 0, 0), -1)
                    
                    # Calibration title
                    cv2.putText(frame, "CALIBRATION IN PROGRESS", 
                            (right_start_x + 20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    
                    # Current status
                    cv2.putText(frame, status, 
                            (right_start_x + 20, 80), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    # Progress bar background
                    cv2.rectangle(frame, (right_start_x + 20, 110), 
                                (right_start_x + 370, 130), (50, 50, 50), -1)
                    
                    # Progress bar fill
                    progress_width = int(350 * (current_frame / total_frames)) if total_frames != 0 else 0
                    cv2.rectangle(frame, (right_start_x + 20, 110), 
                                (right_start_x + 20 + progress_width, 130), 
                                (0, 255, 0), -1)
                    
                    # Progress text
                    if total_frames != 0:
                        progress_percent = int(100 * current_frame / total_frames)
                        progress_text = f"Progress: {current_frame}/{total_frames} ({progress_percent}%)"
                    else:
                        progress_text = f"Progress: {current_frame}/{total_frames} (N/A%)"
                    cv2.putText(frame, progress_text, 
                            (right_start_x + 20, 160), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    # Show instructions based on calibration phase
                    if current_frame <= total_frames // 2:
                        instruction = "Look straight at camera with EYES OPEN"
                    else:
                        instruction = "Keep EYES CLOSED for calibration"
                    
                    cv2.putText(frame, instruction, 
                            (right_start_x + 20, 190), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            # Only process other metrics after calibration is complete
            if self.eye_tracker.modified_ear_detector.is_calibrated:
                # Set calibration status to DONE after calibration is complete
                self.calibration_status = "DONE" 
                # Normal processing after calibration
                ear_value, blink_detected = self.eye_tracker.modified_ear_detector.detect_blinks(face_roi)
                blink_rate = self.eye_tracker.modified_ear_detector.get_blink_rate()
                gaze_score = self.eye_tracker.calculate_gaze_score(landmarks, w, h)
                eye_attention = self.eye_tracker.calculate_attention_level(gaze_score, blink_rate, ear_value) * 100
                emotion, face_attention = self.emotion_analyzer.detect_emotion(frame)
                emotion = self.emotion_analyzer.smooth_emotion(emotion)
                if emotion is not None:
                    self.temp_emotions.append(emotion)

                # Update eye metrics
                self.eye_tracker.update_eye_metrics(
                    gaze_score, blink_rate, ear_value, current_time
                )

    
        # Calculate overall attention only after calibration
        if self.eye_tracker.modified_ear_detector.is_calibrated:
            if not face_detected:
                overall = 0
            else:
                weights = [0.5, 0.5]
                scores = [eye_attention, face_attention]
                overall = sum(w * s for w, s in zip(weights, scores))
        else:
            overall = 0  # Default during calibration

        # Save data periodically (only after calibration)
        if (current_time >= self.next_save_time and 
            self.eye_tracker.modified_ear_detector.is_calibrated):
            self.data['timestamp'].append(self.next_save_time)
            self.data['eye_attention'].append(round(eye_attention, 2))
            self.data['face_attention'].append(round(face_attention, 2))
            self.data['overall'].append(round(overall, 2))
            # if self.temp_emotions:
            #     final_emotion = max(set(self.temp_emotions), key=self.temp_emotions.count)
            #     self.temp_emotions = []
            # else:
            #     final_emotion = "NIL"

            # set emotion based on overall attention
            if overall == 0.0:
                final_emotion = "NIL"
                self.temp_emotions = []  # clear old emotions
            else:
                if self.temp_emotions:
                    final_emotion = max(set(self.temp_emotions), key=self.temp_emotions.count)
                    self.temp_emotions = []
                else:
                    final_emotion = "NIL"

            self.data['emotion'].append(final_emotion)
            self.data['gaze_score'].append(round(gaze_score * 100, 2))
            self.data['blink_rate'].append(round(blink_rate, 2))
            self.data['total_blinks'].append(self.eye_tracker.modified_ear_detector.total_blinks)
            self.next_save_time += 5
        
        self.display_overlay(frame, eye_attention, face_attention, overall, emotion)
        return frame

    def display_overlay(self, frame, eye, face, overall, emotion):
        # Left side panel for attention details
        y_start = 30
        spacing = 30
        cv2.rectangle(frame, (10, 10), (400, 220), (0, 0, 0), -1)
        
        # Get blink information
        if self.eye_tracker.modified_ear_detector.is_calibrated:
            total_blinks = self.eye_tracker.modified_ear_detector.total_blinks
            blink_rate = self.eye_tracker.modified_ear_detector.get_blink_rate()
        else:
            total_blinks = 0
            blink_rate = 0
        
        texts = [
            f"Eyes: {eye:.1f}%",
            f"Face: {face:.1f}% ({emotion})",
            f"Overall: {overall:.1f}%",
            f"Blinks: {total_blinks} ({blink_rate:.1f}/min)"
        ]
        
        colors = [
            (0, 255, 0) if eye > 70 else (0, 165, 255) if eye > 50 else (0, 0, 255),
            (0, 255, 0) if face > 70 else (0, 165, 255) if face > 50 else (0, 0, 255),
            (0, 255, 0) if overall > 70 else (0, 165, 255) if overall > 50 else (0, 0, 255),
            (0, 255, 0) if 10 <= blink_rate <= 20 else (0, 165, 255) if 8 <= blink_rate <= 25 else (0, 0, 255)
        ]
        
        for i, (text, color) in enumerate(zip(texts, colors)):
            cv2.putText(frame, text, (20, y_start + i*spacing), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Progress bar at bottom of left panel
        cv2.rectangle(frame, (20, 190), (370, 210), (50, 50, 50), -1)
        cv2.rectangle(frame, (20, 190), (20 + int(3.5 * overall), 210), 
                (0, 255, 0) if overall > 70 else (0, 165, 255) if overall > 50 else (0, 0, 255), -1)
                    
        # Tracking status at top right
        status_text = "TRACKING " if self.is_tracking else "PAUSED - Press 's' to start"
        status_color = (0, 255, 0) if self.is_tracking else (0, 0, 255)
        cv2.putText(frame, status_text, (frame.shape[1] - 300, frame.shape[0] - 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        
    def create_feature_scatter(self, folder, df, feature, title, xlabel):
        plt.figure()
        sns.regplot(
            x=df[feature], 
            y=df['overall'], 
            scatter_kws={'alpha': 0.6, 's': 40, 'color': 'steelblue'},
            line_kws={'color': 'red', 'linewidth': 2}
        )
        plt.xlabel(f'{xlabel} (%)')
        plt.ylabel('Overall Attention (%)')
        plt.title(title)
        plt.grid(True, alpha=0.3)
        plt.xlim(0, 100)
        plt.ylim(0, 100)
        plt.tight_layout()
        plt.savefig(os.path.join(folder, f"{feature}_vs_attention.png"))
        plt.close()
        
        correlation = df[[feature, 'overall']].corr().iloc[0,1]
        
        summary = f"""
{title.upper()}
"""
        with open(os.path.join(folder, "summary.txt"), 'w') as f:
            f.write(summary)

    def save_results(self):
        if not self.data['timestamp']:
            return
        
        df = pd.DataFrame(self.data)

        # remove NIL emotions from analysis
        # df = df[df['emotion'] != "NIL"]

        session_duration = df['timestamp'].max()
        session_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        ear_threshold = self.get_ear_threshold()
        
        csv_filename = os.path.join(self.output_folder, "attention_metrics.csv")
        df.to_csv(csv_filename, index=False)
        print(f"Raw metrics saved to: {csv_filename}")
        

        eye_folder = os.path.join(self.output_folder, "eye_tracking")
        face_folder = os.path.join(self.output_folder, "facial_expression")
        os.makedirs(eye_folder, exist_ok=True)
        os.makedirs(face_folder, exist_ok=True)
        
        eye_detail_folder = os.path.join(eye_folder, "detailed_analysis")
        os.makedirs(eye_detail_folder, exist_ok=True)
        
        self.save_eye_details(eye_detail_folder, df, session_date, session_duration)
        
        report = f"""
REAL-TIME ATTENTION ANALYSIS SUMMARY
======================================
Session Date       : {session_date}
Session Duration   : {session_duration:.1f} seconds
Overall Attention  : {df['overall'].mean():.1f}%
{'Calibrated EAR Threshold: ' + f"{ear_threshold:.3f}" if ear_threshold is not None else ""}

1. Component Scores
-------------------------------
- Eye Attention: {df['eye_attention'].mean():.1f}%
- Facial Expression: {df['face_attention'].mean():.1f}%

2. Emotion Distribution
-------------------------------
"""
        # emotion_percentages = df['emotion'].value_counts(normalize=True) * 100
        valid_emotions = df[df['emotion'] != "NIL"]

        if not valid_emotions.empty:
            emotion_percentages = valid_emotions['emotion'].value_counts(normalize=True) * 100
        else:
            emotion_percentages = {}

        for emotion, percentage in emotion_percentages.items():
            report += f"- {emotion.capitalize()}: {percentage:.1f}%\n"
            
        report += "\n3. Observations & Recommendations\n----------------------------------\n"
        report += self.generate_recommendations(df)
        
        with open(os.path.join(self.output_folder, "summary.txt"), 'w') as f:
            f.write(report)
        
        sns.set_style("whitegrid")
        plt.rcParams.update({
            'font.size': 10,
            'axes.titlesize': 12,
            'axes.labelsize': 10,
            'xtick.labelsize': 9,
            'ytick.labelsize': 9,
            'legend.fontsize': 9,
            'figure.dpi': 300,
            'savefig.dpi': 300,
            'figure.figsize': (10, 6)
        })
        
        plt.figure()
        plt.plot(df['timestamp'], df['overall'], 'b-', linewidth=2, label='Overall Attention')
        plt.fill_between(df['timestamp'], 0, df['overall'], color='blue', alpha=0.1)
        plt.xlabel('Time (seconds)')
        plt.ylabel('Attention Score (%)')
        plt.title('Attention Timeline')
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 100)
        plt.xlim(0, df['timestamp'].max() * 1.05)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_folder, "attention_timeline.png"))
        plt.close()
        
        self.create_feature_graphs(eye_folder, df, 'eye_attention', 'Eye Tracking Analysis', 'Eye Attention Score', session_date, session_duration)
        
        self.create_feature_graphs(
            face_folder, 
            df, 
            'face_attention', 
            'Facial Expression Analysis', 
            'Face Attention Score',
            session_date,
            session_duration,
            generate_timeline=False
        )
        self.create_emotion_distribution(face_folder, df)
                
        print(f"Results saved to: {self.output_folder}")


    
    def generate_recommendations(self, df):
        recommendations = []
        
        if df['eye_attention'].mean() < 60:
            recommendations.append("- Your eye attention score suggests frequent distractions. Minimize environmental distractions and focus on the task.")
        
        if df['face_attention'].mean() < 60:
            recommendations.append("- Your facial expression analysis indicates potential disengagement. Try to maintain a neutral or positive facial expression.")
        
        if not recommendations:
            return "- All metrics are within optimal ranges. Keep up the good focus!"
        
        return "\n".join(recommendations)

    def create_feature_graphs(self, folder, df, feature, title, xlabel, session_date, session_duration, generate_timeline=True):
        if generate_timeline:
            plt.figure()
            plt.plot(df['timestamp'], df[feature], 'g-', linewidth=1.5)
            plt.xlabel('Time (seconds)')
            plt.ylabel(f'{xlabel} (%)')
            plt.title(f'{title} - Score Over Time')
            plt.grid(True, alpha=0.3)
            plt.ylim(0, 100)
            plt.xlim(0, df['timestamp'].max() * 1.05)
            plt.tight_layout()
            plt.savefig(os.path.join(folder, f"{feature}_timeline.png"))
            plt.close()
        
        plt.figure()
        sns.regplot(
            x=df[feature], 
            y=df['overall'], 
            scatter_kws={'alpha': 0.6, 's': 40, 'color': 'steelblue'},
            line_kws={'color': 'red', 'linewidth': 2}
        )
        plt.xlabel(f'{xlabel} (%)')
        plt.ylabel('Overall Attention (%)')
        plt.title(f'{title} vs Overall Attention')
        plt.grid(True, alpha=0.3)
        plt.xlim(0, 100)
        plt.ylim(0, 100)
        plt.tight_layout()
        plt.savefig(os.path.join(folder, f"{feature}_vs_attention.png"))
        plt.close()
        
        plt.figure()
        sns.histplot(df[feature], bins=20, kde=True, color='skyblue')
        plt.xlabel(f'{xlabel} (%)')
        plt.ylabel('Frequency')
        plt.title(f'{title} Distribution')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(folder, f"{feature}_distribution.png"))
        plt.close()
        
        summary = f"""
{title.upper()} SUMMARY
======================================
Session Date       : {session_date}
Session Duration   : {session_duration:.1f} seconds
Overall Score      : {df[feature].mean():.1f}%

1. Score Distribution
-------------------------------
Minimum: {df[feature].min():.1f}%
Maximum: {df[feature].max():.1f}%
Average: {df[feature].mean():.1f}%

2. Correlation with Overall Attention
--------------------------------------
Correlation Coefficient: {df[[feature, 'overall']].corr().iloc[0,1]:.2f}

3. Time Analysis
-------------------------------
Optimal Time (%): {(df[feature] > 70).mean()*100:.1f}%
Suboptimal Time (%): {(df[feature] < 50).mean()*100:.1f}%
"""
        with open(os.path.join(folder, f"{feature.lower()}_summary.txt"), 'w') as f:
            f.write(summary)

    def create_emotion_distribution(self, folder, df):
        plt.figure()

        # emotion_counts = df['emotion'].value_counts()
        valid_emotions = df[df['emotion'] != "NIL"]
        if valid_emotions.empty:
            return
        emotion_counts = valid_emotions['emotion'].value_counts()


        sns.barplot(x=emotion_counts.index, 
            y=emotion_counts.values, 
            hue=emotion_counts.index,
            palette='viridis')
        plt.xlabel('Emotion')
        plt.ylabel('Count')
        plt.title('Emotion Distribution During Session')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(folder, "emotion_distribution.png"))
        plt.close()
        
        emotion_percentages = df['emotion'].value_counts(normalize=True) * 100
        emotion_summary = f"""
FACIAL EXPRESSION ANALYSIS SUMMARY
======================================
Session Duration: {df['timestamp'].max():.1f} seconds

1. Emotion Distribution
-------------------------------
"""
        for emotion, percentage in emotion_percentages.items():
            emotion_summary += f"- {emotion.capitalize()}: {percentage:.1f}%\n"
        
        emotion_summary += "\n2. Attention Impact\n-------------------------------\n"
        for emotion in emotion_percentages.index:
            avg_attention = valid_emotions[valid_emotions['emotion'] == emotion]['face_attention'].mean()
            emotion_summary += f"- {emotion.capitalize()}: {avg_attention:.1f}% attention\n"
        
        with open(os.path.join(folder, "emotion_summary.txt"), 'w') as f:
            f.write(emotion_summary)

    def save_eye_details(self, folder, df, session_date, session_duration):
        if not self.eye_tracker.gaze_data:
            return
            
        eye_df = pd.DataFrame(self.eye_tracker.gaze_data)
        ear_threshold = self.get_ear_threshold()
        
        # Save blink rate and related data as CSV
        eye_df.to_csv(os.path.join(folder, "blink_rate_details.csv"), index=False)

        # Save blink rate summary as TXT
        blink_stats = eye_df['blink_rate'].describe()
        with open(os.path.join(folder, "blink_rate_summary.txt"), 'w') as f:
            f.write(
                f"Blink Rate Statistics\n"
                f"=====================\n"
                f"Count: {blink_stats['count']:.0f}\n"
                f"Mean: {blink_stats['mean']:.2f} blinks/min\n"
                f"Std: {blink_stats['std']:.2f}\n"
                f"Min: {blink_stats['min']:.2f}\n"
                f"25%: {blink_stats['25%']:.2f}\n"
                f"50%: {blink_stats['50%']:.2f}\n"
                f"75%: {blink_stats['75%']:.2f}\n"
                f"Max: {blink_stats['max']:.2f}\n"
            )
            
        df = df.copy()
        df['timestamp'] = df['timestamp'].astype(float)
        merged_df = pd.merge_asof(
            eye_df.sort_values('timestamp'), 
            df[['timestamp', 'overall']].sort_values('timestamp'),
            on='timestamp',
            direction='nearest'
        )
        plt.figure(figsize=(12, 8))
        plt.subplot(3, 1, 1)
        plt.plot(eye_df['timestamp'], eye_df['gaze_score'], 'b-', label='Gaze Score')
        plt.ylabel('Gaze Score (%)')
        plt.title('Gaze Concentration Over Time')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        plt.subplot(3, 1, 2)
        plt.plot(eye_df['timestamp'], eye_df['blink_rate'], 'g-', label='Blink Rate')
        plt.ylabel('Blinks/Minute')
        plt.title('Blink Rate Over Time')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        plt.subplot(3, 1, 3)
        plt.plot(eye_df['timestamp'], eye_df['ear_value'], 'r-', label='EAR Value')
        plt.xlabel('Time (seconds)')
        plt.ylabel('EAR Value')
        plt.title('Eye Aspect Ratio (EAR) Over Time')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(folder, "eye_metrics_timeline.png"))
        plt.close()
        
        plt.figure()
        sns.histplot(eye_df['blink_rate'], bins=15, kde=True, color='teal')
        plt.axvline(x=15, color='r', linestyle='--', label='Optimal Zone (15 blinks/min)')
        plt.xlabel('Blink Rate (blinks/minute)')
        plt.ylabel('Frequency')
        plt.title('Blink Rate Distribution')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(folder, "blink_rate_distribution.png"))
        plt.close()
        
        plt.figure()
        sns.regplot(
            x=merged_df['gaze_score'], 
            y=merged_df['overall'], 
            scatter_kws={'alpha':0.6, 's':40, 'color':'purple'},
            line_kws={'color':'orange', 'linewidth':2}
        )
        plt.xlabel('Gaze Score (%)')
        plt.ylabel('Overall Attention (%)')
        plt.title('Gaze Concentration vs Overall Attention')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(folder, "gaze_vs_attention.png"))
        plt.close()
        
        plt.figure()
        sns.regplot(
            x=merged_df['blink_rate'], 
            y=merged_df['overall'], 
            scatter_kws={'alpha':0.6, 's':40, 'color':'green'},
            line_kws={'color':'red', 'linewidth':2}
        )
        plt.xlabel('Blink Rate (blinks/minute)')
        plt.ylabel('Overall Attention (%)')
        plt.title('Blink Rate vs Overall Attention')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(folder, "blink_rate_vs_attention.png"))
        plt.close()
        
        plt.figure()
        plt.scatter(
            eye_df['ear_value'], 
            eye_df['blink_rate'], 
            c=eye_df['gaze_score'], 
            cmap='viridis', 
            alpha=0.6,
            s=50
        )
        plt.colorbar(label='Gaze Score (%)')
        plt.axvline(x=self.eye_tracker.ear_threshold, color='r', linestyle='--', label='Blink Threshold')
        plt.xlabel('Eye Aspect Ratio (EAR)')
        plt.ylabel('Blink Rate (blinks/minute)')
        plt.title('EAR vs Blink Rate')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(folder, "ear_vs_blink_rate.png"))
        plt.close()
        
        avg_gaze = eye_df['gaze_score'].mean()
        blink_stats = eye_df['blink_rate'].describe()
        gaze_stats = eye_df['gaze_score'].describe()
        ear_stats = eye_df['ear_value'].describe()
        
        summary = f"""
DETAILED EYE TRACKING ANALYSIS SUMMARY
======================================
Session Date       : {session_date}
Session Duration   : {session_duration:.1f} seconds
{'Calibrated EAR Threshold: ' + f"{ear_threshold:.3f}" if ear_threshold is not None else ""}

1. Overall Metrics
-------------------------------
Overall Eye Attention: {avg_gaze:.1f}%

2. Blink Rate Analysis
-------------------------------
Average: {blink_stats['mean']:.1f} blinks/minute
Optimal Range (14-18): {((eye_df['blink_rate'] >= 14) & (eye_df['blink_rate'] <= 18)).mean()*100:.1f}% of samples
Low Blink Rate (<8): {(eye_df['blink_rate'] < 8).mean()*100:.1f}% of samples
High Blink Rate (>22): {(eye_df['blink_rate'] > 22).mean()*100:.1f}% of samples

3. Gaze Concentration
-------------------------------
Average: {gaze_stats['mean']:.1f}%
High Concentration (>80%): {(eye_df['gaze_score'] > 80).mean()*100:.1f}% of samples
Low Concentration (<40%): {(eye_df['gaze_score'] < 40).mean()*100:.1f}% of samples

4. Eye Aspect Ratio (EAR)
-------------------------------
Average: {ear_stats['mean']:.3f}
Threshold: {self.eye_tracker.ear_threshold:.3f}

5. Recommendations
-------------------------------
{self.generate_eye_recommendations(eye_df)}
"""
        with open(os.path.join(folder, "eye_analysis_summary.txt"), 'w') as f:
            f.write(summary)
    
    def generate_eye_recommendations(self, eye_df):
        avg_blink = eye_df['blink_rate'].mean()
        avg_gaze = eye_df['gaze_score'].mean()
        
        recommendations = []
        
        if avg_blink < 8:
            recommendations.append("- Your blink rate is low, which may indicate intense focus but can lead to eye strain. Try to blink more consciously.")
        elif avg_blink > 22:
            recommendations.append("- Your blink rate is higher than average, which may indicate distraction or eye discomfort. Consider checking your environment for irritants.")
        else:
            recommendations.append("- Your blink rate is in the optimal range for maintaining good eye health and focus.")
        
        if avg_gaze < 40:
            recommendations.append("- Your gaze concentration is low, suggesting frequent distractions. Try to minimize environmental distractions.")
        elif avg_gaze > 80:
            recommendations.append("- Your gaze concentration is excellent, but be mindful of taking regular breaks to prevent eye strain.")
        
        low_ear_frames = (eye_df['ear_value'] < self.eye_tracker.ear_threshold).sum()
        if low_ear_frames > len(eye_df) * 0.3:
            recommendations.append("- You're showing signs of eye fatigue with frequent partial blinks. Consider following the 20-20-20 rule: every 20 minutes, look at something 20 feet away for 20 seconds.")
        
        return "\n".join(recommendations)

    async def process_loop(self):
        global latest_frame

        print("Starting real-time attention analysis...")
        print("Press 'q' to quit")

        self.is_tracking = False

        try:

            while True:
                try:
                    async with frame_lock:
                        frame_data = latest_frame

                    if frame_data is None:
                        await asyncio.sleep(0.01)
                        continue

                    npimg = np.frombuffer(frame_data, dtype=np.uint8)
                    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

                    if frame is None:
                        continue

                    frame = self.process_frame(frame)

                    if not self.is_tracking:
                        cv2.putText(frame, "Press 's' to start tracking",
                                    (frame.shape[1]//2 - 200, frame.shape[0]//2),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

                    cv2.imshow('Attention Analysis', frame)

                    key = cv2.waitKey(1) & 0xFF

                    # if key == ord('s'):
                    #     self.is_tracking = True
                    #     self.start_time = time.time()
                    #     self.next_save_time = 5
                    #     self.data = {k: [] for k in self.data}

                    #     self.output_folder = self.create_output_folder()
                    #     os.makedirs(self.output_folder, exist_ok=True)
                    #     print("Tracking started...")

                    if key == ord('q'):
                        # break
                        print("Quit key pressed - ignored")

                    elif key == ord('p'):
                        self.is_tracking = not self.is_tracking
                    
                    # elif fo.get_kid_name() == "q":
                    #     break

                    await asyncio.sleep(0.001)
                except Exception as e:
                    print("Loop error:", e)
                    await asyncio.sleep(0.5)
                    continue
        except Exception as e:
            print("Error:", e)
        finally:
            print("Process loop stopped unexpectedly. Restarting...")
            # print("Auto-saving results...")
            # cv2.destroyAllWindows()
            # self.save_results()
            # print("Analysis complete! Results saved.")
            


async def main():

    uri = "ws://" + fo.get_connected_ip() + ":8765"
    # uri = "ws://10.10.7.91:8765"
    print(f"Attempting to connect to Raspberry Pi at {uri}...")

    analyzer = RealTimeAttentionAnalyzer()

    while True:
        try:
            print("Waiting for Raspberry Pi connection...")

            async with websockets.connect(uri) as websocket:
                print("Connected")

                await asyncio.gather(
                    receiver(websocket, analyzer),
                    analyzer.process_loop(),
                    sender(websocket, analyzer)
                )

        except Exception as e:
            print("Connection lost. Reconnecting...", e)
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
