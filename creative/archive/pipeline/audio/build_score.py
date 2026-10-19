#!/usr/bin/env python3
"""A Clearer Signal: original 20 s JJIntern pipeline score.

All oscillators, percussion noise, transitions and reverberation are computed
here. No samples, recordings, loops, sampled IRs, vocals or external music AI.
Run with Python 3.13, numpy, scipy and ffmpeg on PATH.
"""
from pathlib import Path
import json
import re
import subprocess
import time
import wave

import numpy as np
from scipy import signal

START = time.perf_counter()
OUT = Path(__file__).resolve().parent
SR = 48000
SECS = 20.0
N = int(SR * SECS)
PI = np.pi
RNG = np.random.default_rng(730171026)
melody = np.zeros((N, 2))
harmony = np.zeros_like(melody)
drums = np.zeros_like(melody)
low = np.zeros_like(melody)
fx = np.zeros_like(melody)
posting_ding = np.zeros_like(melody)
duck = np.zeros(N)
events = []


def hz(note):
    return 440 * 2 ** ((note - 69) / 12)


def tt(length):
    return np.arange(round(length * SR)) / SR


def filt(x, cutoff, kind='lowpass', order=2):
    sos = signal.butter(order, cutoff, kind, fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=0)


def env(t, attack=.003, decay=.2, release=.03):
    return (1 - np.exp(-t / attack)) * np.exp(-t / decay) * np.clip((t[-1] - t) / release, 0, 1)


def add(bus, x, seconds, gain=1., pan=0., kind=None, note=None):
    at = round(seconds * SR)
    if x.ndim == 1:
        angle = (pan + 1) * PI / 4
        x = np.stack((x * np.cos(angle), x * np.sin(angle)), axis=1)
    count = min(N - at, len(x))
    if count > 0:
        bus[at:at + count] += x[:count] * gain
    if kind:
        event = {'s': round(seconds, 6), 'kind': kind, 'gain': gain, 'pan': pan}
        if note is not None:
            event['midi_note'] = note
        events.append(event)


def fm_glass(note, length=1.6, strength=1.):
    """Purpose-built posting tone: sine/FM strike plus tuned glass partials."""
    t = tt(length)
    f = hz(note)
    phase = 2 * PI * f * t
    x = np.sin(phase + 1.8 * np.exp(-t / .026) * np.sin(phase * 2.003))
    x += .20 * np.sin(phase * 2.002) * np.exp(-t / .26)
    x += .075 * np.sin(phase * 3.01) * np.exp(-t / .115)
    x += .028 * np.sin(phase * 5.013) * np.exp(-t / .07)
    return x * env(t, .0012, .42, .12) * .36 * strength


def sequence_note(note, length=.20, intensity=.8):
    """Short harmonically rich, tuned pulse; no fixed repetitive alarm timbre."""
    t = tt(length)
    phase = 2 * PI * hz(note) * t
    x = np.sin(phase + .85 * intensity * np.exp(-t / .025) * np.sin(2 * phase))
    for partial, amp in [(2, .24), (3, .115), (4, .047)]:
        x += amp * np.sin(phase * partial) * np.exp(-t / (.09 / partial))
    x += .075 * np.sin(phase * 1.003 + .3)
    return x * env(t, .0015, .085 + .035 * intensity, .025) * .22


def lead(note, length=.66):
    t = tt(length)
    p = 2 * PI * hz(note) * t
    x = np.sin(p + .9 * np.exp(-t / .06) * np.sin(p * 2.0))
    x += .26 * np.sin(p * 2) * np.exp(-t / .14)
    x += .10 * np.sin(p * .5)
    return x * env(t, .003, .23, .07) * .27


def chord(notes, length, amplitude=.055):
    t = tt(length)
    x = np.zeros((len(t), 2))
    for j, note in enumerate(notes):
        for channel, detune in enumerate([-.042, .042]):
            p = 2 * PI * hz(note + detune) * t
            tone = np.sin(p + .10 * np.sin(2 * PI * (.17 + .02 * j) * t))
            tone += .18 * np.sin(p * 2) + .045 * np.sin(p * 3)
            x[:, channel] += tone
    shape = np.minimum(1, t / .11) * np.minimum(1, np.maximum(length - t, 0) / .48)
    return filt(x, 2300) * shape[:, None] * amplitude


