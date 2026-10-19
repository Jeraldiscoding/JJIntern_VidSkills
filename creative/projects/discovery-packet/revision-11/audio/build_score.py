#!/usr/bin/env python3
"""Revision11 timing adaptation of the original revision09 electro-break score.

No previous WAV, recording, sample, loop, soundfont or impulse response is read.
All kit layers, the three-note hook, bass, cymbals, fills and effects originate
from oscillators, deterministic noise, filters and amplitude envelopes.
"""
from array import array
from pathlib import Path
import hashlib
import json
import math
import random
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SR, DURATION, SEED = 48000, 18.0, 91603181
N, TAU, BPM = round(SR * DURATION), 2 * math.pi, 160
BEAT = 60 / BPM
BUS = [array('f', [0]) * N, array('f', [0]) * N]
EVENTS = []
TABLE_SIZE = 4096
SAW = [sum((-1) ** (h + 1) * math.sin(2 * math.pi * h * j / TABLE_SIZE) / h
           for h in range(1, 15)) * .63 for j in range(TABLE_SIZE)]


def hz(note):
    return 440 * 2 ** ((note - 69) / 12)


def smooth(v):
    v = min(1., max(0., v))
    return v * v * (3 - 2 * v)


def edge(t, length, attack=.002, release=.025):
    return smooth(t / attack) * smooth((length - t) / release)


def saw(phase):
    position = (phase % 1) * TABLE_SIZE
    index = int(position)
    frac = position - index
    return SAW[index] * (1 - frac) + SAW[(index + 1) % TABLE_SIZE] * frac


def add(start, length, synth, gain, pan, kind, **params):
    begin = round(start * SR)
    count = min(round(length * SR), N - begin)
    lg, rg = gain * math.cos((pan + 1) * math.pi / 4), gain * math.sin((pan + 1) * math.pi / 4)
    for i in range(count):
        v = synth(i / SR)
        BUS[0][begin + i] += lg * v
        BUS[1][begin + i] += rg * v
    EVENTS.append(dict(start_s=start, duration_s=length, kind=kind, gain=gain, pan=pan, **params))


def kick(start, gain=.215, strong=False):
    length, f = (.34, 49) if strong else (.29, 52)
    rng = random.Random(SEED + round(start * SR) + 1)
    low = 0.
    a = 1 - math.exp(-TAU * 2500 / SR)
    def synth(t):
        nonlocal low
        p = TAU * (f * t + 132 * .014 * (1 - math.exp(-t / .014)))
        sub = .78 * math.sin(p) * math.exp(-t / .095)
        chest = .32 * math.sin(TAU * (98 * t + 60 * .008 * (1 - math.exp(-t / .008)))) * math.exp(-t / .042)
        white = rng.uniform(-1, 1)
        low += a * (white - low)
        beater = .20 * low * math.exp(-t / .0037)
        return math.tanh(1.55 * (sub + chest + beater)) * edge(t, length, .0008, .04)
    add(start, length, synth, gain, 0, 'layered sub/body/beater kick', strong=strong,
        sub_hz=f, body_hz=98)


def clap(start, gain=.047, pan=.23):
    length = .17
    rng = random.Random(SEED + round(start * SR) + round((pan + 1) * 173) + 7)
    low = high = 0.
    a, b = 1 - math.exp(-TAU * 7200 / SR), 1 - math.exp(-TAU * 1050 / SR)
    def synth(t):
        nonlocal low, high
        white = rng.uniform(-1, 1)
        high += a * (white - high)
        low += b * (white - low)
        cluster = 0.
        for when, g in [(0., 1.), (.011, .82), (.024, .68)]:
            if t >= when:
                cluster += g * math.exp(-(t - when) / .0068) * smooth((t - when) / .0008)
        tail = .35 * math.exp(-max(0., t - .025) / .044) * smooth((t - .02) / .006)
        return (high - low) * (cluster + tail) * edge(t, length, .0006, .025)
    add(start, length, synth, gain, pan, 'three-burst filtered-noise clap')


