#!/usr/bin/env python3
"""Find your focus — an original 32-second, 120 BPM electronic film score.

Requires Python's standard library and ffmpeg/ffprobe only. Every sound is
synthesized here from oscillators, deterministic noise, envelopes and filters.
No recordings, samples, prior scores, soundfonts, IRs or external audio are read.
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
SR, DURATION, BPM, SEED = 48000, 32.0, 120, 2026102041
N, TAU, BEAT = int(SR * DURATION), math.tau, 60 / BPM
BUS = {name: [array('f', [0]) * N, array('f', [0]) * N]
       for name in ('drums', 'music', 'effects', 'space')}
EVENTS, KICKS = [], []
TABLE_SIZE = 4096
SAW = [sum((-1) ** (h + 1) * math.sin(TAU * h * j / TABLE_SIZE) / h
           for h in range(1, 18)) * .60 for j in range(TABLE_SIZE)]


def hz(note):
    return 440 * 2 ** ((note - 69) / 12)


def smooth(x):
    x = max(0., min(1., x))
    return x * x * (3 - 2 * x)


def edge(t, length, attack=.002, release=.03):
    return smooth(t / attack) * smooth((length - t) / release)


def saw(phase):
    p = (phase % 1) * TABLE_SIZE
    i = int(p)
    f = p - i
    return SAW[i] * (1 - f) + SAW[(i + 1) % TABLE_SIZE] * f


def add(start, length, synth, gain, pan, kind, bus='music', send=.0, **params):
    begin = round(start * SR)
    count = max(0, min(round(length * SR), N - begin))
    lg, rg = gain * math.cos((pan + 1) * math.pi / 4), gain * math.sin((pan + 1) * math.pi / 4)
    for i in range(count):
        v = synth(i / SR)
        BUS[bus][0][begin + i] += lg * v
        BUS[bus][1][begin + i] += rg * v
        if send:
            BUS['space'][0][begin + i] += lg * v * send
            BUS['space'][1][begin + i] += rg * v * send
    EVENTS.append(dict(start_s=round(start, 5), duration_s=length, kind=kind, bus=bus,
                       gain=gain, pan=pan, **params))


def kick(start, gain=.34, strong=False, soft=False):
    length, base = (.40, 48.5) if strong else (.31, 51.9)
    rng = random.Random(SEED + round(start * SR) + 1)
    low = 0.
    a = 1 - math.exp(-TAU * 3100 / SR)
    def synth(t):
        nonlocal low
        phase = TAU * (base * t + 155 * .013 * (1 - math.exp(-t / .013)))
        sub = .89 * math.sin(phase) * math.exp(-t / (.113 if strong else .085))
        body = .25 * math.sin(TAU * (102 * t + 45 * .009 * (1 - math.exp(-t / .009)))) * math.exp(-t / .027)
        low += a * (rng.uniform(-1, 1) - low)
        beater = (.07 if soft else .28) * low * math.exp(-t / .003)
        return math.tanh(1.55 * (sub + body + beater)) * edge(t, length, .0007, .04)
    add(start, length, synth, gain, 0, 'rounded sub/body/beater kick', 'drums', strong=strong)
    KICKS.append((start, .26 if strong else .22))


def clap(start, gain=.060, pan=0):
    rng = random.Random(SEED + round(start * SR) + round(pan * 900) + 5)
    hi = lo = 0.
    a, b = 1 - math.exp(-TAU * 7600 / SR), 1 - math.exp(-TAU * 1400 / SR)
    length = .19
    def synth(t):
        nonlocal hi, lo
        v = rng.uniform(-1, 1)
        hi += a * (v - hi)
        lo += b * (v - lo)
        clusters = sum(g * math.exp(-(t - offset) / .0055) * smooth((t - offset) / .0007)
                       for offset, g in ((0, .85), (.012, .73), (.023, 1)) if t >= offset)
        tail = .40 * math.exp(-max(0, t - .022) / .038) * smooth((t - .02) / .005)
        return (hi - lo) * (clusters + tail) * edge(t, length, .0004, .025)
    add(start, length, synth, gain, pan, 'dry stereo clustered clap', 'drums', send=.11)


def snare(start, gain=.185, ghost=False, stereo=True):
    rng = random.Random(SEED + round(start * SR) + 11)
    hi = lo = 0.
    a, b = 1 - math.exp(-TAU * 9500 / SR), 1 - math.exp(-TAU * 950 / SR)
    length = .12 if ghost else .23
    def synth(t):
        nonlocal hi, lo
        v = rng.uniform(-1, 1)
        hi += a * (v - hi)
        lo += b * (v - lo)
        phase = TAU * (180 * t + 60 * .011 * (1 - math.exp(-t / .011)))
        tone = (.67 * math.sin(phase) + .18 * math.sin(TAU * 305 * t)) * math.exp(-t / .043)
        noise = .73 * (hi - lo) * math.exp(-t / (.025 if ghost else .052))
        return math.tanh(1.65 * (tone + noise)) * edge(t, length, .0008, .035)
    add(start, length, synth, gain, -.025, 'snare ghost' if ghost else 'tuned body and wire snare', 'drums', send=.065)
    if stereo and not ghost:
        clap(start + .006, gain * .34, -.30)
        clap(start + .011, gain * .29, .30)


def hat(start, gain=.047, opened=False, pan=.35):
    length, decay = (.22, .055) if opened else (.052, .010)
    rng = random.Random(SEED + round(start * SR) + 17)
    hi = lo = 0.
    a, b = 1 - math.exp(-TAU * 13600 / SR), 1 - math.exp(-TAU * 5300 / SR)
    def synth(t):
        nonlocal hi, lo
        w = rng.uniform(-1, 1)
        hi += a * (w - hi)
        lo += b * (w - lo)
        metal = (math.sin(TAU * 6623 * t) + math.sin(TAU * 9137 * t) + math.sin(TAU * 11749 * t)) / 3
        return (.88 * (hi - lo) + .12 * metal) * math.exp(-t / decay) * edge(t, length, .0006, .01)
    add(start, length, synth, gain, pan, 'open hat' if opened else 'closed hat', 'drums')


def tom(start, midi=45, gain=.18, pan=0):
    f, length = hz(midi), .24
    def synth(t):
        p = TAU * (f * t + 45 * .026 * (1 - math.exp(-t / .026)))
        return math.tanh(1.4 * (math.sin(p) + .18 * math.sin(p * 1.998))) * math.exp(-t / .065) * edge(t, length, .001, .025)
    add(start, length, synth, gain, pan, 'tuned rounded tom', 'drums', send=.13, midi=midi)


def tick(start, gain=.034, pan=0, frequency=1800, kind='precision tick'):
    length = .036
    rng = random.Random(SEED + round(start * SR) + 23)
    def synth(t):
        return (.45 * math.sin(TAU * frequency * t) + .23 * rng.uniform(-1, 1)) * math.exp(-t / .0048) * edge(t, length, .0005, .007)
    add(start, length, synth, gain, pan, kind, 'effects', send=.13, frequency_hz=frequency)


def bass(start, note=38, length=.25, gain=.16, bright=1):
    f = hz(note)
    low = band = 0.
    def synth(t):
        nonlocal low, band
        raw = .72 * saw(f * t) + .28 * math.sin(TAU * f * t)
        cutoff = 160 + 820 * bright * math.exp(-t / .075)
        c = 2 * math.sin(math.pi * cutoff / SR)
        low += c * band
        high = math.tanh(raw * 2) - low - .94 * band
        band += c * high
        tone = .68 * math.tanh(1.7 * low) + .28 * math.sin(TAU * f * t)
        return tone * edge(t, length, .006, .045)
    add(start, length, synth, gain, 0, 'resonant syncopated bass', note=note,
        fundamental_hz=f, length_beats=length / BEAT)


def pluck(start, note, length=.48, gain=.073, pan=0, bright=1, delay=True):
    """A firm, slightly metallic wood/glass attack with a rounded harmonic body."""
    f = hz(note)
    low = 0.
    a = 1 - math.exp(-TAU * 5200 / SR)
    def synth(t):
        nonlocal low
        env = math.exp(-t / (.13 + .025 * bright))
        fm = .75 * bright * math.exp(-t / .047) * math.sin(TAU * f * 2.003 * t)
        core = math.sin(TAU * f * t + fm)
        body = .27 * math.sin(TAU * f * 1.0023 * t) + .19 * math.sin(TAU * f * 2 * t) * math.exp(-t / .07)
        edgeharm = .12 * saw(f * t) * math.exp(-t / .055)
        low += a * ((core + body + edgeharm) / 1.25 - low)
        return low * env * edge(t, length, .0028, .08)
    add(start, length, synth, gain, pan, 'wood-glass FM pluck', send=.20, midi=note, brightness=bright)
    if delay:
        # Analytic repeats are separately synthesized, quieter and darker.
        pluck(start + .375, note, .36, gain * .17, -pan if abs(pan) > .1 else .4, bright * .6, False)
        pluck(start + .750, note, .30, gain * .065, pan, bright * .4, False)


def chord(start, notes, length=.9, gain=.050, bright=1, spread=.5):
    """Short opening-filter saw/triangle stabs; no sustained wallpaper pad."""
    for k, note in enumerate(notes):
        f = hz(note)
        low = band = 0.
        def synth(t, f=f):
            nonlocal low, band
            raw = .42 * saw(f * .9985 * t) + .38 * saw(f * 1.0015 * t) + .20 * math.sin(TAU * f * t)
            cutoff = 580 + 2600 * bright * math.exp(-t / .14)
            c = 2 * math.sin(math.pi * cutoff / SR)
            low += c * band
            high = raw - low - 1.25 * band
            band += c * high
            envelope = math.exp(-t / (length * .37)) * edge(t, length, .012, .13)
            return math.tanh(1.8 * low) * envelope
        pan = spread * (k / max(1, len(notes) - 1) * 2 - 1)
        add(start, length, synth, gain, pan, 'detuned harmonic chord stab', send=.32, midi=note, brightness=bright)


def sweep(start, length, gain=.055, rising=True, pan=0):
    rng = random.Random(SEED + round(start * SR) + 31)
    hi = lo = 0.
    def synth(t):
        nonlocal hi, lo
        u = t / length
        p = u if rising else 1 - u
        cutoff = 500 + 7300 * p * p
        a, b = 1 - math.exp(-TAU * cutoff / SR), 1 - math.exp(-TAU * 350 / SR)
        w = rng.uniform(-1, 1)
        hi += a * (w - hi)
        lo += b * (w - lo)
        envelope = (p ** 1.5) * edge(t, length, .03, .018)
        texture = .77 + .23 * math.sin(TAU * (17 * t + 31 * t * t)) ** 2
        return (hi - lo) * envelope * texture
    add(start, length, synth, gain, pan, 'short rising transition' if rising else 'short impact air decay', 'effects')


def impact(start, power=1, notes=(62, 69, 72, 76), strong=True):
    kick(start, .38 * power, strong)
    tom(start + .004, 38, .14 * power, -.08)
    chord(start, notes, 1.25, .058 * power, 1.05, .62)
    sweep(start + .005, .35, .075 * power, False, .12)
    tick(start, .074 * power, 0, 1100, 'scene contact accent')


def groove(start, variation=0, power=1, root=38, hats=True, full=True):
    patterns = [(0, 1.5, 2.75, 3.5), (0, .75, 2, 3.25), (0, 1.75, 2.5, 3.5)]
    for j, step in enumerate(patterns[variation % 3]):
        if not full and j > 2:
            continue
        if step != 0:  # Section impact or the caller supplies the downbeat.
            kick(start + step * BEAT, power * (.30 if j != 2 else .275))
    for step in (1, 3):
        snare(start + step * BEAT, .19 * power, stereo=full)
    if full:
        snare(start + (2.5 if variation % 2 else .75) * BEAT, .045 * power, True, False)
    if hats:
        for i in range(8):
            # Swing only the second sixteenth; the quarter and eighth grid is stable.
            hat(start + i * .25, (.041 if i % 2 else .028) * power,
                opened=(i == 7 and variation % 2 == 1), pan=.28 if i % 2 else -.22)
        if full:
            hat(start + .391, .023 * power, pan=-.45)
            hat(start + 1.391, .025 * power, pan=.48)
    riffs = [((0, 0, .29), (.75, 0, .14), (1.5, 7, .18), (2.75, 10, .20), (3.5, 0, .16)),
             ((0, 0, .28), (.75, 12, .15), (2, 7, .25), (3.25, 3, .19)),
             ((0, 0, .30), (1.75, 0, .15), (2.5, 7, .18), (3.5, 10, .17))]
    for step, interval, length in riffs[variation % 3]:
        bass(start + step * BEAT, root + interval, length, .155 * power, .8 if not full else 1.05)


def fill(end, gain=.85):
    snare(end - .5, .09 * gain, True, False)
    tom(end - .375, 57, .13 * gain, -.3)
    tom(end - .25, 50, .16 * gain, .3)
    snare(end - .125, .13 * gain, False, False)


def motif(start, gain=.075, high=False):
    # One identifiable syncopated phrase: D, A, C, F, then E resolves to D.
    for off, note, strength, pan in ((0, 74, 1, -.24), (.375, 69, .78, .28),
                                    (.875, 72, .86, -.13), (1.25, 77, .94, .25)):
        pluck(start + off, note + (12 if high and off == 1.25 else 0), .48,
              gain * strength, pan, 1.1 if high else .9)


def compose():
    # 0–4: unaligned sources become a regular pulse; the hook begins as fragments.
    kick(0, .25, False, True)
    bass(0, 38, .45, .11, .45)
    chord(0, (62, 69, 76), 1.2, .031, .38)
    for t, note, pan, g in ((.18, 74, -.58, .060), (.83, 69, .53, .047),
                             (1.42, 72, -.34, .054), (1.875, 77, .44, .058),
                             (2.125, 74, -.20, .060), (2.625, 69, .18, .058),
                             (3.125, 72, -.12, .063)):
        pluck(t, note, .48, g, pan, .65)
    for t, pan in ((.55, .65), (1.07, -.7), (1.71, .45), (2.4, -.4), (2.85, .3)):
        tick(t, .043, pan, 1550 + 130 * t, 'scattered search tick')
    kick(1.5, .22, False, True)
    kick(2, .26)
    bass(2, 38, .28, .13, .65)
    snare(2.5, .14, False, False)
    kick(3, .27)
    hat(2.75, .04, True)
    sweep(3.25, .70, .065, True, -.12)
    fill(4, .83)

    # 4–8: pieces lock to the beat. Drums and bass carry the energy.
    impact(4, 1)
    groove(4, 0, 1)
    motif(4.125, .073)
    kick(6, .33)
    groove(6, 1, 1, 38)
    chord(6.125, (65, 69, 72, 76), .75, .045, .8)
    pluck(7.125, 76, .55, .066, .3)
    sweep(7.65, .32, .045)

    # 8–12: broad editorial feature reveal; two harmonic colours stay related.
    impact(8, 1.05, (62, 65, 69, 76))
    groove(8, 2, 1.04)
    motif(8.125, .078)
    kick(10, .33)
    groove(10, 0, 1, 34)
    chord(10, (62, 65, 69, 72), .95, .050, .9)
    pluck(10.875, 77, .62, .076, .28)
    pluck(11.375, 76, .48, .059, -.22)
    fill(12, .62)
    sweep(11.6, .36, .045)

    # 12–18: a pocket for the authentic search interaction. Fewer top layers.
    impact(12, .80, (62, 69, 76))
    groove(12, 1, .73, full=False)
    for k, t in enumerate((12.60, 12.78, 12.96, 13.14, 13.32, 13.5, 13.68, 13.86, 14.04, 14.2)):
        tick(t, .036 if k < 9 else .052, -.13 + k * .028, 1700 + 40 * k, 'search character/result tick')
    kick(14, .27)
    groove(14, 2, .78, full=False)
    chord(14.25, (60, 65, 69, 74), .85, .040, .65)
    pluck(14.625, 74, .46, .055, -.25)
    pluck(15.375, 69, .48, .046, .25)
    kick(16, .28)
    groove(16, 0, .81, full=False)
    chord(16, (60, 67, 72, 76), 1.05, .040, .72)
    pluck(16.875, 76, .50, .056, -.25)
    pluck(17.375, 77, .46, .059, .25)
    sweep(17.5, .45, .057)

    # 18–22: circular rhythmic detail supports the orbital cadence graphic.
    impact(18, 1.05, (62, 65, 69, 76))
    groove(18, 1, .97)
    kick(20, .34)
    groove(20, 2, 1.02)
    chord(20.125, (62, 65, 69, 74), .9, .052, 1)
    for i, note in enumerate((74, 81, 77, 76, 74, 69, 72, 76)):
        t = 18.25 + i * .375
        pluck(t, note, .38, .053 if i % 2 else .065, math.sin(i * 1.1) * .55, .8)
        tick(t, .026, math.sin(i * 1.1 + 1) * .5, 1200 + i * 110, 'orbital indexed tick')
    fill(22, 1)
    sweep(21.25, .69, .072, True, .12)

    # 22–28: richest phrase, broad chords and one octave variation for payoff.
    impact(22, 1.14, (62, 65, 69, 76))
    groove(22, 0, 1.10)
    motif(22.125, .086, True)
    kick(24, .37)
    groove(24, 1, 1.10, 34)
    chord(24, (62, 65, 69, 72), 1.2, .058, 1.2, .7)
    pluck(24.375, 77, .57, .078, -.27, 1.2)
    pluck(25.125, 76, .52, .072, .27)
    kick(26, .36)
    groove(26, 2, 1.07, 36)
    chord(26, (60, 67, 72, 76), 1.1, .059, 1.10, .7)
    pluck(26.125, 72, .45, .071, -.25)
    pluck(26.875, 76, .55, .080, .24)
    pluck(27.375, 81, .44, .067, -.14)
    fill(28, 1)
    sweep(27.375, .56, .080)

    # 28–32: brand contact, then a deliberate resolved three-tone sonic sign-off.
    impact(28, 1.15, (62, 65, 69, 76))
    bass(28, 38, .55, .19, 1)
    snare(28.5, .15)
    hat(28.25, .037, True, .25)
    kick(29, .25)
    bass(29, 38, .34, .12, .5)
    hat(29.25, .027, False, -.3)
    tom(29.5, 50, .095, .25)
    for t, note, g, pan in ((28.13, 74, .087, -.25), (28.625, 81, .078, .25),
                           (29.25, 76, .066, -.20), (29.875, 74, .086, 0)):
        pluck(t, note, .9, g, pan, .8)
    chord(29.875, (62, 69, 74), 1.50, .038, .35, .55)


def build_mix():
    """Short early reflections and music-only sidechain preserve crisp transients."""
    result = [array('f', [0]) * N, array('f', [0]) * N]
    # Fixed diffuse taps, not a sampled impulse response, no endless wash.
    taps = ((.031, .34, 1), (.047, .29, 0), (.079, .23, 1), (.113, .19, 0),
            (.163, .14, 1), (.227, .095, 0), (.311, .060, 1))
    for delay, gain, cross in taps:
        offset = round(delay * SR)
        for ch in range(2):
            source = BUS['space'][1 - ch if cross else ch]
            for i in range(offset, N):
                result[ch][i] += source[i - offset] * gain
    duck = array('f', [1]) * N
    for start, depth in KICKS:
        at = round(start * SR)
        for i in range(min(round(.25 * SR), N - at)):
            t = i / SR
            v = 1 - depth * math.exp(-t / .075) * smooth(t / .002)
            duck[at + i] = min(duck[at + i], v)
    hp = [0., 0.]
    a = 1 - math.exp(-TAU * 25 / SR)
    data = array('f')
    energy, peak = 0., 0.
    for i in range(N):
        t = i / SR
        # Brief negative spaces immediately before key downbeats; not extra noise.
        pre = 1.
        for stop in (4., 22., 28.):
            if stop - .070 <= t < stop:
                pre = 1 - smooth((t - stop + .070) / .020)
        ending = 1 - smooth((t - 31.10) / .40)
        fader = smooth(t / .004) * ending
        for ch in range(2):
            dry = BUS['drums'][ch][i] + BUS['music'][ch][i] * duck[i] + BUS['effects'][ch][i]
            v = (dry * pre + result[ch][i] * (.55 + .45 * pre)) * fader
            hp[ch] += a * (v - hp[ch])
            v = (v - hp[ch]) * fader
            data.append(v)
            energy += v * v
            peak = max(peak, abs(v))
    if sys.byteorder != 'little':
        data.byteswap()
    raw = ROOT / '.synthesis-f32le.raw'
    raw.write_bytes(data.tobytes())
    return raw, dict(sample_peak_dbfs=20 * math.log10(peak), rms_dbfs=10 * math.log10(energy / (2 * N)))


def ffmpeg(args):
    return subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', *args],
                          text=True, capture_output=True, check=True).stderr


def report(stderr):
    return json.loads(re.findall(r'\{[\s\S]*?\}', stderr)[-1])


def main():
    compose()
    raw, raw_stats = build_mix()
    print('Synthesis complete; mastering and verifying.', flush=True)
    inp = ['-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', str(raw)]
    # Broad gentle glue, then measured two-pass loudness normalization.
    glue = 'highpass=f=27,lowpass=f=17000,acompressor=threshold=0.30:ratio=1.8:attack=12:release=110:makeup=1.10'
    norm = 'loudnorm=I=-15:TP=-1.6:LRA=9:print_format=json'
    first = report(ffmpeg([*inp, '-af', glue + ',' + norm, '-f', 'null', '-']))
    af = (glue + ',loudnorm=I=-15:TP=-1.6:LRA=9:linear=true:print_format=json'
          f':measured_I={first["input_i"]}:measured_TP={first["input_tp"]}'
          f':measured_LRA={first["input_lra"]}:measured_thresh={first["input_thresh"]}'
          f':offset={first["target_offset"]}')
    output = ROOT / 'jjintern-find-your-focus-original-score.wav'
    normalization = report(ffmpeg(['-y', *inp, '-af', af, '-ar', str(SR), '-ac', '2',
                                   '-c:a', 'pcm_s24le', '-t', '32.000', str(output)]))
    measurement = report(ffmpeg(['-i', str(output), '-af', norm, '-f', 'null', '-']))
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                       '-show_format', '-of', 'json', str(output)], text=True))
    decoded = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(output),
                                      '-f', 'f32le', '-acodec', 'pcm_f32le', '-'])
    samples = array('f')
    samples.frombytes(decoded)
    if sys.byteorder != 'little':
        samples.byteswap()
    peak = max(abs(v) for v in samples)
    assert len(samples) == N * 2
    assert float(probe['streams'][0]['duration']) == DURATION
    assert all(v == 0 for v in samples[-round(.20 * SR) * 2:])
    assert peak < 1
    assert float(measurement['input_tp']) <= -1.0
    assert -16 <= float(measurement['input_i']) <= -14
    aac = ROOT / '.aac-check.m4a'
    ffmpeg(['-y', '-i', str(output), '-c:a', 'aac', '-b:a', '320k', str(aac)])
    aac_measurement = report(ffmpeg(['-i', str(aac), '-af', norm, '-f', 'null', '-']))
    aac.unlink()
    ffmpeg(['-y', '-i', str(output), '-filter_complex',
            'showwavespic=s=1920x480:split_channels=1:colors=0071e3|203145',
            '-frames:v', '1', '-update', '1', str(ROOT / 'waveform.png')])
    ffmpeg(['-y', '-i', str(output), '-lavfi',
            'showspectrumpic=s=1920x640:legend=1:scale=log:fscale=log:color=intensity',
            '-frames:v', '1', '-update', '1', str(ROOT / 'spectrogram.png')])
    manifest = {
        'title': 'Find your focus — JJIntern original score',
        'source': 'build_score.py', 'output': output.name,
        'provenance': 'Original 120 BPM composition and sound design synthesized from analytic oscillators, deterministic noise, band-limited saw tables, envelopes and filters. No samples, loops, recordings, prior WAVs, soundfonts or external impulse responses are read. Generic synthesis techniques draw on the workspace synthesis utilities; the composition, arrangement and score source are new.',
        'external_audio_inputs': [], 'voiceover': False,
        'duration_seconds': DURATION, 'sample_rate_hz': SR, 'channels': 2,
        'pcm_bit_depth': 24, 'samples_per_channel': N, 'tempo_bpm': BPM,
        'beat_seconds': BEAT, 'random_seed': SEED,
        'musical_identity': {'key': 'D minor / extended minor harmony',
            'motif_midi': [74, 69, 72, 77], 'motif_notes': ['D5', 'A4', 'C5', 'F5'],
            'motif_offsets_seconds': [0, .375, .875, 1.25],
            'timbres': ['rounded sub/body/beater kick', 'tuned body-and-wire snare and short stereo clap',
                        'dry swung hats', 'rounded tuned toms', 'mono resonant bass',
                        'wood-glass FM pluck', 'wide detuned harmonic chord stab'],
            'resolution': 'E5 descends to D5 at 29.875; final D/A/D chord and reflections decay, with full silence by 31.5.'},
        'arrangement': [
            {'from_s': 0, 'to_s': 4, 'description': 'Scattered pluck fragments and tactile ticks coalesce into a pulse; brief pre-drop negative space.'},
            {'from_s': 4, 'to_s': 8, 'description': 'First impact, syncopated full-kit groove and low bass; first motif statement.'},
            {'from_s': 8, 'to_s': 12, 'description': 'Broader chord colours underline finance/technology in one place.'},
            {'from_s': 12, 'to_s': 18, 'description': 'Drums and bass continue at reduced intensity; light precise search ticks from 12.6 to 14.2.'},
            {'from_s': 18, 'to_s': 22, 'description': 'Orbiting stereo plucks and indexed ticks add circular rhythmic motion.'},
            {'from_s': 22, 'to_s': 28, 'description': 'Fullest groove, wider chords, higher motif variation and tom/snare pickup.'},
            {'from_s': 28, 'to_s': 32, 'description': 'Strong brand contact; percussion thins and melodic sign-off resolves to D.'}],
        'synchronization': {'major_accents_s': [4, 8, 12, 18, 22, 28],
                            'search_ticks_s': [12.6, 12.78, 12.96, 13.14, 13.32, 13.5, 13.68, 13.86, 14.04, 14.2],
                            'full_silence_from_s': 31.5},
        'mastering': {'target_integrated_lufs': -15, 'internal_true_peak_ceiling_dbtp': -1.6,
                      'required_wav_true_peak_max_dbtp': -1.0, 'normalization_type': normalization['normalization_type'],
                      'raw_synthesis_stats': raw_stats, 'filters': glue,
                      'stereo': 'Mono kick/bass; restrained panning for high percussion and harmonic material; short analytic early reflections.'},
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
                                     'integrated loudness and true-peak analysis', 'zero tail and no clipped samples',
                                     '320 kbps AAC encode/decode headroom check', 'waveform and spectrogram generation'],
                       'not_performed': ['subjective human listening', 'physical-phone playback'],
                       'limitation': 'Musical arrangement and technical measurements are inspected. Subjective listening is not claimed.'},
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