def bass(note, length=.42, velocity=1.):
    t = tt(length)
    p = 2 * PI * hz(note) * t + .14 * np.exp(-t / .008)
    x = np.sin(p) + .31 * np.sin(p * 2) + .10 * np.sin(p * 3)
    x = np.tanh(x * 1.15) / 1.15
    return x * env(t, .008, .35, .065) * .40 * velocity


def kick(velocity=1.):
    t = tt(.48)
    f = 47 + 105 * np.exp(-t / .014) + 20 * np.exp(-t / .07)
    p = 2 * PI * np.cumsum(f) / SR
    x = np.sin(p) * np.exp(-t / .13)
    x += filt(RNG.standard_normal(len(t)), 3800, 'highpass') * np.exp(-t / .0014) * .09
    return np.tanh(x * 1.45) * np.minimum(t / .0005, 1) * np.minimum((.48 - t) / .03, 1) * .72 * velocity


def clap(velocity=1., ghost=False):
    t = tt(.24)
    white = RNG.standard_normal(len(t))
    n = filt(white, [1100, 7800], 'bandpass')
    body = np.sin(2 * PI * (205 * t + .4 * np.exp(-t / .007))) * np.exp(-t / .025)
    x = .20 * body + .40 * n * np.exp(-t / (.024 if ghost else .05))
    for at in [.008, .015]:
        x += .09 * n * np.exp(-np.maximum(t - at, 0) / .019) * (t >= at)
    return x * velocity * np.minimum(t / .0003, 1) * .65


def hat(velocity=1., opened=False):
    length = .22 if opened else .07
    t = tt(length)
    x = .26 * RNG.standard_normal(len(t))
    for ratio in [1, 1.414, 1.734, 2.103, 2.721]:
        x += .04 * np.sign(np.sin(2 * PI * 2180 * ratio * t))
    x = filt(x, [6500, 16000], 'bandpass')
    return x * env(t, .0003, .05 if opened else .012, .02) * velocity * .37


def clock_tick(high=False):
    t = tt(.075)
    f = 1440 if high else 930
    x = np.sin(2 * PI * f * t) + .28 * np.sin(2 * PI * f * 2.61 * t)
    noise = filt(RNG.standard_normal(len(t)), [2000, 9000], 'bandpass')
    return (x * np.exp(-t / .006) + .13 * noise * np.exp(-t / .004)) * .16


def rush(length, gain=.1, downward=False):
    t = tt(length)
    q = t / length
    noise = filt(RNG.standard_normal(len(t)), [950, 10000], 'bandpass')
    # Granular-feeling motion comes from an amplitude function, not sound grains.
    movement = .65 + .35 * np.sin(2 * PI * (5 * t + 4 * t * t / length)) ** 2
    p = 2 * PI * (170 * t + 1500 * t * t / (2 * length))
    x = (noise * .60 + np.sin(p) * .075) * movement
    if downward:
        x = x[::-1]
        shape = (1 - q) ** 2 * np.minimum(q / .025, 1)
    else:
        shape = q ** 2 * np.minimum((1 - q) / .015, 1)
    x *= shape * gain
    moving_pan = .65 * np.sin(2 * PI * (1.5 * t + t * t / length))
    return np.stack((x * np.sqrt((1 - moving_pan) / 2), x * np.sqrt((1 + moving_pan) / 2)), axis=1)


def kick_at(seconds, gain=.8, velocity=1.):
    add(drums, kick(velocity), seconds, gain, kind='synthesized kick')
    at = round(seconds * SR)
    count = min(N - at, round(.35 * SR))
    duck[at:at+count] = np.maximum(duck[at:at+count], np.exp(-np.arange(count) / SR / .105))


def arrival(seconds, weight=1., with_kick=True):
    if with_kick:
        kick_at(seconds, .76 * weight)
    t = tt(.9)
    p = 2 * PI * (70 * t + 4 * np.exp(-t / .12))
    body = np.sin(p) * np.exp(-t / .22) * .13
    body += filt(RNG.standard_normal(len(t)), 1800) * np.exp(-t / .09) * .06
    add(fx, body, seconds, weight, kind='tonal arrival bloom')
    add(fx, rush(.7, .075, True), seconds, weight, kind='arrival air')


# 0--2.5: checking tension. A minor-tonic colour and a few dry clock marks.
add(harmony, chord([42, 49, 56, 57, 64], 2.9, .023), 0, kind='checking tension chord')
for seconds, note, gain in [(0.02, 30, .48), (1.02, 30, .34), (2.02, 30, .25)]:
    add(low, bass(note, .53), seconds, gain, kind='restrained heartbeat', note=note)
