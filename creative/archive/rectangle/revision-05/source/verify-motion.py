#!/usr/bin/env python3
"""Verify the actual revision-05 exports with Python stdlib and FFmpeg.

Run after both encoders finish:
    python3 creative/archive/rectangle/revision-05/source/verify-motion.py

--geometry-only checks the flight manifest without touching final-qa.json.
The automatic result deliberately leaves perceptual and physical-device review
separate. Contact sheets contain frames decoded from the delivered MP4 files.
"""

import argparse
import array
import hashlib
import json
import math
import struct
import subprocess
import sys
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REVIEW = ROOT / "review"
EXPECTED = ((120, "JJIntern-revision05-120fps-master.mp4"),
            (60, "JJIntern-revision05-60fps.mp4"))


def run(args, binary=False):
    result = subprocess.run(args, capture_output=True, text=not binary)
    if result.returncode:
        error = result.stderr.decode(errors="replace") if binary else result.stderr
        raise RuntimeError(f"{args[0]} failed ({result.returncode}): {error[-5000:]}")
    return result


def probe(path, *args):
    return json.loads(run(["ffprobe", "-v", "error", *args, "-of", "json", str(path)]).stdout)


def ffmpeg(*args, binary=False):
    return run(["ffmpeg", "-hide_banner", "-nostdin", "-threads", "2", *map(str, args)], binary)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check(checks, name, passed, evidence):
    checks.append({"check": name, "passed": bool(passed), "evidence": evidence})


