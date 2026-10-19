#!/usr/bin/env python3
"""Compose and synthesize the original JJIntern score. No samples, loops or IRs.

Run with Python 3.13 + numpy/scipy, then master using the accompanying command.
Every waveform and every reverberation tail is generated mathematically here.
"""
from pathlib import Path
import json
import math
import re
import subprocess
import time
import wave

import numpy as np
from scipy import signal

START = time.perf_counter()
OUT = Path(__file__).resolve().parent
SR = 48000
DURATION = 20.0
N = int(SR * DURATION)
BPM = 120
BEAT = 60 / BPM
RNG = np.random.default_rng(17102026)
PI = np.pi

harm = np.zeros((N, 2), dtype=np.float64)
drum = np.zeros_like(harm)
bass_bus = np.zeros_like(harm)
effects = np.zeros_like(harm)
duck = np.zeros(N, dtype=np.float64)
events = []


def hz(midi):
    return 440 * 2 ** ((midi - 69) / 12)


def tt(duration):
    return np.arange(int(duration * SR)) / SR


def filt(x, cutoff, kind='lowpass', order=2):
    return signal.sosfilt(signal.butter(order, cutoff, kind, fs=SR, output='sos'), x, axis=0)


def envelope(t, attack=0.004, decay=0.3, release=0.08):
    env = (1 - np.exp(-t / attack)) * np.exp(-t / decay)
    if len(t):
        env *= np.clip((t[-1] - t) / max(0.001, release), 0, 1)
    return env


def add(bus, x, seconds, amp=1., pan=0., label=None):
    pos = int(seconds * SR)
    if pos >= N:
        return
    if x.ndim == 1:
        a = (np.clip(pan, -1, 1) + 1) * PI / 4
        x = np.stack((x * np.cos(a), x * np.sin(a)), axis=1)
    if pos < 0:
        x = x[-pos:]
        pos = 0
    count = min(len(x), N - pos)
    bus[pos:pos + count] += x[:count] * amp
    if label:
        events.append({'seconds': round(seconds, 4), 'kind': label, 'gain': amp, 'pan': pan})


def pluck(midi, length=1.2, brightness=1., velocity=1.):
    t = tt(length)
    f = hz(midi)
    # A tuned resonator, an FM strike and slowly detuned upper tone.
    strike = 2.5 * brightness * np.exp(-t / .045) * np.sin(2 * PI * f * 2.003 * t)
    core = np.sin(2 * PI * f * t + strike)
    core += .31 * np.sin(2 * PI * f * 2.0006 * t) * np.exp(-t / .15)
    core += .13 * np.sin(2 * PI * f * 3.998 * t) * np.exp(-t / .075)
    core += .07 * np.sin(2 * PI * f * .5 * t) * np.exp(-t / .2)
    env = envelope(t, .0012, .28 + .12 * velocity, .09)
    return core * env * velocity * .23


def glass(midi, length=2.4):
    t = tt(length)
    f = hz(midi)
    x = np.zeros_like(t)
    for ratio, gain, decay in [(1, .7, .85), (2.001, .22, .4), (3.997, .08, .2), (5.012, .035, .15)]:
        x += gain * np.sin(2 * PI * f * ratio * t) * np.exp(-t / decay)
    return x * (1 - np.exp(-t / .004)) * np.minimum(1, (length - t) / .1) * .28


def pad(notes, length, lift=1.):
    t = tt(length)
    y = np.zeros((len(t), 2))
    for ni, note in enumerate(notes):
        f = hz(note)
        for channel, cents in enumerate([-.065, .065]):
            phase = 2 * PI * f * 2 ** (cents / 12) * t
            voice = np.sin(phase + .2 * np.sin(2 * PI * (.11 + ni * .013) * t))
            voice += .22 * np.sin(phase * 2 + .3 * ni)
            voice += .095 * np.sin(phase * 3 + .7)
            voice += .04 * np.sin(phase * 5)
            y[:, channel] += voice
    # The attack breathes, and a long release overlaps chord changes.
    env = np.minimum(1, t / .35) * np.minimum(1, np.maximum(0, length - t) / .9)
    slow = .88 + .12 * np.sin(2 * PI * .22 * t)
    return filt(y, 1900) * env[:, None] * slow[:, None] * (.038 * lift)