for i, seconds in enumerate([.25, 1., 1.75, 2.25]):
    add(drums, clock_tick(i % 2 == 1), seconds, .35, -.25 + .15 * (i % 3), 'checking clock')
for seconds, note in [(.55, 66), (1.55, 68)]:
    add(melody, sequence_note(note, .25, .4), seconds, .38, -.18 if note == 66 else .18, 'tentative signal', note)

# 2.5--4: a posting appears. A custom, exposed ascending two-note glass ding.
# E5 -> B5 is an open fifth: bright and readable without copying a brand motif.
add(posting_ding, fm_glass(76, 1.3, .98), 2.55, .92, -.08, 'original posting ding / first note', 76)
add(posting_ding, fm_glass(83, 1.6, .92), 2.80, .87, .08, 'original posting ding / second note', 83)
add(harmony, chord([42, 49, 56, 57, 64], 2.1, .021), 2.5, kind='posting harmony')

# 4--6: the 30-minute checking service gains momentum.
add(harmony, chord([38, 45, 52, 54, 61], 2.6, .041), 4, kind='momentum Dmaj9')
for seconds, note, velocity in [(4, 38, .72), (4.75, 38, .6), (5.25, 45, .6), (5.625, 38, .65)]:
    add(low, bass(note, .45), seconds, velocity, kind='momentum bass', note=note)
for seconds in [4., 4.875, 5.5]:
    kick_at(seconds, .49)
for i in range(8):
    add(drums, clock_tick(i % 2 == 1), 4 + i * .25, .43 + .045 * i, .32 * (-1 if i % 2 else 1), 'checking clock accelerates')
for i, note in enumerate([69, 73, 76, 78, 81, 78, 76, 73]):
    add(melody, sequence_note(note), 4 + i * .25, .40 + .025 * i, .4 * np.sin(i * 1.7), 'pipeline builds', note)
add(fx, rush(1.15, .10), 4.85, kind='momentum breath')

# 6--10: data-tunnel. Increasing subdivision forms one ascending phrase.
# A stable rhythmic grid gives fast graphics a measured, audible structure.
for seconds, notes in [(6, [40, 47, 54, 57, 59]), (8, [40, 47, 56, 59, 62])]:
    add(harmony, chord(notes, 2.5, .040), seconds, kind='tunnel dominant harmony')
for bar in [3, 4]:
    base = bar * 2
    for offset in [0, .75, 1.25, 1.75]:
        kick_at(base + offset, .58 if offset else .70)
    for offset in [.5, 1.5]:
        add(drums, clap(.8), base + offset, .57, -.05 if offset == .5 else .05, 'tunnel snare')
    for j in range(16):
        at = base + j * .125
        # Light off-grid pan detail; the downbeat and low end stay centered.
        add(drums, hat(.7 if j % 2 else .35), at, .8, .4 * (-1 if j % 2 else 1), 'tunnel hat')
    for offset, note in [(0, 40), (.75, 40), (1.125, 47), (1.625, 40)]:
        add(low, bass(note, .34), base + offset, .72, kind='tunnel bass', note=note)

phrase_a = [68, 71, 76, 78, 71, 76, 80, 83, 76, 80, 83, 85, 80, 83, 85, 88]
phrase_b = [71, 74, 76, 80, 74, 76, 80, 83, 76, 80, 83, 86, 80, 83, 86, 88]
for base, notes, gain in [(6, phrase_a, .46), (8, phrase_b, .55)]:
    for j, note in enumerate(notes):
        add(melody, sequence_note(note, .16, .9), base + j * .125, gain * (1 if j % 4 == 0 else .72), .4 * np.sin(j * 1.2), 'data arpeggio', note)
for j in range(8):
    add(drums, clock_tick(j % 2 == 1), 6 + j * .5, .43, .28 * (-1 if j % 2 else 1), 'pipeline clock')
add(fx, rush(1.9, .12), 8.1, kind='long tunnel rise')
for j in range(6):
    add(drums, clap(.16 + j * .035, True), 9.5 + j * .0625, .48, .20 * (-1 if j % 2 else 1), 'arrival pickup roll')

