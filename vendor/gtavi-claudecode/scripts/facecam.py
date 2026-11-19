"""Find the streamer's webcam box in a video.

usage: python facecam.py <video> [--start S --end E] [--json out.json] [--debug out.jpg]
importable: find_cam(video, start=None, end=None) -> dict

Returns one of
  {"mode":"cam",  "box":[x,y,w,h] (fractions of the frame), "face":[x,y,w,h], "confidence":0..1, "reason":...}
  {"mode":"face", "box":[...], ...}   no clean rectangle, tight 16:9-ish crop around the face
  {"mode":"none", "reason":...}       no stable face: callers should fall back to the blur layout
Fractions plug straight into cut.py --cam x:y:w:h.

Method: YuNet face detection on ~12 sampled frames, keep the face cluster that stays at the same spot in most
frames (in-game faces move). Then grow a rectangle around that face using a median-of-frames edge map:
the webcam border is a straight, static line, so its edge response survives the median while gameplay edges blur out.
"""
import argparse, json, os, subprocess, sys, urllib.request
from pathlib import Path

import cv2
import numpy as np

MODEL_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
MODEL = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".cache")) / "gtavi-claudecode" / "models" / "face_detection_yunet_2023mar.onnx"
N_FRAMES = 12
MAX_W = 1280  # analysis width


def model_path():
    if not MODEL.exists() or MODEL.stat().st_size < 100_000:
        MODEL.parent.mkdir(parents=True, exist_ok=True)
        tmp = MODEL.with_suffix(".part")
        urllib.request.urlretrieve(MODEL_URL, tmp)
        tmp.replace(MODEL)
    return str(MODEL)


def duration(video):
    cap = cv2.VideoCapture(str(video))
    n = cap.get(cv2.CAP_PROP_FRAME_COUNT); fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.release()
    return n / fps if n > 0 else 0


def sample_frames(video, start, end, n=N_FRAMES):
    """Grab n frames evenly across [start,end] with cv2 (seek by time)."""
    dur = duration(video)
    s = max(0.0, start or 0.0)
    e = min(end if end is not None else dur, dur) if dur else (end or s + 20)
    if e <= s:
        e = s + 1
    cap = cv2.VideoCapture(str(video))
    frames = []
    for i in range(n):
        t = s + (e - s) * (i + 0.5) / n
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        if ok and f is not None:
            h, w = f.shape[:2]
            if w > MAX_W:
                f = cv2.resize(f, (MAX_W, int(h * MAX_W / w)), interpolation=cv2.INTER_AREA)
            frames.append(f)
    cap.release()
    return frames


def detect_faces(frames):
    det = cv2.FaceDetectorYN.create(model_path(), "", (320, 320), 0.7, 0.3, 5000)
    out = []
    for f in frames:
        h, w = f.shape[:2]
        det.setInputSize((w, h))
        _, faces = det.detect(f)
        out.append([] if faces is None else [tuple(map(float, r[:4])) + (float(r[14]),) for r in faces])
    return out


def iou(a, b):
    ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    iw = max(0, min(ax2, bx2) - max(a[0], b[0])); ih = max(0, min(ay2, by2) - max(a[1], b[1]))
    inter = iw * ih
    return inter / (a[2] * a[3] + b[2] * b[3] - inter + 1e-9)


def stable_face(dets, n):
    """Cluster detections by position; return (median face box, hits) of the best stable cluster."""
    best = None
    flat = [(i, d) for i, ds in enumerate(dets) for d in ds]
    for _, seed in flat:
        members = {}
        for i, d in flat:
            # same webcam face: centre within ~1.3 face widths (streamers sway) and similar size
            dx = (seed[0] + seed[2] / 2) - (d[0] + d[2] / 2); dy = (seed[1] + seed[3] / 2) - (d[1] + d[3] / 2)
            if (dx * dx + dy * dy) ** 0.5 < 1.3 * max(seed[2], d[2]) and 0.6 < d[2] / seed[2] < 1.67:
                if i not in members or d[4] > members[i][4]:
                    members[i] = d
        if best is None or len(members) > len(best):
            best = members
    if not best:
        return None, 0
    arr = np.array(list(best.values()))
    return np.median(arr[:, :4], axis=0), len(best)


def edge_map(frames):
    """Median over frames of gradient magnitude per frame: keeps only static edges."""
    gs = []
    for f in frames:
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        g = cv2.GaussianBlur(g, (3, 3), 0)
        gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
        gs.append((gx, gy))
    mx = np.median(np.abs([a for a, _ in gs]), axis=0)
    my = np.median(np.abs([b for _, b in gs]), axis=0)
    # edges are 2-3 px thick after scaling: take the max over 1 px neighbours across the edge direction
    mx = np.maximum(mx, np.maximum(np.roll(mx, 1, 1), np.roll(mx, -1, 1)))
    my = np.maximum(my, np.maximum(np.roll(my, 1, 0), np.roll(my, -1, 0)))
    return mx, my