def bass(midi, length):
    t = tt(length)
    f = hz(midi)
    phase = 2 * PI * (f * t - .12 * np.exp(-t / .008))
    x = np.sin(phase) + .23 * np.sin(phase * 2) + .09 * np.sin(phase * 3)
    x = np.tanh(x * 1.15) / 1.15
    return x * envelope(t, .012, length * .95, .09) * .34


def kick(velocity=1.):
    t = tt(.58)
    freq = 46 + 105 * np.exp(-t / .018) + 25 * np.exp(-t / .065)
    phase = np.cumsum(freq) * 2 * PI / SR
    x = np.sin(phase) * np.exp(-t / .16)
    transient = RNG.standard_normal(len(t)) * np.exp(-t / .0022) * .16
    x += filt(transient, 3500, 'highpass')
    x *= np.minimum(1, t / .0005) * np.minimum(1, (.58 - t) / .04)
    return np.tanh(x * 1.5) * .75 * velocity


def snare(velocity=1., ghost=False):
    t = tt(.25 if ghost else .4)
    noise = RNG.standard_normal(len(t))
    bright = filt(noise, [1600, 8500], 'bandpass')
    warm = filt(noise, [450, 3000], 'bandpass')
    env = np.exp(-t / (.032 if ghost else .065))
    body = np.sin(2 * PI * (186 * t + .8 * np.exp(-t / .012))) * np.exp(-t / .035)
    x = (.38 * bright + .17 * warm) * env + body * .23
    # A pair of generated, delayed noise transients gives the snap a clap tail.
    for at in [.008, .016]:
        x += bright * np.exp(-np.maximum(t - at, 0) / .021) * (t >= at) * .07
    return x * velocity * .7 * np.minimum(1, t / .0004)


def hat(opened=False, velocity=1.):
    length = .3 if opened else .1
    t = tt(length)
    x = np.zeros_like(t)
    for ratio in [1., 1.342, 1.521, 1.849, 2.173, 2.592]:
        x += np.sign(np.sin(2 * PI * 1987 * ratio * t)) * .075
    x += .23 * RNG.standard_normal(len(t))
    x = filt(x, [5900, 16000], 'bandpass')
    return x * envelope(t, .0003, .063 if opened else .015, .03) * velocity * .32


def tick(pitch=1200, length=.12):
    t = tt(length)
    phase = 2 * PI * (pitch * t + .4 * np.exp(-t / .002))
    return (np.sin(phase) + .3 * np.sin(phase * 2.17)) * envelope(t, .0003, .013, .03) * .19


def sweep(length, direction=1, strength=.16):
    t = tt(length)
    q = t / length
    # Filtered Gaussian noise is newly synthesized, never a sampled effect.
    hiss = filt(RNG.standard_normal(len(t)), [500, 9000], 'bandpass')
    carrier = np.sin(2 * PI * (150 * t + (1800 / (2 * length)) * t * t))
    if direction < 0:
        hiss, carrier = hiss[::-1], carrier[::-1]
        env = (1 - q) ** 2 * np.minimum(1, q / .01)
    else:
        env = q ** 2.3 * np.minimum(1, (1 - q) / .025)
    x = (hiss * .65 + carrier * .07) * env * strength
    # A moving stereo field rather than a centered broadband hiss.
    pan = np.sin(2 * PI * 1.2 * t) * .7
    return np.stack((x * np.sqrt((1 - pan) / 2), x * np.sqrt((1 + pan) / 2)), axis=1)


def impact(seconds, weight=.6):
    add(drum, kick(.8 * weight), seconds, label='synth impact')
    t = tt(1.3)
    tone = np.sin(2 * PI * (70 * t + 9 * np.exp(-t / .14))) * np.exp(-t / .32)
    tone += filt(RNG.standard_normal(len(t)), 1600) * np.exp(-t / .17) * .2
    add(effects, tone, seconds, .19 * weight, label='impact bloom')