def snare(start, gain=.125, ghost=False, with_clap=True):
    length = .135 if ghost else .225
    rng = random.Random(SEED + round(start * SR) + 13)
    low = high = 0.
    a, b = 1 - math.exp(-TAU * 9500 / SR), 1 - math.exp(-TAU * 900 / SR)
    def synth(t):
        nonlocal low, high
        white = rng.uniform(-1, 1)
        high += a * (white - high)
        low += b * (white - low)
        # A thick tuned body sits under a longer wire tail and short attack snap.
        phase = TAU * (185 * t + 45 * .014 * (1 - math.exp(-t / .014)))
        body = (.60 * math.sin(phase) + .23 * math.sin(TAU * 330 * t)) * math.exp(-t / .053)
        wires = (high - low) * .76 * math.exp(-t / (.026 if ghost else .056))
        return math.tanh(1.55 * (body + wires)) * edge(t, length, .0008, .035)
    add(start, length, synth, gain, -.025, 'ghost snare' if ghost else 'fat layered body-and-wire snare')
    if with_clap and not ghost:
        clap(start + .007, .042, -.23)
        clap(start + .013, .036, .23)


def cymbal(start, gain=.025, opened=False, crash=False, pan=.28):
    length = .68 if crash else (.255 if opened else .055)
    decay = .19 if crash else (.076 if opened else .014)
    rng = random.Random(SEED + round(start * SR) + 23)
    low = high = 0.
    a, b = 1 - math.exp(-TAU * 14000 / SR), 1 - math.exp(-TAU * (2900 if crash else 5000) / SR)
    frequencies = [4163, 5621, 6719, 8123, 10193, 12461]
    def synth(t):
        nonlocal low, high
        white = rng.uniform(-1, 1)
        high += a * (white - high)
        low += b * (white - low)
        # Multiple inharmonic sines enrich a broad noise cymbal, not a pitched poke.
        metal = sum(math.sin(TAU * f * t) for f in frequencies) / 6
        wave = .83 * (high - low) + .17 * metal
        return wave * math.exp(-t / decay) * edge(t, length, .0007, .025 if opened or crash else .009)
    add(start, length, synth, gain, pan,
        'short crash cymbal' if crash else ('open cymbal' if opened else 'closed cymbal'),
        decay_s=decay)


def tom(start, note, gain=.12, length=.235, pan=0):
    f = hz(note)
    rng = random.Random(SEED + round(start * SR) + 31)
    def synth(t):
        p = TAU * (f * t + f * .42 * .021 * (1 - math.exp(-t / .021)))
        body = math.sin(p) + .19 * math.sin(1.99 * p)
        attack = .045 * rng.uniform(-1, 1) * math.exp(-t / .004)
        return math.tanh(1.3 * (body + attack)) * math.exp(-t / .075) * edge(t, length, .001, .03)
    add(start, length, synth, gain, pan, 'pitched drum-fill tom', midi=note, fundamental_hz=f)


def bass(start, note, length=.22, gain=.115, bright=1.):
    f = hz(note)
    low = band = 0.
    def synth(t):
        nonlocal low, band
        wave = .70 * saw(f * t) + .30 * math.sin(TAU * f * t)
        drive = math.tanh(2.35 * wave)
        cutoff = 175 + 1250 * bright * math.exp(-t / .065)
        c = 2 * math.sin(math.pi * cutoff / SR)
        low += c * band
        high = drive - low - .72 * band
        band += c * high
        body = .77 * math.tanh(1.5 * low) + .28 * math.sin(TAU * f * t)
        return body * edge(t, length, .004, .047)
    add(start, length, synth, gain, 0, 'syncopated resonant sub-bass', midi=note,
        fundamental_hz=f, filter_initial_hz=175 + 1250 * bright)


def hook_note(start, note, length, gain=.045, bright=1., pan=-.16):
    f = hz(note)
    low = band = 0.
    def synth(t):
        nonlocal low, band
        # Detuned band-limited saws and a pulse-like difference form a wide gritty lead.
        wave = .53 * saw(f * t * .998) + .47 * saw(f * t * 1.002)
        pulse = .16 * (saw(f * t) - saw(f * t + .37))
        driven = math.tanh(2.0 * (wave + pulse))
        cutoff = 650 + 2200 * bright * math.exp(-t / .105)
        c = 2 * math.sin(math.pi * cutoff / SR)
        low += c * band
        high = driven - low - .95 * band
        band += c * high
        amp = (.88 + .12 * math.exp(-t / .04)) * edge(t, length, .006, .045)
        return math.tanh(1.35 * low) * amp
    add(start, length, synth, gain, pan, 'three-note gritty synth hook', midi=note,
        fundamental_hz=f, detune_ratio=[.998, 1.002], bright=bright)