def find_rect(frames, face):
    """Expand from the face outward to the strongest static straight edges on each side.
    Returns (x0,y0,x1,y1, score) or None. Static edges: vertical lines (|gx|) for left/right, horizontal (|gy|) for top/bottom."""
    h, w = frames[0].shape[:2]
    gx, gy = edge_map(frames)
    fx, fy, fw, fh = face
    cx, cy = fx + fw / 2, fy + fh / 2
    # also demand the line to be temporally static in intensity (low variance across frames) along its length
    gray = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]).astype(np.float32)
    # the cam interior (face) is also dynamic, so static means: the edge exists in the median, with a long run
    thr_v = max(20.0, np.percentile(gx, 99.0) * 0.35)
    thr_h = max(20.0, np.percentile(gy, 99.0) * 0.35)

    def run_len(line_mask):
        # longest continuous run (allowing small gaps) in a 1-D boolean array
        best = cur = gap = 0
        for v in line_mask:
            if v:
                cur += 1 + gap; gap = 0; best = max(best, cur)
            elif cur and gap < 4:
                gap += 1
            else:
                cur = gap = 0
        return best

    # Candidate extents: face-relative search windows
    def search(axis_edges, lo, hi, other_lo, other_hi, thr, vertical):
        """Best static edge position in [lo,hi) judged over the span [other_lo,other_hi)."""
        cands = []
        for p in range(max(lo, 1), min(hi, (w if vertical else h) - 1)):
            sl = axis_edges[other_lo:other_hi, p] if vertical else axis_edges[p, other_lo:other_hi]
            m = sl > thr
            if m.mean() < 0.4:
                continue
            frac = run_len(m) / max(1, other_hi - other_lo)
            if frac < 0.4:  # a real border is one long straight line, not text or furniture
                continue
            cands.append((p, frac * float(sl.mean())))
        if not cands:
            return None, 0
        top = max(sc for _, sc in cands)
        # near-best lines: take the outermost (the webcam frame is outside inner furniture lines)
        strong = [(p, sc) for p, sc in cands if sc >= 0.9 * top]
        ref = cx if vertical else cy
        after = lo > ref
        return max(strong, key=lambda t: t[0] if after else -t[0])

    # span used to judge vertical lines: the face's height band extended; horizontal lines: face's width band
    ys0, ys1 = int(max(0, cy - fh * 2.5)), int(min(h, cy + fh * 2.5))
    xs0, xs1 = int(max(0, cx - fw * 4)), int(min(w, cx + fw * 4))
    # sides limited to sane webcam size: box between 1.6x and 8x face width
    def sides(ys0, ys1, xs0, xs1):
        return (search(gx, int(cx - fw * 10), int(fx - fw * 0.1), ys0, ys1, thr_v, True),
                search(gx, int(fx + fw * 1.1), int(cx + fw * 10), ys0, ys1, thr_v, True),
                search(gy, int(cy - fh * 4.5), int(fy - fh * 0.1), xs0, xs1, thr_h, False),
                search(gy, int(fy + fh * 1.1), int(cy + fh * 4.5), xs0, xs1, thr_h, False))
    (L, sL), (R, sR), (T, sT), (B, sB) = sides(ys0, ys1, xs0, xs1)
    # refine: judge each line over the full extent of the box found so far (overlays and room furniture do not span it)
    for _ in range(2):
        if None in (L, R, T, B):
            break
        (L2, sL), (R2, sR), (T2, sT), (B2, sB) = sides(T, B, L, R)
        L, R, T, B = (L2 if L2 is not None else L), (R2 if R2 is not None else R), (T2 if T2 is not None else T), (B2 if B2 is not None else B)
    # frame borders count as edges (cam docked to a corner)
    notes = []
    if L is None and fx - fw * 10 < 3: L = 0; sL = 1; notes.append("L=frame")
    if R is None and cx + fw * 10 > w - 3: R = w; sR = 1; notes.append("R=frame")
    if T is None and cy - fh * 4.5 < 3: T = 0; sT = 1; notes.append("T=frame")
    if B is None and cy + fh * 4.5 > h - 3: B = h; sB = 1; notes.append("B=frame")
    found = [x is not None for x in (L, R, T, B)]
    weak = [n for n, s, t in (("L", sL, thr_v), ("R", sR, thr_v), ("T", sT, thr_h), ("B", sB, thr_h)) if s < 0.9 * t]
    return dict(L=L, R=R, T=T, B=B, found=found, notes=notes, weak=len(weak))


def refine_with_frame_edges(rect, w, h, face):
    """If cam is docked to a frame edge, snap sides that are within a few px or close to the frame edge."""
    return rect


def where(box):
    x, y, bw, bh = box
    cx, cy = x + bw / 2, y + bh / 2
    v = "top" if cy < 0.4 else "bottom" if cy > 0.6 else "middle"
    hz = "left" if cx < 0.4 else "right" if cx > 0.6 else "center"
    return f"{v}-{hz} {round(bw * 100)}% x {round(bh * 100)}%"