def rhythm(bar, density=1.):
    base = bar * 2
    # Deliberately syncopated drums; swung eighths and changing ghost notes.
    pattern = [0, 1.5, 2.25] if bar % 2 == 0 else [0, .75, 2.5, 3.5]
    for beat in pattern:
        at = base + beat * BEAT
        if at >= 17:
            continue
        add(drum, kick(.83 if beat else 1), at, .72 * density, label='kick')
        p = int(at * SR)
        n = min(N - p, int(.38 * SR))
        duck[p:p+n] = np.maximum(duck[p:p+n], np.exp(-np.arange(n) / SR / .12))
    for beat in [1, 3]:
        at = base + beat * BEAT
        if at < 17:
            add(drum, snare(.93 if beat == 3 else .83), at, .75 * density, -.07 if beat == 1 else .08, 'snare')
    for sub in range(8):
        at = base + sub * .25 + (.035 if sub % 2 else 0)
        if at < 17:
            add(drum, hat(sub in [3, 7] and bar % 2 == 1, .58 + .2 * (sub % 2)), at, density, -.32 + (sub % 3) * .28, 'synth hat')
    if bar in [2, 4, 6, 7]:
        for beat, pan in [(2.75, .4), (3.75, -.25)]:
            at = base + beat * BEAT
            if at < 17:
                add(drum, snare(.28, True), at, density, pan, 'ghost snare')


# Harmony has a direction: suspended open -> bright ascent -> settled Dmaj9.
# Ten 2-second bars; the final dominant resolves early at exactly 17 seconds.
chords = [
    [50, 57, 61, 64, 66],  # Dmaj9
    [54, 57, 61, 64, 68],  # F#m9
    [47, 54, 57, 61, 64],  # Bm11
    [43, 54, 57, 62, 66],  # Gmaj9
    [45, 52, 59, 61, 64],  # Aadd9
    [50, 57, 61, 64, 66],
    [47, 54, 57, 61, 66],
    [43, 54, 57, 62, 66],
    [45, 52, 57, 59, 64],
]
roots = [38, 42, 35, 31, 33, 38, 35, 31, 33]
for bar, notes in enumerate(chords):
    length = 2.9 if bar != 8 else 1.6
    add(harm, pad(notes, length, .7 if bar < 3 else 1.12), bar * 2, label='tonal pad')
    if bar >= 3:
        offsets = [0, .75, 1.125, 1.625] if bar % 2 else [0, .875, 1.25]
        for j, at in enumerate(offsets):
            if bar * 2 + at < 17:
                add(bass_bus, bass(roots[bar] + (12 if j == 3 else 0), .42 if j else .65), bar * 2 + at, .9, label='rounded bass')
    elif bar in [0, 2]:
        add(bass_bus, bass(roots[bar], 1.35), bar * 2, .65, label='opening sub')

# Opening signature: a five-note, rising hook with deliberately spacious gaps.
for at, midi, pan, level in [(0.03, 74, -.15, .8), (.5, 81, .22, .7), (.875, 76, -.25, .58), (1.25, 78, .15, .82), (1.75, 85, .35, .43), (2.25, 80, -.25, .72), (2.625, 76, .15, .55)]:
    add(harm, pluck(midi), at, level, pan, 'signature mallet')
add(harm, glass(86), .03, .26, .5, 'opening sparkle')
add(drum, kick(.8), .0, .65, label='opening pulse')
for at in [.5, 1.25, 2., 2.5]:
    add(drum, tick(1000 + at * 180), at, .42, (-1 if at == 1.25 else 1) * .35, 'opening tick')

# Fragmentation: the hook breaks into a quicker, antiphonal sequence.
fragments = [74, 78, 81, 85, 81, 78, 76, 73, 74, 78, 81, 85]
for j, midi in enumerate(fragments):
    at = 3 + j * .21875
    add(harm, pluck(midi, .8, .9, .75 + .15 * (j % 3)), at, .59, .52 * (-1 if j % 2 else 1), 'fragment arpeggio')
for at in [3.0, 3.75, 4.5, 5.25, 5.5, 5.75]:
    add(drum, hat(False, .6), at, .7, .35 * math.sin(at * 5), 'fragment hat')
impact(3, .5)
rhythm(2, .48)

