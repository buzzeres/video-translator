from __future__ import annotations
import logging
from pipeline.context import PipelineContext, StepSkippedException

logger = logging.getLogger(__name__)

UPPER_LIP = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409]
LOWER_LIP = [146, 91, 181, 84, 17, 314, 405, 321, 375, 291]


def run(ctx: PipelineContext) -> None:
    if not ctx.request.lip_sync:
        raise StepSkippedException("lip_sync disabled")
    try:
        import mediapipe as mp
        import cv2
        import numpy as np
    except ImportError:
        raise StepSkippedException("mediapipe or opencv not installed")

    mp_mesh = mp.solutions.face_mesh
    fps = ctx.video_metadata.get("fps", 25.0)
    landmarks_by_frame: dict[int, dict[str, float]] = {}

    cap = cv2.VideoCapture(str(ctx.video_path))
    frame_idx = 0

    with mp_mesh.FaceMesh(static_image_mode=False, max_num_faces=4, refine_landmarks=True) as mesh:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = mesh.process(rgb)
            frame_data: dict[str, float] = {}
            if results.multi_face_landmarks:
                for fi, face_lm in enumerate(results.multi_face_landmarks):
                    lms = face_lm.landmark
                    upper_y = np.mean([lms[i].y * h for i in UPPER_LIP])
                    lower_y = np.mean([lms[i].y * h for i in LOWER_LIP])
                    mouth_h = abs(lower_y - upper_y)
                    face_h = abs(lms[10].y - lms[152].y) * h
                    openness = mouth_h / face_h if face_h > 0 else 0.0
                    face_id = f"FACE_{fi:02d}"
                    frame_data[face_id] = float(openness)
            if frame_data:
                landmarks_by_frame[frame_idx] = frame_data
            frame_idx += 1

    cap.release()
    ctx.lip_landmarks = landmarks_by_frame
    logger.info(f"Lip landmarks extracted for {len(landmarks_by_frame)} frames")