def hook(start, bright=1., gain=.050, variation=False):
    # Memorable F#–A–E cell: short, short, held; same contour across the film.
    notes = [66, 69, 64]
    for k, (offset, length, note) in enumerate(zip([0, .75 * BEAT, 1.5 * BEAT], [.19, .15, .31], notes)):
        hook_note(start + offset, note + (12 if variation and k == 1 else 0), length,
                  gain * [1., .90, .94][k], bright, [-.13, .12, -.06][k])


def click(start, gain=.05, frequency=2100, kind='mechanical sync click'):
    length = .036
    rng = random.Random(SEED + round(start * SR) + 41)
    def synth(t):
        return (.52 * math.sin(TAU * frequency * t) + .22 * rng.uniform(-1, 1)) * math.exp(-t / .005) * edge(t, length, .0005, .008)
    add(start, length, synth, gain, 0, kind, frequency_hz=frequency)


def source_ding(start=.18):
    f, length = hz(90), .66
    def synth(t):
        return (math.sin(TAU * f * t) * math.exp(-t / .19) + .20 * math.sin(TAU * 2.01 * f * t) * math.exp(-t / .065)) * edge(t, length, .0015, .08)
    add(start, length, synth, .092, 0,
        'source ding' if start == .18 else 'same source-style ding for logo/Found bubble',
        fundamental_hz=f, identical_synthesis_parameters=True)


def zipper(start, length, gain=.045, descending=False, kind='filtered motion texture'):
    rng = random.Random(SEED + round(start * SR) + 47)
    low = high = 0.
    def synth(t):
        nonlocal low, high
        u = t / length
        cutoff = 750 + 6200 * ((1 - u) ** 1.6 if descending else u ** 1.6)
        white = rng.uniform(-1, 1)
        high += (1 - math.exp(-TAU * cutoff / SR)) * (white - high)
        low += (1 - math.exp(-TAU * 450 / SR)) * (white - low)
        grain = .60 + .40 * math.sin(TAU * (29 * t + 31 * t * t)) ** 2
        return (high - low) * grain * edge(t, length, .006, .013)
    add(start, length, synth, gain, -.05, kind, descending=descending)


def drum_bar(start, variation=0, gain=1., hats=True):
    kicks = [[0, 1.5, 2.75], [0, .75, 2, 3.5], [0, 1.75, 2.5]][variation % 3]
    for step in kicks:
        kick(start + step * BEAT, gain * (.205 if step in (0, 2) else .177))
    for step in (1, 3):
        snare(start + step * BEAT, gain * .118)
    snare(start + (2.5 if variation % 2 else .75) * BEAT, gain * .041, True, False)
    if hats:
        for k in range(8):
            cymbal(start + k * .5 * BEAT, gain * (.023 if k % 2 else .018),
                   opened=(k == 7 and variation % 2 == 0), pan=.24)
        if variation == 1:
            cymbal(start + 2.75 * BEAT, gain * .012, pan=-.22)
    riffs = [
        [(0, 30, .24), (.75, 30, .13), (1.5, 37, .19), (2.75, 40, .20)],
        [(0, 30, .28), (1.75, 33, .15), (2.5, 37, .16), (3.5, 30, .15)],
        [(0, 30, .25), (.75, 42, .15), (2, 37, .21), (3.25, 40, .15)]]
    for step, note, length in riffs[variation % 3]:
        bass(start + step * BEAT, note, length, .107 * gain, 1 + .12 * variation)


def drum_fill(end, explosive=False):
    # Four sixteenths lead directly to the impact: snare, high tom, low tom, snare.
    grid = BEAT / 4
    snare(end - 4 * grid, .073, True, False)
    tom(end - 3 * grid, 54, .105, .16, -.24)
    tom(end - 2 * grid, 45, .13, .18, .22)
    snare(end - grid, .115 if explosive else .095, False, explosive)