# Full groove enters at 6 seconds. The phrase changes with every harmony.
arp_shapes = [
    [74, 78, 81, 86, 81, 78],
    [73, 76, 81, 83, 81, 76],
    [74, 78, 81, 85, 88, 81],
    [73, 78, 81, 85, 86, 81],
    [74, 78, 81, 86, 90, 86],
    [73, 76, 81, 83, 88, 85],
]
for bar in range(3, 9):
    rhythm(bar, 1. if bar < 7 else 1.07)
    offsets = [0, .375, .625, 1., 1.375, 1.75]
    for j, (offset, midi) in enumerate(zip(offsets, arp_shapes[bar - 3])):
        at = bar * 2 + offset
        if at >= 17:
            continue
        add(harm, pluck(midi, .95, 1.05, .85), at, .70 if j in [0, 3] else .49, .45 * math.sin(j * 1.75 + bar), 'lead arpeggio')

# Wide, singing counterline in the expanded second half; no repetitive alarm tone.
for at, midi, amp, pan in [(10, 78, .6, -.35), (10.75, 81, .55, .28), (11.5, 85, .68, -.15), (12.25, 83, .55, .3), (13, 81, .55, -.25), (13.5, 78, .5, .22), (14, 86, .7, -.25), (14.75, 90, .55, .3), (15.25, 88, .5, -.3), (16, 85, .52, .25)]:
    add(harm, glass(midi, 2.2), at, amp, pan, 'glass counterline')

# Finely subdivided details at the typographic climax; each last hit is intentional.
for j in range(20):
    at = 14 + j * .125
    if j % 3 != 1:
        add(drum, tick(1300 + (j % 5) * 430), at, .24 + .12 * (j % 4 == 0), .65 * math.sin(j * 2.4), 'climax detail')
for at, length, strength in [(2.45, .55, .11), (5., 1., .16), (9., 1., .15), (13.15, .85, .18), (16.3, .7, .13)]:
    add(effects, sweep(length, 1, strength), at, label='rising transition')
for at in [6, 10, 14]:
    impact(at, .65 if at != 14 else .8)
    add(effects, sweep(.9, -1, .08), at, label='falling transition')

# Brand resolution, precisely at 17 s: percussion makes room for a major ninth.
impact(17, .7)
add(bass_bus, bass(38, 2.7), 17, 1., label='resolved tonic')
add(harm, pad([50, 57, 61, 64, 66, 73], 3., 1.2), 17, 1.05, label='final Dmaj9')
for j, midi in enumerate([62, 69, 73, 78, 81]):
    add(harm, glass(midi, 2.8), 17 + j * .016, .45 if j < 3 else .3, -.5 + .25 * j, 'resolved chord bloom')
for at, midi, pan in [(17.75, 81, -.25), (18.25, 85, .25), (18.75, 86, .0)]:
    add(harm, pluck(midi, 1.2, .6, .6), at, .38, pan, 'closing signature')


def ambience(x):
    # Reproducible stereo delays and diffusion, all generated (no impulse recording).
    wet = np.zeros_like(x)
    for delay, gain, cross in [(.117, .18, True), (.193, .15, False), (.283, .16, True), (.419, .105, True), (.613, .078, False), (.887, .042, True), (1.127, .025, False)]:
        d = int(delay * SR)
        source = x[:, ::-1] if cross else x
        wet[d:] += source[:-d] * gain
    return filt(wet, [350, 6100], 'bandpass')


# A little musical breathing on the harmonic bus preserves the drum transients.
harmonic = harm + ambience(harm) * .8
harmonic *= (1 - .22 * duck)[:, None]
bass_bus *= (1 - .35 * duck)[:, None]
mix = harmonic + drum + bass_bus + effects + ambience(effects) * .35
mix = filt(mix, 29, 'highpass')
mix = np.tanh(mix * 1.13) / 1.13
# Gentle master balance, then a fully silent finish with no clipped reverb edge.
mix = filt(mix, 17500, 'lowpass')
fade = np.minimum(1, np.arange(N) / (SR * .002))
fade *= np.minimum(1, np.maximum(0, (DURATION - np.arange(N) / SR) / .55)) ** 1.55
mix *= fade[:, None]
mix *= .88 / max(.88, float(np.max(np.abs(mix))))