def geometry():
    data = json.loads((REVIEW / "flight-positions.json").read_text())
    scene, positions = data["scene"], data["positions"]
    packet = scene["packet"]
    x0, x1 = packet["startX"], packet["endX"]
    checks = []
    check(checks, "flight spans exactly 4.5 to 6.5 seconds",
          scene["flight"]["start"] == 4.5 and scene["flight"]["end"] == 6.5,
          scene["flight"])
    check(checks, "120 fps flight is frames 540..779; arrival is frame 780",
          [p["frame"] for p in positions] == list(range(540, 781)),
          {"flight_first": 540, "flight_last": 779, "arrival": 780,
           "samples_including_arrival": len(positions)})
    check(checks, "60 fps flight is frames 270..389; arrival is frame 390",
          [p["frame"] // 2 for p in positions[::2]] == list(range(270, 391)),
          {"flight_first": 270, "flight_last": 389, "arrival": 390,
           "method": "every second source frame"})
    errors, velocity_errors, time_errors = [], [], []
    for p in positions:
        u = (p["frame"] / 120 - 4.5) / 2
        errors.append(abs(p["x"] - (x0 + (x1 - x0) * (.12 * u + .88 * u ** 3))))
        velocity_errors.append(abs(p["velocity"] - (x1 - x0) / 2 * (.12 + 2.64 * u ** 2)))
        time_errors.append(abs(p["t"] - p["frame"] / 120))
    check(checks, "samples match specified cubic position and derivative",
          max(errors + velocity_errors + time_errors) < 1e-8,
          {"max_position_error_px": max(errors), "max_velocity_error_px_s": max(velocity_errors),
           "max_time_error_s": max(time_errors), "formula": "x0+(x1-x0)*(0.12*u+0.88*u^3)"})
    check(checks, "position and speed strictly increase through arrival",
          x1 > x0 and all(b["x"] > a["x"] and b["velocity"] > a["velocity"]
                         for a, b in zip(positions, positions[1:])) and positions[0]["velocity"] > 0,
          {"start_x": x0, "arrival_x": x1, "start_speed_px_s": positions[0]["velocity"],
           "arrival_speed_px_s": positions[-1]["velocity"]})
    check(checks, "packet leading edge reaches contact coordinate at arrival",
          abs(x1 + packet["width"] - packet["leadingEdgeAtContact"]) < 1e-8,
          {"packet_width": packet["width"], "arrival_leading_edge": x1 + packet["width"],
           "contact_coordinate": packet["leadingEdgeAtContact"]})
    check(checks, "scene declares stationary camera", scene["flight"]["cameraTracking"] is False,
          "Source declaration, corroborated separately by encoded screen-space motion tracking.")
    return {"checks": checks, "passed": all(c["passed"] for c in checks), "scene": scene}


def atoms(path):
    result = []
    with path.open("rb") as file:
        end = path.stat().st_size
        while file.tell() + 8 <= end:
            start = file.tell()
            size, kind = struct.unpack(">I4s", file.read(8))
            if size == 1:
                size = struct.unpack(">Q", file.read(8))[0]
            elif size == 0:
                size = end - start
            if size < 8 or start + size > end:
                raise ValueError("Invalid MP4 atom size")
            result.append({"type": kind.decode("ascii", errors="replace"), "offset": start, "bytes": size})
            file.seek(start + size)
    return result


def audio_analysis(path):
    analysis = ffmpeg("-v", "info", "-i", path, "-map", "0:a:0", "-af",
                      "loudnorm=I=-16:TP=-1:LRA=9:print_format=json", "-f", "null", "-").stderr
    start, end = analysis.rfind("{"), analysis.rfind("}")
    loudness = json.loads(analysis[start:end + 1])
    pcm = ffmpeg("-v", "error", "-i", path, "-map", "0:a:0", "-f", "f32le", "-acodec",
                 "pcm_f32le", "-", binary=True).stdout
    samples = array.array("f")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    peak = max(abs(s) for s in samples)
    return {"integrated_lufs": float(loudness["input_i"]),
            "true_peak_dbtp": float(loudness["input_tp"]),
            "loudness_range_lu": float(loudness["input_lra"]),
            "sample_peak_dbfs": 20 * math.log10(peak) if peak else None,
            "clipped_interleaved_samples": sum(abs(s) >= 1 for s in samples),
            "decoded_samples_per_channel": len(samples) // 2,
            "untrimmed_decoder_duration_s": len(samples) / (2 * 48000),
            "first_stereo_sample": list(samples[:2]), "last_stereo_sample": list(samples[-2:]),
            "duration_note": "MP4 presentation duration is checked separately; AAC may return a padded final codec block."}


def screen_flight(path, fps, scene):
    """Track the narrow leading stripe in decoded pixels, independent of metadata."""
    first, arrival = round(4.5 * fps), round(6.5 * fps)
    # This band avoids content bars and the horizontal connector. Color gating
    # excludes the pale pressure arc. The rightmost blue component is the stripe.
    crop_y, crop_height = 924, 16
    pixels = ffmpeg("-v", "error", "-i", path, "-an", "-vf",
                    f"select='between(n,{first},{arrival})',crop=1080:{crop_height}:0:{crop_y}",
                    "-fps_mode", "passthrough", "-pix_fmt", "rgb24", "-f", "rawvideo", "-",
                    binary=True).stdout
    size = 1080 * crop_height * 3
    observed = []
    for offset in range(0, len(pixels), size):
        frame = pixels[offset:offset + size]
        weights = [0] * 1080
        for i in range(0, len(frame), 3):
            r, g, b = frame[i:i + 3]
            weights[(i // 3) % 1080] += max(0, min(b - r - 70, g - r - 45))
        if not max(weights):
            raise ValueError("Packet leading stripe not detected in encoded flight frame")
        threshold = .15 * max(weights)
        right = max(i for i, value in enumerate(weights) if value >= threshold)
        left = right
        while left > 0 and weights[left - 1] > 0:
            left -= 1
        while right < 1079 and weights[right + 1] > 0:
            right += 1
        observed.append(sum(x * weights[x] for x in range(left, right + 1)) / sum(weights[left:right + 1]))
    expected = []
    for frame in range(first, arrival + 1):
        u = (frame / fps - 4.5) / 2
        expected.append((scene["packet"]["endX"] - scene["packet"]["startX"]) * (.12 * u + .88 * u ** 3))
    relative = [x - observed[0] for x in observed]
    errors = [actual - theoretical for actual, theoretical in zip(relative, expected)]
    stride = fps // 6  # 1/6-second speed windows smooth subpixel/codec quantization.
    speeds = [(observed[i + stride] - observed[i]) / (stride / fps)
              for i in range(0, len(observed) - stride, stride)]
    frame_steps = [b - a for a, b in zip(observed, observed[1:])]
    return {"method": "Blue-weighted centroid of rightmost narrow blue stripe in 16 decoded RGB rows; pale pressure arc excluded",
            "crop": [0, crop_y, 1080, crop_height], "first_frame": first, "last_frame": arrival,
            "sample_count": len(observed), "expected_sample_count": arrival - first + 1,
            "observed_displacement_px": relative[-1], "expected_displacement_px": expected[-1],
            "max_relative_position_error_px": max(abs(e) for e in errors),
            "rms_relative_position_error_px": math.sqrt(sum(e * e for e in errors) / len(errors)),
            "minimum_frame_step_px": min(frame_steps), "speed_window_s": stride / fps,
            "window_speeds_px_s": speeds, "centroid_x_by_frame": observed,
            "codec_tolerance": "Relative error below1px; individual subpixel centroid jitter up to0.25px allowed; all1/6s speed windows must be positive and strictly increasing",
            "passed": len(observed) == arrival - first + 1 and max(abs(e) for e in errors) < 1
                      and min(frame_steps) > -.25 and min(speeds) > 0
                      and all(b > a for a, b in zip(speeds, speeds[1:]))}


def decoded_frames(path, fps):
    times = [0, .6, 2.9, 3.3, 3.7, 4.1, 4.5 - 1 / fps, 4.5, 5, 5.5, 6,
             6.5 - 1 / fps, 6.5, 6.65, 6.8, 7.1, 9.9, 10.3, 10.8, 11.3,
             15 - 1 / fps, 15, 15.4, 18 - 1 / fps]
    frames = [round(t * fps) for t in times]
    expression = "+".join(f"eq(n,{n})" for n in frames)
    pattern = REVIEW / f"encoded-{fps}-frame-%02d.png"
    ffmpeg("-v", "error", "-y", "-i", path, "-an", "-vf", f"select='{expression}'",
           "-fps_mode", "passthrough", "-start_number", "0", pattern)
    records = [{"index": i, "frame": frame, "time_s": frame / fps,
                "path": str(REVIEW / f"encoded-{fps}-frame-{i:02d}.png")}
               for i, frame in enumerate(frames)]
    boards = []
    for start in range(0, len(records), 4):
        batch = records[start:start + 4]
        board = REVIEW / f"encoded-{fps}-board-{start // 4 + 1}.png"
        labels = REVIEW / f"encoded-{fps}-labels-{start // 4 + 1}.ppm"
        bitmap_labels(labels, batch)
        filters = (f"[0:v]scale=360:640:flags=lanczos,tile={len(batch)}x1:nb_frames={len(batch)}"
                   ":padding=0:margin=0[b];[b][1:v]vstack=inputs=2")
        ffmpeg("-v", "error", "-y", "-framerate", "1", "-start_number", str(start),
               "-i", pattern, "-i", labels, "-filter_complex", filters, "-frames:v", "1", board)
        labels.unlink()
        boards.append(str(board))
    return records, boards


def bitmap_labels(path, batch):
    """Tiny PPM footer avoids optional FFmpeg drawtext/Pillow dependencies."""
    glyphs = {
        "0": [14, 17, 19, 21, 25, 17, 14], "1": [4, 12, 4, 4, 4, 4, 14],
        "2": [14, 17, 1, 2, 4, 8, 31], "3": [30, 1, 1, 14, 1, 1, 30],
        "4": [2, 6, 10, 18, 31, 2, 2], "5": [31, 16, 16, 30, 1, 1, 30],
        "6": [14, 16, 16, 30, 17, 17, 14], "7": [31, 1, 2, 4, 8, 8, 8],
        "8": [14, 17, 17, 14, 17, 17, 14], "9": [14, 17, 17, 15, 1, 1, 14],
        ".": [0, 0, 0, 0, 0, 6, 6], "S": [15, 16, 16, 14, 1, 1, 30],
        "F": [31, 16, 16, 30, 16, 16, 16], "/": [1, 1, 2, 4, 8, 16, 16],
        " ": [0] * 7,
    }
    width, height = 360 * len(batch), 30
    data = bytearray([32, 49, 69] * width * height)
    for cell, item in enumerate(batch):
        label = f"{item['time_s']:.6f} S / F{item['frame']}"
        for index, char in enumerate(label):
            for y, bits in enumerate(glyphs[char]):
                for x in range(5):
                    if bits & (1 << (4 - x)):
                        for dy in range(2):
                            for dx in range(2):
                                px, py = cell * 360 + 10 + index * 12 + x * 2 + dx, 8 + y * 2 + dy
                                offset = (py * width + px) * 3
                                data[offset:offset + 3] = b"\xff\xff\xff"
    path.write_bytes(f"P6\n{width} {height}\n255\n".encode() + data)


def frame_delta(first, second):
    crops = []
    for path in (first, second):
        crops.append(ffmpeg("-v", "error", "-i", path, "-vf", "crop=1080:460:0:730",
                            "-pix_fmt", "rgb24", "-f", "rawvideo", "-", binary=True).stdout)
    diffs = [abs(a - b) for a, b in zip(*crops)]
    return {"crop": [0, 730, 1080, 460], "mean_absolute_rgb_delta_0_255": sum(diffs) / len(diffs),
            "maximum_channel_delta": max(diffs),
            "channel_fraction_changing_more_than_8": sum(d > 8 for d in diffs) / len(diffs),
            "method": "Pixel differences in central action crop; complements screen-space tracking and visual inspection."}


def verify_export(path, fps, scene):
    checks = []
    media = probe(path, "-show_streams", "-show_format")
    videos = [s for s in media["streams"] if s["codec_type"] == "video"]
    audios = [s for s in media["streams"] if s["codec_type"] == "audio"]
    if len(videos) != 1 or len(audios) != 1:
        raise ValueError("Expected exactly one video and one audio stream")
    video, audio = videos[0], audios[0]
    check(checks, "1080x1920 H.264 yuv420p", video["width"] == 1080 and video["height"] == 1920
          and video["codec_name"] == "h264" and video["pix_fmt"] == "yuv420p",
          {k: video.get(k) for k in ("width", "height", "codec_name", "profile", "level", "pix_fmt")})
    check(checks, "BT.709 limited-range tagging", all(video.get(k) == "bt709" for k in
          ("color_space", "color_transfer", "color_primaries")) and video.get("color_range") == "tv",
          {k: video.get(k) for k in ("color_space", "color_transfer", "color_primaries", "color_range")})
    check(checks, "declared frame rate", Fraction(video["r_frame_rate"]) == fps
          and Fraction(video["avg_frame_rate"]) == fps,
          {"r_frame_rate": video["r_frame_rate"], "avg_frame_rate": video["avg_frame_rate"]})
    check(checks, "exact 18.000-second presentation", all(abs(float(item["duration"]) - 18) < 1e-6
          for item in (media["format"], video, audio)),
          {"container_duration": media["format"]["duration"], "video_duration": video["duration"],
           "audio_duration": audio["duration"]})
    check(checks, "48 kHz stereo AAC", audio["codec_name"] == "aac" and int(audio["sample_rate"]) == 48000
          and audio["channels"] == 2, {k: audio.get(k) for k in ("codec_name", "sample_rate", "channels", "channel_layout")})
    structure = atoms(path)
    atom_names = [a["type"] for a in structure]
    check(checks, "faststart moov precedes mdat", "moov" in atom_names and "mdat" in atom_names
          and atom_names.index("moov") < atom_names.index("mdat"), structure)
    frame_data = probe(path, "-select_streams", "v:0", "-show_frames", "-show_entries",
                       "frame=best_effort_timestamp_time")
    pts = [float(f["best_effort_timestamp_time"]) for f in frame_data["frames"]]
    max_pts_error = max(abs(t - i / fps) for i, t in enumerate(pts))
    check(checks, "decoded frame count and constant timestamps", len(pts) == 18 * fps and max_pts_error < 1e-6,
          {"decoded_frames": len(pts), "expected_frames": 18 * fps, "first_pts": pts[0], "last_pts": pts[-1],
           "maximum_pts_error_s": max_pts_error, "arrival_frame": round(6.5 * fps),
           "arrival_pts": pts[round(6.5 * fps)]})
    decoded = ffmpeg("-v", "error", "-xerror", "-i", path, "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-")
    check(checks, "complete audio/video decode without errors", not decoded.stderr.strip(), decoded.stderr or "No decoder errors")
    audio_result = audio_analysis(path)
    check(checks, "encoded AAC below digital and true-peak clipping", audio_result["clipped_interleaved_samples"] == 0
          and audio_result["sample_peak_dbfs"] < 0 and audio_result["true_peak_dbtp"] < 0, audio_result)
    observed = screen_flight(path, fps, scene)
    check(checks, "decoded packet follows accelerating screen-space path", observed["passed"],
          {k: v for k, v in observed.items() if k not in ("centroid_x_by_frame", "passed")})
    records, boards = decoded_frames(path, fps)
    at = {r["frame"]: r["path"] for r in records}
    boundary = frame_delta(at[round(4.5 * fps) - 1], at[round(4.5 * fps)])
    check(checks, "compression-to-flight boundary has no large raster discontinuity",
          boundary["mean_absolute_rgb_delta_0_255"] < 2, boundary)
    final_hold = frame_delta(at[round(15.4 * fps)], at[18 * fps - 1])
    check(checks, "final sign-off remains stable through last frame", final_hold["mean_absolute_rgb_delta_0_255"] < 1, final_hold)
    reference_comparisons = []
    for label, time, name in (("source", .6, "0.600s.png"), ("logo", 7.1, "7.100s.png")):
        reference = ROOT / "stills" / name
        fidelity = frame_delta(reference, at[round(time * fps)])
        fidelity["reference_path"] = str(reference)
        fidelity["reference_sha256"] = sha256(reference)
        fidelity["encoded_frame"] = round(time * fps)
        fidelity["reference_kind"] = label
        fidelity["interpretation"] = "Measurement only: RGB-to-limited-range YUV420 encoding and decoding are lossy; RGB identity is not required. Inspect the decoded image alongside source."
        reference_comparisons.append(fidelity)
    return {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size,
            "passed": all(c["passed"] for c in checks), "checks": checks,
            "flight_pixel_tracking": observed, "decoded_review_frames": records, "contact_sheets": boards,
            "source_to_encoded_measurements": reference_comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry-only", action="store_true")
    args = parser.parse_args()
    flight = geometry()
    if args.geometry_only:
        print(json.dumps(flight, indent=2))
        return 0 if flight["passed"] else 1
    missing = [name for _, name in EXPECTED if not (ROOT / name).is_file()]
    if missing:
        parser.error("Wait for the final render to finish; missing: " + ", ".join(missing))
    report = {"schema_version": "1.0", "review_date": "2026-10-17", "timezone": "Europe/Stockholm",
              "method": "Actual MP4 metadata, full decode, decoded pixels, PCM and loudness; no visual pass inferred from source",
              "source_sha256": sha256(ROOT / "source" / "motion.html"), "geometry": flight, "exports": [],
              "perceptual_review": {"status": "pending separate inspection", "performed": [],
                                    "pending": ["Inspect decoded contact sheets for composition, text and final frame",
                                                "Review digital 360px equivalent for reading and muted comprehension",
                                                "Subjective listening on headphones or speakers"]},
              "external_release_checks_pending": ["Physical phone playback", "Actual platform upload preview",
                                                  "Final campaign rights confirmation"],
              "publication": "Not performed or authorized by this verifier"}
    requirements = json.loads((REVIEW / "requirements.json").read_text())
    workspace = ROOT.parents[3]
    original_logo = workspace / requirements["logo"]["path"]
    report["logo_integrity"] = {"path": str(original_logo), "sha256": sha256(original_logo),
                                "expected_sha256": requirements["logo"]["sha256"],
                                "passed": sha256(original_logo) == requirements["logo"]["sha256"]}
    for fps, name in EXPECTED:
        print(f"Verifying {name}", flush=True)
        try:
            report["exports"].append(verify_export(ROOT / name, fps, flight["scene"]))
        except Exception as error:
            report["exports"].append({"path": str(ROOT / name), "passed": False, "error": str(error)})
    wav = ROOT / "audio" / "jjintern-revision-05-original-score.wav"
    raw_media = probe(wav, "-show_streams", "-show_format")
    raw_audio = audio_analysis(wav)
    raw_audio["presentation_duration_s"] = float(raw_media["format"]["duration"])
    raw_audio["passed"] = raw_audio["presentation_duration_s"] == 18 and raw_audio["decoded_samples_per_channel"] == 864000 \
        and raw_audio["clipped_interleaved_samples"] == 0 and raw_audio["true_peak_dbtp"] < 0
    report["raw_score"] = raw_audio
    report["automated_passed"] = flight["passed"] and report["logo_integrity"]["passed"] and raw_audio["passed"] \
        and all(e["passed"] for e in report["exports"])
    report["artifact_status"] = "Automated checks passed; perceptual review separate" if report["automated_passed"] else "Automated checks require attention"
    target = REVIEW / "final-qa.json"
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"automated_passed": report["automated_passed"], "report": str(target),
                      "exports": [{"path": e["path"], "passed": e["passed"], "error": e.get("error")}
                                  for e in report["exports"]]}, indent=2))
    return 0 if report["automated_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