def flight_air(start=2.0, length=6.75):
    rng = random.Random(SEED + 310)
    low = high = 0.
    for j in range(round(length * SR)):
        t = j / SR
        absolute = start + t
        if absolute < 2.55:
            speed = .20 + .15 * smooth((absolute - 2.0) / .55)
        elif absolute < 6.55:
            speed = .35 + .65 * ((absolute - 2.55) / 4.0) ** 1.4
        elif absolute < 8.05:
            speed = 1.0 - .88 * smooth((absolute - 6.55) / 1.5)
        else:
            speed = .12 * (1 - smooth((absolute - 8.05) / .70))
        white = rng.uniform(-1, 1)
        cutoff = 1700 + 6100 * speed * speed
        high += (1 - math.exp(-TAU * cutoff / SR)) * (white - high)
        low += (1 - math.exp(-TAU * 360 / SR)) * (white - low)
        grain = .78 + .22 * math.sin(TAU * (19 * t + 5 * t * t))
        amplitude = .037 * speed * edge(t, length, .02, .018)
        v = (high - low) * grain * amplitude
        pan = -.18 + .36 * smooth((absolute - 6.55) / 1.5)
        idx = round(start * SR) + j
        BUS[0][idx] += v * math.cos((pan + 1) * math.pi / 4)
        BUS[1][idx] += v * math.sin((pan + 1) * math.pi / 4)
    EVENTS.append(dict(start_s=start, duration_s=length, kind='stationary-flight air build, convergence deceleration and capture taper',
                       gain=.037, filter_floor_peak_hz=[1700, 7800],
                       build_range_s=[2.55, 6.55], deceleration_range_s=[6.55, 8.05],
                       capture_taper_range_s=[8.05, 8.75]))


def compose():
    source_ding()
    # Hook teaser and thick drums establish a musical identity before the motion.
    kick(.65, .175)
    bass(.65, 30, .24, .095)
    hook(.65, .78, .038)
    snare(1.025, .095)
    cymbal(.8375, .020)
    kick(1.40, .17)
    bass(1.40, 37, .23, .095)
    cymbal(1.5875, .023, opened=True)
    snare(1.775, .079, True, False)
    zipper(2.0, .55, .038, False, 'fast morph friction')
    click(2.08, .057, 2600, 'morph sync click one')
    click(2.24, .062, 2050, 'morph sync click two')
    click(2.42, .067, 1510, 'morph sync click three')
    zipper(2.50, .05, .032, False, 'high-speed field intake')
    click(2.55, .072, 890, 'morph closure and high-speed field onset')
    tom(2.55, 42, .055, .14)
    # Original groove pickup is retained as a boost after the new 2.55 s launch.
    drum_fill(3.1, True)
    drum_bar(3.1, 0, 1., True)
    cymbal(3.1, .064, crash=True, pan=-.15)
    hook(3.1, 1.16, .048)
    hook(4.225, 1.26, .044)
    kick(4.6, .205)
    bass(4.6, 30, .25, .112, 1.2)
    snare(4.975, .116)
    cymbal(4.7875, .026, opened=True)
    # One continuous air profile replaces the former two passes and whip effects.
    flight_air()
    drum_bar(5.32, 1, 1.03, True)
    hook(5.32, 1.35, .048)
    hook(6.07, 1.43, .042, True)
    # Continue a cleaner version of the same groove through the longer convergence.
    kick(6.82, .17)
    bass(6.82, 30, .27, .096)
    snare(7.195, .090, False, False)
    cymbal(7.0075, .022)
    cymbal(7.3825, .020)
    kick(7.57, .17)
    bass(7.57, 37, .20, .093, .8)
    drum_fill(8.05, True)
    # Contact now lands after the 1.5-second convergence; the intake completes at 8.75.
    kick(8.05, .205, True)
    bass(8.05, 30, .27, .122, 1.2)
    tom(8.05, 42, .10, .20)
    cymbal(8.05, .035, crash=True, pan=-.1)
    for t, f, g in [(8.17, 1150, .031), (8.40, 1450, .033), (8.63, 1800, .035)]:
        click(t, g, f, 'receiver intake articulation')
    zipper(8.07, .68, .055, True, 'receiver swallow texture')
    tom(8.46875, 54, .085, .14, -.23)
    tom(8.5625, 45, .11, .15, .22)
    snare(8.65625, .088, True, False)
    # Layered kick, snare/clap, crash and octave body form a full but brief impact.
    kick(8.75, .25, True)
    snare(8.75, .132)
    cymbal(8.75, .067, crash=True, pan=.12)
    bass(8.75, 30, .38, .132, 1.05)
    hook_note(8.75, 54, .37, .045, 1.1, -.12)
    hook_note(8.75, 61, .28, .025, 1.0, .12)
    click(8.88, .043, 970, 'receiver tiny latch')
    # Retain the musical brand sting and repeat the exact source-ding synthesis.
    hook(8.88, 1.05, .046)
    source_ding(9.05)
    # A cleaner kit continues through the logo hold; there is no long empty drop.
    snare(9.175, .082, False, False)
    cymbal(8.9875, .020)
    cymbal(9.3625, .021)
    kick(9.55, .16)
    bass(9.55, 30, .23, .091, .8)
    cymbal(9.7375, .022, opened=True)
    snare(9.925, .075, False, False)
    # Keep the underlying music; the former separate 10.2 s Found crash/hook accent is removed.
    drum_bar(10.2, 0, .93, True)
    click(9.9, .022, 1450, 'first payoff line edit tick')
    click(10.15, .022, 1800, 'second payoff line edit tick')
    drum_bar(11.7, 2, .90, True)
    hook(12.075, .90, .036)
    kick(13.2, .178)
    bass(13.2, 30, .24, .098)
    cymbal(13.3875, .020)
    snare(13.575, .094)
    drum_fill(14.0, False)
    # A short drum stop focuses the final brand hit.
    kick(14.0, .225, True)
    snare(14.0, .105)
    cymbal(14.0, .055, crash=True, pan=.16)
    bass(14.0, 30, .39, .128, .86)
    hook(14.0, 1.0, .047)
    snare(14.375, .089)
    cymbal(14.1875, .023)
    kick(14.75, .17)
    bass(14.75, 37, .23, .098, .75)
    cymbal(14.9375, .024, opened=True)
    snare(15.125, .071)
    hook(15.125, .72, .029)
    kick(15.5, .135)
    bass(15.5, 30, .34, .085, .68)
    cymbal(15.6875, .017)
    tom(15.78125, 45, .055, .20, -.16)
    cymbal(15.875, .015, opened=True, pan=.19)
    # The riff resolves to F# and decays in timed oscillator echoes, not a sustained pad.
    for k in range(5):
        hook_note(15.95 + .375 * k, 66, .38, .021 * .46 ** k, .55,
                  .22 if k % 2 else -.22)
        EVENTS[-1]['kind'] = 'resolved synth-hook tail repeat'