# 10--17: real JJIntern destination. The dominant becomes A major: purpose,
# confidence and a warmer melodic register instead of simply more noise.
harmonies = [
    (10, [45, 52, 56, 59, 61], 33),  # Amaj9
    (12, [44, 52, 56, 59, 64], 32),  # Eadd9/G#
    (14, [38, 45, 52, 54, 61], 38),  # Dmaj9
    (16, [40, 47, 54, 57, 59], 40),  # Esus, resolves early at 17
]
for base, notes, root in harmonies:
    length = 2.55 if base != 16 else 1.5
    add(harmony, chord(notes, length, .056), base, kind='hopeful destination harmony')
    for offset, lift in [(0, 0), (.75, 0), (1.125, 12), (1.625, 0)]:
        if base + offset < 17:
            add(low, bass(root + lift, .40 if offset else .55), base + offset, .83, kind='destination bass', note=root + lift)
    for offset in [0, .75, 1.25, 1.75]:
        if base + offset < 17:
            kick_at(base + offset, .72 if offset else .88)
    for offset in [.5, 1.5]:
        if base + offset < 17:
            add(drums, clap(.91), base + offset, .85, -.06 if offset == .5 else .06, 'destination snare')
    for j in range(8):
        at = base + j * .25
        if at < 17:
            add(drums, hat(.66 + .15 * (j % 2), j == 7), at, .92, .32 * (-1 if j % 2 else 1), 'destination hat')

arrival(10, weight=1., with_kick=False)
arrival(14, weight=.68, with_kick=False)
# A distinctive rising hook followed by an answering phrase. Its clear spaces
# leave room for the actual website and the line about worrying less.
lead_events = [
    (10.00, 76, .94), (10.375, 78, .72), (10.75, 81, .88), (11.375, 85, .84),
    (12.00, 83, .86), (12.50, 80, .74), (13.00, 76, .78), (13.625, 80, .66),
    (14.00, 81, .90), (14.50, 85, .85), (15.00, 88, .76), (15.625, 85, .70),
    (16.00, 83, .82), (16.50, 80, .70),
]
for seconds, note, gain in lead_events:
    add(melody, lead(note, .8), seconds, gain, .25 * np.sin(seconds * 3), 'destination lead', note)
# The fast data figure becomes an unobtrusive eighth-note accompaniment.
for base, notes in [(10, [69, 73, 76, 80]), (12, [68, 71, 76, 80]), (14, [69, 73, 78, 81]), (16, [68, 71, 76, 80])]:
    for j in range(8):
        at = base + j * .25
        if at < 17:
            add(melody, sequence_note(notes[j % 4], .2, .55), at + .125, .26, .52 * (-1 if j % 2 else 1), 'flow accompaniment', notes[j % 4])
add(fx, rush(.7, .075), 16.3, kind='CTA lift')

# 17--20: Amaj9 resolution and an intentional, audible tail for the CTA.
arrival(17, weight=.83)
add(low, bass(33, 2.55), 17, .95, kind='CTA resolved tonic', note=33)
add(harmony, chord([45, 52, 56, 59, 61, 68], 3., .065), 17, kind='CTA Amaj9 resolution')
for j, note in enumerate([69, 73, 76, 80, 83]):
    add(melody, lead(note, 2.3), 17 + j * .012, .37 if j < 3 else .26, -.42 + j * .21, 'CTA chord', note)
for seconds, note in [(17.75, 81), (18.25, 80), (18.75, 81)]:
    add(melody, fm_glass(note, 1.25, .6), seconds, .27, 0, 'CTA melodic punctuation', note)


def ambience(bus, scale=1.):
    """Short computed reflections; no recordings or sampled impulse response."""
    out = np.zeros_like(bus)
    for delay, gain, swap in [(.094, .15, True), (.156, .12, False), (.263, .10, True), (.387, .065, True), (.531, .041, False), (.719, .022, True)]:
        n = round(delay * SR)
        source = bus[:, ::-1] if swap else bus
        out[n:] += source[:-n] * gain * scale
    return filt(out, [360, 6200], 'bandpass')


# Dry, immediate rhythm; modest reflections replace the previous dreamier bed.
music = melody + ambience(melody, .72) + harmony + ambience(harmony, .28)
music *= (1 - .24 * duck)[:, None]
low *= (1 - .38 * duck)[:, None]
# The isolated two-note cue receives its own small space and is not sidechained.
mix = music + low + drums + fx + ambience(fx, .25)
mix += posting_ding + ambience(posting_ding, .50)
mix = filt(mix, 29, 'highpass')
mix = filt(np.tanh(mix * 1.10) / 1.10, 17300)
tail = np.minimum(1, np.maximum(0, (SECS - np.arange(N) / SR) / .50)) ** 1.65
tail *= np.minimum(1, np.arange(N) / (SR * .002))
mix *= tail[:, None]
mix *= .86 / max(.86, float(np.max(np.abs(mix))))

