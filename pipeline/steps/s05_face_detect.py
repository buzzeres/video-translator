from __future__ import annotations
import logging
from pipeline.context import PipelineContext, StepSkippedException

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> None:
    if not ctx.request.lip_sync:
        raise StepSkippedException("lip_sync disabled")
    try:
        import mediapipe as mp
        import cv2
    except ImportError:
        raise StepSkippedException("mediapipe or opencv not installed")

    mp_face = mp.solutions.face_detection
    face_tracks: list[dict] = []
    face_id_map: dict[int, str] = {}
    next_id = [0]

    cap = cv2.VideoCapture(str(ctx.video_path))
    fps = ctx.video_metadata.get("fps", 25.0)
    frame_idx = 0

    with mp_face.FaceDetection(min_detection_confidence=0.5) as detector:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = detector.process(rgb)
            if results.detections:
                for det in results.detections:
                    bbox = det.location_data.relative_bounding_box
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    bw = int(bbox.width * w)
                    bh = int(bbox.height * h)
                    face_id = _assign_face_id(face_id_map, next_id, x, y, bw, bh)
                    face_tracks.append({
                        "frame_idx": frame_idx,
                        "time": frame_idx / fps,
                        "face_id": face_id,
                        "bbox": (x, y, bw, bh),
                    })
            frame_idx += 1

    cap.release()
    ctx.face_tracks = face_tracks
    logger.info(f"Face detection: {frame_idx} frames, {len(set(t['face_id'] for t in face_tracks))} unique faces")


def _assign_face_id(id_map: dict, next_id: list, x: int, y: int, w: int, h: int) -> str:
    cx, cy = x + w // 2, y + h // 2
    for (ox, oy), fid in id_map.items():
        if abs(cx - ox) < 80 and abs(cy - oy) < 80:
            id_map[(cx, cy)] = fid
            return fid
    fid = f"FACE_{next_id[0]:02d}"
    next_id[0] += 1
    id_map[(cx, cy)] = fid
    return fid