def write_raw():
    raw = ROOT / '.synthesis-f32le.raw'
    samples = array('f')
    highpass_state = [0., 0.]
    a = 1 - math.exp(-TAU * 25 / SR)
    peak, energy = 0., 0.
    for i in range(N):
        t = i / SR
        gate = 1.
        if 13.930 <= t < 13.942:
            gate = 1 - smooth((t - 13.930) / .012)
        elif 13.942 <= t < 14.0:
            gate = 0.
        fade = smooth(t / .005) * smooth((DURATION - t - 1 / SR) / .30)
        for ch in range(2):
            highpass_state[ch] += a * (BUS[ch][i] - highpass_state[ch])
            v = (BUS[ch][i] - highpass_state[ch]) * gate * fade
            samples.append(v)
            peak = max(peak, abs(v))
            energy += v * v
    if sys.byteorder != 'little':
        samples.byteswap()
    raw.write_bytes(samples.tobytes())
    return raw, dict(peak_dbfs=20 * math.log10(peak), rms_dbfs=10 * math.log10(energy / (2 * N)))


def ffmpeg(args):
    process = subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', *args],
                             capture_output=True, text=True, check=True)
    return process.stderr


def report(stderr):
    return json.loads(re.findall(r'\{[\s\S]*?\}', stderr)[-1])


