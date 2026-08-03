# gaze_controller.py
import cv2
import numpy as np
from collections import deque
from eyetrax import GazeEstimator, run_9_point_calibration
from eyetrax.calibration import (
    run_9_point_calibration,
)
from eyetrax.cli import parse_common_args
from eyetrax.filters import KalmanSmoother, make_kalman
from eyetrax.gaze import GazeEstimator
import os

class GazeController:
    def __init__(self, model_file="gaze_model.pkl", camera_index=0):
        self.camera_index = camera_index
        self.estimator = GazeEstimator()

        run_9_point_calibration(self.estimator, camera_index=self.camera_index)

        # Kalman smoothing
        self.kalman = make_kalman()
        self.smoother = KalmanSmoother(self.kalman)
        self.smoother.tune(self.estimator, camera_index=self.camera_index)

        # Open webcam
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError("[GazeController] Could not open webcam.")

    def get_gaze(self):
        #Returns smoothed gaze coordinates (x, y) or (None, None
        ret, frame = self.cap.read()
        if not ret:
            return None, None

        features, blink = self.estimator.extract_features(frame)
        if features is None or blink:
            return None, None

        x, y = self.estimator.predict([features])[0]
        x, y = self.smoother.step(x, y)  # Kalman smoothing
        return int(x), int(y)


    def get_gaze_blink(self):
        ret, frame = self.cap.read()
        if not ret:
            return None, None, False

        features, blink = self.estimator.extract_features(frame)
        if features is None:
            return None, None, False

        x, y = self.estimator.predict([features])[0]
        x, y = self.smoother.step(x, y)
        return int(x), int(y), blink

    def release(self):
        if self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