pcm = (np.clip(mix, -1, 1) * (2 ** 23 - 1)).astype(np.int32)
packed = np.stack((pcm & 255, (pcm >> 8) & 255, (pcm >> 16) & 255), axis=-1).astype(np.uint8)
raw = OUT / 'jjintern-pipeline-premaster.wav'
with wave.open(str(raw), 'wb') as wav:
    wav.setnchannels(2)
    wav.setsampwidth(3)
    wav.setframerate(SR)
    wav.writeframes(packed.tobytes())


def measure(path):
    result = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(path), '-af',
                             'loudnorm=I=-14:TP=-1:LRA=9:print_format=json',
                             '-f', 'null', '-'], capture_output=True, text=True, check=True)
    return json.loads(re.findall(r'\{[^{}]*\}', result.stderr)[-1])


first = measure(raw)
options = 'loudnorm=I=-14:TP=-1:LRA=9:' + ':'.join([
    f'measured_I={first["input_i"]}', f'measured_TP={first["input_tp"]}',
    f'measured_LRA={first["input_lra"]}', f'measured_thresh={first["input_thresh"]}',
    f'offset={first["target_offset"]}', 'linear=true', 'print_format=json',
])
final = OUT / 'jjintern-pipeline-original-score.wav'
subprocess.run(['ffmpeg', '-hide_banner', '-y', '-i', str(raw), '-af', options,
                '-ar', str(SR), '-c:a', 'pcm_s24le', str(final)],
               capture_output=True, text=True, check=True)
measured = measure(final)
manifest = {
    'title': 'A Clearer Signal',
    'revision': 'V3, new composition for internship-alert data pipeline',
    'duration_seconds': SECS, 'sample_rate': SR, 'channels': 2,
    'bits_per_sample': 24, 'tempo_bpm': 120, 'meter': '4/4',
    'tonal_narrative': 'F-sharp minor checking tension -> dominant E -> A-major destination and CTA',
    'originality': 'Every tone, drum, noise transition and reverberation tap synthesized in this file. No samples, recordings, stock loops, vocals, external music generators or sampled IRs.',
    'seed': 730171026,
    'posting_ding': {'notes_midi': [76, 83], 'times_seconds': [2.55, 2.80], 'interval': 'ascending perfect fifth', 'synthesis': 'Original two-note FM glass/resonator; no branded sound recording'},
    'cues': [
        {'s': 0, 'cue': 'Quiet checking tension; low pulse and sparse dry clock'},
        {'s': 2.55, 'cue': 'Posting appears: original exposed two-note glass ding'},
        {'s': 4, 'cue': '30-minute checking line: sequencer and rhythm build'},
        {'s': 6, 'cue': 'Data tunnel: fast tonal sixteenth-note arpeggio'},
        {'s': 8, 'cue': 'Escalation: dominant tension and subdivided pickup'},
        {'s': 10, 'cue': 'Website/feed arrival: Amaj9 and strong drum downbeat'},
        {'s': 14, 'cue': 'Hopeful payoff: melody lifts and opens space'},
        {'s': 17, 'cue': 'Resolved CTA: Amaj9, drums make room for logo'},
        {'s': 19.5, 'cue': 'Clean final half-second tail to silence'},
    ],
    'premaster': {'integrated_lufs': float(first['input_i']), 'true_peak_dbtp': float(first['input_tp']), 'loudness_range_lu': float(first['input_lra'])},
    'master': {'file': final.name, 'integrated_lufs': float(measured['input_i']), 'true_peak_dbtp': float(measured['input_tp']), 'loudness_range_lu': float(measured['input_lra']), 'method': 'Two-pass ffmpeg EBU R128 loudnorm; -14 LUFS and -1 dBTP targets'},
    'stereo_correlation_premaster': round(float(np.corrcoef(mix.T)[0, 1]), 5),
    'build_seconds': round(time.perf_counter() - START, 3),
    'events': sorted(events, key=lambda e: e['s']),
}
(OUT / 'score-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({k: manifest[k] for k in ['title', 'duration_seconds', 'posting_ding', 'premaster', 'master', 'build_seconds']}, indent=2))
print(final)