def find_cam(video, start=None, end=None):
    frames = sample_frames(video, start, end)
    if len(frames) < 4:
        return {"mode": "none", "confidence": 0.0, "reason": f"could only read {len(frames)} frames"}
    h, w = frames[0].shape[:2]
    dets = detect_faces(frames)
    face, hits = stable_face(dets, len(frames))
    need = max(3, int(len(frames) * 0.5))
    total = sum(len(d) for d in dets)
    if face is None or hits < need:
        return {"mode": "none", "confidence": 0.0, "faces_seen": total,
                "reason": f"no face stable across frames (best cluster {hits}/{len(frames)}, need {need})"}
    fx, fy, fw, fh = face
    fracface = [round(fx / w, 4), round(fy / h, 4), round(fw / w, 4), round(fh / h, 4)]
    if fw / w > 0.5:
        return {"mode": "none", "confidence": 0.0, "face": fracface,
                "reason": "stable face is huge (full-frame talking head, not a webcam overlay)"}
    stab = hits / len(frames)

    r = find_rect(frames, face)
    L, R, T, B = r["L"], r["R"], r["T"], r["B"]
    n_found = sum(r["found"])
    # snap sides near frame borders
    m = 0.01 * w
    if L is not None and L < m: L = 0
    if R is not None and R > w - m: R = w
    if T is not None and T < 0.01 * h: T = 0
    if B is not None and B > h - 0.01 * h: B = h
    ok = L is not None and R is not None and T is not None and B is not None
    if ok:
        bw, bh = R - L, B - T
        # sane webcam: smaller than 60% of frame width/height, contains the face
        contains = L <= fx and R >= fx + fw and T <= fy and B >= fy + fh
        sane = 0.08 < bw / w < 0.6 and 0.08 < bh / h < 0.7 and contains and bw > fw * 1.2 and bh > fh * 1.2
        if sane:
            box = [round(L / w, 4), round(T / h, 4), round(bw / w, 4), round(bh / h, 4)]
            conf = round(min(1.0, 0.55 + 0.25 * stab + 0.2 * (1 if n_found == 4 else 0.5)), 2)
            return {"mode": "cam", "box": box, "face": fracface, "confidence": conf,
                    "reason": f"face stable in {hits}/{len(frames)} frames, rectangle edges found on {n_found}/4 sides {r['notes']}",
                    "summary": f"cam: {where(box)}"}
    # fallback: tight 16:9 crop around the face (about 3x face width)
    cw = min(w, fw * 3.2); ch = cw * 9 / 16
    if ch < fh * 1.8:
        ch = fh * 1.8; cw = ch * 16 / 9
    ccx, ccy = fx + fw / 2, fy + fh * 0.55
    x0 = min(max(0, ccx - cw / 2), w - cw); y0 = min(max(0, ccy - ch / 2), h - ch)
    box = [round(x0 / w, 4), round(y0 / h, 4), round(cw / w, 4), round(ch / h, 4)]
    conf = round(min(0.8, 0.35 + 0.4 * stab), 2)
    return {"mode": "face", "box": box, "face": fracface, "confidence": conf,
            "reason": f"face stable in {hits}/{len(frames)} frames but no clean rectangle ({n_found}/4 sides found); face-centred crop",
            "summary": f"face (no cam border): {where(box)}"}


def draw_debug(video, res, out, start=None, end=None):
    frames = sample_frames(video, start, end, 3)
    if not frames:
        return
    f = frames[len(frames) // 2].copy()
    h, w = f.shape[:2]
    if res.get("box"):
        x, y, bw, bh = res["box"]
        col = (0, 255, 0) if res["mode"] == "cam" else (0, 200, 255)
        cv2.rectangle(f, (int(x * w), int(y * h)), (int((x + bw) * w), int((y + bh) * h)), col, 4)
    if res.get("face"):
        x, y, bw, bh = res["face"]
        cv2.rectangle(f, (int(x * w), int(y * h)), (int((x + bw) * w), int((y + bh) * h)), (255, 0, 0), 2)
    cv2.putText(f, f"{res['mode']} conf={res.get('confidence')}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 255), 3)
    cv2.imwrite(str(out), f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--start", type=float); ap.add_argument("--end", type=float)
    ap.add_argument("--json"); ap.add_argument("--debug", help="write a JPG with the box drawn")
    a = ap.parse_args()
    res = find_cam(a.video, a.start, a.end)
    if res["mode"] == "none":
        line = f"no webcam found ({res['reason']}) -> use the blur layout"
    else:
        line = f"{res['summary']} (confidence {res['confidence']}; {res['reason']}) -> --cam {':'.join(f'{v:.3f}' for v in res['box'])}"
    print(line)
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1), encoding="utf-8")
    if a.debug:
        draw_debug(a.video, res, a.debug, a.start, a.end)


if __name__ == "__main__":
    main()