def main():
    compose()
    raw, raw_stats = write_raw()
    inp = ['-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', str(raw)]
    # -1.5 dBTP internal ceiling leaves a little margin for resampling and AAC.
    target = 'loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json'
    first = report(ffmpeg([*inp, '-af', target, '-f', 'null', '-']))
    af = ('loudnorm=I=-14:TP=-1.5:LRA=9:linear=true:print_format=json'
          f':measured_I={first["input_i"]}:measured_TP={first["input_tp"]}'
          f':measured_LRA={first["input_lra"]}:measured_thresh={first["input_thresh"]}'
          f':offset={first["target_offset"]}')
    output = ROOT / 'jjintern-revision-11-original-score.wav'
    normalization = report(ffmpeg(['-y', *inp, '-af', af, '-ar', str(SR), '-ac', '2',
                                   '-c:a', 'pcm_s24le', '-t', '18.000', str(output)]))
    measurement = report(ffmpeg(['-i', str(output), '-af', target, '-f', 'null', '-']))
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                       '-show_format', '-of', 'json', str(output)], text=True))
    decoded = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(output),
                                      '-f', 'f32le', '-acodec', 'pcm_f32le', '-'])
    samples = array('f')
    samples.frombytes(decoded)
    if sys.byteorder != 'little':
        samples.byteswap()
    peak = max(abs(v) for v in samples)
    assert len(samples) == 2 * N and float(probe['streams'][0]['duration']) == DURATION
    assert peak < 1 and all(v == 0 for v in samples[-2:])
    assert float(measurement['input_tp']) <= -1.3, 'True peak exceeded required WAV ceiling'
    aac = ROOT / '.aac-check.m4a'
    ffmpeg(['-y', '-i', str(output), '-c:a', 'aac', '-b:a', '320k', str(aac)])
    aac_measurement = report(ffmpeg(['-i', str(aac), '-af', target, '-f', 'null', '-']))
    aac.unlink()
    ffmpeg(['-y', '-i', str(output), '-filter_complex',
            'showwavespic=s=1800x420:split_channels=1:colors=0071e3|203145',
            '-frames:v', '1', '-update', '1', str(ROOT / 'waveform.png')])
    manifest = {
        'title': 'JJIntern revision11 — stationary flight, convergence and capture',
        'source': 'build_score.py', 'output': output.name,
        'provenance': 'Reproducible staging adaptation of revision10, retaining the original revision09 160 BPM composition, musical hook, timbres and seed. Whip-specific effects are removed; capture, brand sting and copy cues are retimed. A cleaner existing groove section extends the convergence. Every sound is synthesized anew from analytic oscillators, a mathematically generated band-limited saw table, deterministic noise, resonant filters and envelopes. No prior WAV, sample, recording, loop, soundfont, voiceover or external impulse response is read.',
        'external_audio_inputs': [], 'voiceover': False,
        'duration_seconds': DURATION, 'sample_rate_hz': SR, 'channels': 2,
        'pcm_bit_depth': 24, 'samples_per_channel': N, 'tempo_bpm': BPM,
        'beat_seconds': BEAT, 'random_seed': SEED,
        'musical_hook': {'notes': ['F#4', 'A4', 'E4'], 'midi': [66, 69, 64],
                         'rhythm_in_beats': [0, .75, 1.5],
                         'timbre': 'Detuned band-limited saws, pulse difference, saturation and an envelope-controlled resonant filter',
                         'development': 'Opening teaser; two flight statements and an octave variation; motif-based brand sting; payoff reprise; final F# resolution and echoes'},
        'kit': ['Layered sub/body/beater kick', 'Tuned body-and-wire snare',
                'Stereo three-burst noise claps', 'Open and closed broad cymbals',
                'Short crash cymbal', 'Pitched toms and snare fills'],
        'arrangement': 'Retains the 160 BPM electro-break composition, full kit, three-note hook, bass and fills. Air begins at 2.0, builds during the stationary-packet speed field from 2.55 to 6.55, decelerates during convergence to 8.05 and tapers through intake to 8.75. Contact, swallow and latch have separate cues. The unchanged source-style ding repeats at 9.05 for the settled logo and Found bubble; payoff ticks occur at 9.9 and 10.15. The sign-off and tail remain at their existing times.',
        'changes_from_revision10': ['Removed the 5.15–5.32 whip filter, snare glitch, tom, pre-whip cymbal roll, 5.32 crash and master-bus glitch stop',
            'Replaced two air segments with one continuous build/deceleration/capture profile from 2.0 to 8.75',
            'Retimed capture fill/contact to 8.05, swallow impact to 8.75 and latch to 8.88',
            'Retimed the identical second ding to 9.05 and payoff ticks to 9.9/10.15',
            'Retained the musical material, extending its cleaner groove through convergence; sign-off remains at 14.0'],
        'synchronization': [
            {'at_s': .18, 'event': 'isolated source ding'},
            {'from_s': 2.0, 'to_s': 2.55, 'event': 'fast morph friction'},
            {'at_s': 2.08, 'event': 'morph click one'},
            {'at_s': 2.24, 'event': 'morph click two'},
            {'at_s': 2.42, 'event': 'morph click three'},
            {'at_s': 2.50, 'event': 'high-speed field intake'},
            {'at_s': 2.55, 'event': 'morph closure and stationary-packet speed-field onset'},
            {'from_s': 2.0, 'to_s': 8.75, 'event': 'continuous morph, flight, convergence and capture air profile'},
            {'from_s': 2.55, 'to_s': 6.55, 'event': 'four-second stationary-packet flight air build'},
            {'from_s': 2.725, 'to_s': 3.1, 'event': 'retained snare/tom musical pickup'},
            {'at_s': 3.1, 'event': 'retained groove boost with crash and hook'},
            {'from_s': 6.55, 'to_s': 8.05, 'event': 'air brightness and level ease down during convergence'},
            {'from_s': 7.675, 'to_s': 8.05, 'event': 'retimed capture drum fill'},
            {'at_s': 8.05, 'event': 'capture contact'},
            {'from_s': 8.07, 'to_s': 8.75, 'event': 'descending intake texture and tom pickup'},
            {'at_s': 8.75, 'event': 'swallow impact: layered kick, snare/clap, crash and octave body'},
            {'at_s': 8.88, 'event': 'tiny mechanical latch and motif-based brand sting'},
            {'at_s': 9.05, 'event': 'second identical source-style ding for settled logo/Found bubble'},
            {'from_s': 9.05, 'to_s': 9.9, 'event': 'brief Found hold with retained music'},
            {'at_s': 10.2, 'event': 'underlying groove continues without the former standalone Found accent'},
            {'at_s': 9.9, 'event': 'first copy-line tick'},
            {'at_s': 10.15, 'event': 'second copy-line tick'},
            {'from_s': 13.942, 'to_s': 14.0, 'event': 'short pre-sign-off stop'},
            {'at_s': 14.0, 'event': 'strong sign-off downbeat and hook'},
            {'from_s': 14.0, 'to_s': 16.0, 'event': 'rhythmic tail with full F# resolution'},
            {'from_s': 16.0, 'to_s': 18.0, 'event': 'decaying analytically synthesized hook echoes'}],
        'mastering': {'target_integrated_lufs': -14, 'internal_true_peak_ceiling_dbtp': -1.5,
                      'required_wav_true_peak_max_dbtp': -1.3,
                      'normalization_type': normalization['normalization_type'], 'raw_synthesis_stats': raw_stats},
        'measured_final': {'integrated_lufs': float(measurement['input_i']),
                           'true_peak_dbtp': float(measurement['input_tp']),
                           'loudness_range_lu': float(measurement['input_lra']),
                           'sample_peak_dbfs': 20 * math.log10(peak),
                           'duration_seconds': float(probe['streams'][0]['duration']),
                           'samples_per_channel': len(samples) // 2,
                           'last_stereo_sample': list(samples[-2:]),
                           'clipped_samples': sum(abs(v) >= 1 for v in samples)},
        'aac_320k_roundtrip_check': {'integrated_lufs': float(aac_measurement['input_i']),
                                    'true_peak_dbtp': float(aac_measurement['input_tp'])},
        'inspection': {'performed': ['composition, source and timing inspection', 'duration/sample count/codec check',
                                     'integrated loudness and true-peak analysis', 'zero endpoints and no clipped samples',
                                     '320 kbps AAC encode/decode headroom check', 'waveform generated for inspection'],
                       'not_performed': ['subjective human listening', 'physical-phone playback'],
                       'limitation': 'Source, musical arrangement and measurements are inspected; subjective listening is not claimed.'},
        'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'events': sorted(EVENTS, key=lambda event: event['start_s'])}
    (ROOT / 'audio-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (ROOT / 'loudness-analysis.json').write_text(json.dumps(dict(first_pass=first, normalization=normalization,
        final_measurement=measurement, aac_320k_roundtrip=aac_measurement), indent=2) + '\n')
    raw.unlink()
    print(json.dumps(dict(output=str(output), measured_final=manifest['measured_final'],
                         aac_320k_roundtrip=manifest['aac_320k_roundtrip_check']), indent=2))


if __name__ == '__main__':
    main()