# 24-bit PCM intermediate retains headroom for final EBU R128 loudness mastering.
pcm = (np.clip(mix, -1, 1) * (2 ** 23 - 1)).astype(np.int32)
packed = np.stack((pcm & 255, (pcm >> 8) & 255, (pcm >> 16) & 255), axis=-1).astype(np.uint8)
raw = OUT / 'jjintern-original-premaster.wav'
with wave.open(str(raw), 'wb') as wav:
    wav.setnchannels(2)
    wav.setsampwidth(3)
    wav.setframerate(SR)
    wav.writeframes(packed.tobytes())

manifest = {
    'title': 'Signal to Possibility',
    'duration_seconds': DURATION,
    'sample_rate': SR,
    'channels': 2,
    'tempo_bpm': BPM,
    'meter': '4/4',
    'bars': 10,
    'key': 'D major',
    'harmonic_colour': 'major ninth / suspended added ninth',
    'originality': 'Every oscillator, noise source, drum transient, delay and reverb tap is synthesized in this file. No samples, recordings, stock loops, external music model or impulse response.',
    'seed': 17102026,
    'cues': [
        {'s': 0, 'cue': 'Spark: intimate five-note mallet signature, soft sub pulse'},
        {'s': 3, 'cue': 'Fragments: rapid antiphonal motif and percussion pickup'},
        {'s': 6, 'cue': 'Focus: full swung garage groove and rounded bass'},
        {'s': 10, 'cue': 'Expand: stereo glass counterline opens the harmony'},
        {'s': 14, 'cue': 'Climax: highest motif register and sixteenth-note detail'},
        {'s': 17, 'cue': 'Resolve: drums clear for Dmaj9 brand chord'},
        {'s': 19.45, 'cue': 'Smooth final tail fade to silence'},
    ],
    'events': sorted(events, key=lambda e: e['seconds']),
    'build_seconds': round(time.perf_counter() - START, 3),
    'premaster_peak_dbfs': round(20 * np.log10(np.max(np.abs(mix))), 3),
    'premaster_rms_dbfs': round(20 * np.log10(np.sqrt(np.mean(mix ** 2))), 3),
}


def loudness_pass(path, options):
    proc = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(path), '-af', options,
                           '-f', 'null', '-'], capture_output=True, text=True, check=True)
    return json.loads(re.findall(r'\{[^{}]*\}', proc.stderr)[-1])


first = loudness_pass(raw, 'loudnorm=I=-14:TP=-1:LRA=8:print_format=json')
settings = 'loudnorm=I=-14:TP=-1:LRA=8:' + ':'.join([
    f'measured_I={first["input_i"]}',
    f'measured_TP={first["input_tp"]}',
    f'measured_LRA={first["input_lra"]}',
    f'measured_thresh={first["input_thresh"]}',
    f'offset={first["target_offset"]}',
    'linear=true',
    'print_format=json',
])
final = OUT / 'jjintern-original-score.wav'
subprocess.run(['ffmpeg', '-hide_banner', '-y', '-i', str(raw), '-af', settings,
                '-ar', str(SR), '-c:a', 'pcm_s24le', str(final)],
               capture_output=True, text=True, check=True)
measured = loudness_pass(final, 'loudnorm=I=-14:TP=-1:LRA=8:print_format=json')
manifest['master'] = {
    'file': final.name,
    'bits_per_sample': 24,
    'integrated_lufs': float(measured['input_i']),
    'true_peak_dbtp': float(measured['input_tp']),
    'loudness_range_lu': float(measured['input_lra']),
    'normalization': 'FFmpeg two-pass EBU R128 loudnorm; -14 LUFS / -1 dBTP targets',
}
manifest['build_seconds'] = round(time.perf_counter() - START, 3)
(OUT / 'score-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({k: manifest[k] for k in ['title', 'duration_seconds', 'tempo_bpm', 'build_seconds', 'premaster_peak_dbfs', 'premaster_rms_dbfs', 'master']}, indent=2))
print(final)
