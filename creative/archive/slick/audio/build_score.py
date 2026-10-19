#!/usr/bin/env python3
"""JJIntern V4 — Weight / Direction. Entirely original procedural synthesis.

No samples, recordings, stock loops, vocal material, external music model or
recorded impulse responses. Python 3.13 + numpy/scipy; ffmpeg for mastering.
"""
from pathlib import Path
import json
import re
import subprocess
import time
import wave
import numpy as np
from scipy import signal
from scipy.io import wavfile

START = time.perf_counter()
OUT = Path(__file__).resolve().parent
SR, SECS, BPM = 48000, 20., 128
N, BEAT = round(SR * SECS), 60 / BPM
PI = np.pi
RNG = np.random.default_rng(41171026)
music = np.zeros((N, 2))
bassbus = np.zeros_like(music)
drums = np.zeros_like(music)
sound = np.zeros_like(music)
kick_duck = np.zeros(N)
events = []


def hz(note):
    return 440 * 2 ** ((note - 69) / 12)


def tt(length):
    return np.arange(round(length * SR)) / SR


def filt(x, cutoff, kind='lowpass', order=2):
    return signal.sosfilt(signal.butter(order, cutoff, kind, fs=SR, output='sos'), x, axis=0)


def decay(t, attack=.002, fall=.16, release=.025):
    return (1 - np.exp(-t / attack)) * np.exp(-t / fall) * np.clip((t[-1] - t) / release, 0, 1)


def add(bus, x, at, gain=1., pan=0., kind=None, note=None):
    i = round(at * SR)
    if i >= N:
        return
    if x.ndim == 1:
        angle = (pan + 1) * PI / 4
        x = np.stack([x * np.cos(angle), x * np.sin(angle)], axis=1)
    count = min(N - i, len(x))
    bus[i:i+count] += x[:count] * gain
    if kind:
        item = {'s': round(at, 6), 'event': kind, 'gain': gain, 'pan': pan}
        if note is not None:
            item['midi_note'] = note
        events.append(item)


def kick(velocity=1.):
    t = tt(.46)
    frequency = 49 + 96 * np.exp(-t / .012) + 19 * np.exp(-t / .052)
    p = 2 * PI * np.cumsum(frequency) / SR
    fundamental = np.sin(p) * np.exp(-t / .115)
    transient = filt(RNG.standard_normal(len(t)), [2600, 9000], 'bandpass') * np.exp(-t / .0016) * .11
    return np.tanh((fundamental + transient) * 1.38) * .80 * velocity * np.minimum(t / .0004, 1) * np.minimum((.46-t) / .03, 1)


def kick_at(at, gain=.85, velocity=1.):
    add(drums, kick(velocity), at, gain, kind='dry punch kick')
    i = round(at * SR)
    n = min(N - i, round(.30 * SR))
    kick_duck[i:i+n] = np.maximum(kick_duck[i:i+n], np.exp(-np.arange(n) / SR / .075))


def bass(note, length=.32, velocity=1.):
    """Centered saw/triangle body and a quiet octave-down sub, no pads/arp."""
    t = tt(length)
    f = hz(note)
    p = 2 * PI * f * t
    saw = sum(np.sin(p * k) / k for k in range(1, 13)) * .57
    smooth = filt(saw, 700)
    bright = filt(saw, 2900)
    opening = np.exp(-t / .065)
    texture = smooth * .26 + bright * opening * .18
    x = .65 * np.sin(p + .22 * np.exp(-t / .08) * np.sin(2*p))
    x += .27 * np.sin(p / 2) + texture
    # A small stable sustain gives each bass note a deliberate physical body.
    shape = (1 - np.exp(-t / .003)) * (.52 + .48 * np.exp(-t / .10))
    shape *= np.minimum(1, np.maximum(length - t, 0) / .040)
    return np.tanh(x * 1.25) / 1.25 * shape * .44 * velocity


def clap(velocity=1., rim=False):
    t = tt(.19)
    n = filt(RNG.standard_normal(len(t)), [1800, 9000], 'bandpass')
    ring = np.sin(2 * PI * 184 * t) * np.exp(-t / .019)
    x = .32 * n * np.exp(-t / (.025 if rim else .040)) + .23 * ring
    x += .09 * n * np.exp(-np.maximum(t-.009, 0) / .019) * (t >= .009)
    return x * np.minimum(t / .0003, 1) * .66 * velocity


def hat(velocity=1., opened=False):
    length = .17 if opened else .055
    t = tt(length)
    white = RNG.standard_normal(len(t))
    metal = sum(np.sin(2 * PI * 2400 * r * t) for r in [1, 1.39, 1.77, 2.41]) * .035
    x = filt(white * .22 + metal, [7200, 16500], 'bandpass')
    return x * decay(t, .00025, .043 if opened else .009, .012) * .39 * velocity


def strike(note=81, length=1.7):
    """One signature metallic/glass strike; not a notification melody."""
    t = tt(length)
    f = hz(note)
    p = 2 * PI * f * t
    x = .60 * np.sin(p + 2.5 * np.exp(-t/.022) * np.sin(p * 1.997)) * np.exp(-t/.38)
    for ratio, gain, fall in [(2.014, .18, .16), (2.987, .065, .09), (4.15, .027, .055)]:
        x += gain * np.sin(p * ratio) * np.exp(-t / fall)
    x += .10 * np.sin(p / 2) * np.exp(-t / .21)
    return x * (1 - np.exp(-t/.0007)) * np.minimum((length-t) / .1, 1) * .43


def tactile(number=0, length=.10):
    t = tt(length)
    n = filt(RNG.standard_normal(len(t)), [650, 6500], 'bandpass')
    f = [420, 610, 840, 1100][number % 4]
    body = np.sin(2 * PI * (f*t + .3*np.exp(-t/.003))) * np.exp(-t/.011)
    return (body * .35 + n * np.exp(-t/.007) * .26) * np.minimum(t/.0003, 1) * .30


def pressure(length, gain=.10):
    t = tt(length)
    q = t / length
    x = filt(RNG.standard_normal(len(t)), [180, 3600], 'bandpass')
    x *= (.6 + .4*np.sin(2*PI*(7*t + 3*t*t/length))**2)
    x += np.sin(2*PI*(78*t + 35*t*t/length)) * .18
    return x * np.sin(PI*q) ** .8 * gain


def passby(length=.35, reverse=False):
    t = tt(length)
    q = t / length
    x = filt(RNG.standard_normal(len(t)), [500, 12000], 'bandpass')
    # A falling oscillator and a shaped air transient imply velocity and mass.
    p = 2*PI*(1050*t - 760*t*t/(2*length))
    x = (x*.37 + np.sin(p)*.042) * np.sin(PI*q)**1.5 * .26
    pan = -1 + 2*q
    if reverse:
        pan = -pan
    return np.stack([x*np.sqrt((1-pan)/2), x*np.sqrt((1+pan)/2)], axis=1)


def chord(notes, length, level=.032):
    t = tt(length)
    y = np.zeros((len(t), 2))
    for j, note in enumerate(notes):
        for channel, detune in enumerate([-.035, .035]):
            p = 2*PI*hz(note+detune)*t
            y[:, channel] += np.sin(p) + .15*np.sin(2*p) + .035*np.sin(3*p)
    shape = np.minimum(t/.035, 1) * np.minimum(np.maximum(length-t, 0)/.3, 1)
    return filt(y, 1800) * shape[:, None] * level


def impact(at, weight=1.):
    t = tt(.72)
    p = 2*PI*(63*t + 2.8*np.exp(-t/.07))
    x = np.sin(p) * np.exp(-t/.17) * .15
    x += filt(RNG.standard_normal(len(t)), [650, 7500], 'bandpass') * np.exp(-t/.033) * .09
    add(sound, x, at, weight, kind='controlled arrival impact')


# 0--1: restrained pressure, not a decorative music introduction.
add(sound, pressure(.85, .045), 0, kind='intro restrained pressure')
add(bassbus, bass(40, .48), .10, .27, kind='intro low intent', note=40)

# 1.05: one sharp, ownable material event marks the example posting.
add(sound, strike(81), 1.05, .98, 0, 'signature metallic glass posting strike', 81)
add(sound, tactile(0), 1.05, .24, 0, 'posting strike physical edge')
# The sound briefly recedes; the posting gets time to register.
for at, note, gain in [(1.8, 40, .28), (2.5, 47, .23)]:
    add(bassbus, bass(note, .24), at, gain, kind='restrained bass anticipation', note=note)

# 3.2--4.65: a card physically compresses into a solid blue packet.
add(sound, pressure(1.40, .080), 3.20, kind='fold compression pressure')
for j, at in enumerate([3.20, 3.47, 3.78, 4.05, 4.30, 4.57]):
    add(sound, tactile(j), at, .48 + .045*j, -.26 + .10*j, 'tactile fold / locking click')
for at, note in [(3.2, 40), (3.78, 40), (4.3, 43)]:
    add(bassbus, bass(note, .18), at, .31, kind='fold rhythmic weight', note=note)

# 4.65--5.65: packet launch. Sound travels L->R for 900 ms, then an
# intentional 100 ms near-silent suspension makes the destination land.
add(sound, passby(.90), 4.65, 1., kind='one-second-window left-to-right packet launch')
add(sound, tactile(3, .08), 4.65, .6, -.65, 'packet release click')

# 5.65: the real website/feed arrives; the compact bass motif is the hook.
impact(5.65, 1.)
add(music, chord([52, 59, 62, 66], 1.3, .040), 5.65, kind='feed arrival Em9 colour')
bar_seconds = 4*BEAT
root_plan = [40, 40, 43, 40, 36, 38, 40]
for bar, root in enumerate(root_plan):
    base = 5.65 + bar*bar_seconds
    # A concise four-note contour, with rhythmic rests: the repeated low E
    # answers a higher G/D/B figure. It is bass, not a high arpeggio loop.
    for beat, interval, length, velocity in [
        (0., 0, .31, 1.), (.75, 0, .19, .82),
        (1.5, 3 if bar in [0,1,3,6] else 7, .23, .91),
        (2.5, 10 if bar in [0,1,3,6] else 12, .18, .77),
        (3.25, 7, .20, .86),
    ]:
        at = base + beat*BEAT
        if at < 16.65:
            note = root + interval
            add(bassbus, bass(note, length), at, .93*velocity, kind='signature bass motif', note=note)
    # Stable low-end grid with one syncopated pickup per bar.
    for beat, gain in [(0, .93), (1, .76), (2, .85), (2.75, .58), (3, .76)]:
        at = base + beat*BEAT
        if at < 16.65:
            kick_at(at, gain)
    for beat in [1, 3]:
        at = base + beat*BEAT
        if at < 16.65:
            add(drums, clap(.9), at, .82, .04 if beat == 3 else -.04, 'crisp sparse snare')
    for j in range(8):
        at = base + j*BEAT/2
        if at < 16.65 and (j % 2 or bar in [1,3,4]):
            add(drums, hat(.82 if j%2 else .32, j==7 and bar%2==1), at, .78, .30*(-1 if j%2 else 1), 'tight high percussion')
    if bar in [1, 3, 5]:
        at = base + 3.5*BEAT
        if at < 16.65:
            add(drums, clap(.26, True), at, .48, .22, 'single ghost pickup')

# 9.5 type transition: one intentional reverse-pressure event and dry snap.
add(sound, pressure(.18, .10)[::-1], 9.32, .80, -.12, 'type transition suction')
add(sound, tactile(2), 9.50, .72, .12, 'type change snap')
add(sound, passby(.21, True), 9.50, .39, kind='brief type-transition pass')

# 10--13.5: the claim gets strong rhythm with no high-register melody.
add(music, chord([48, 55, 59, 62], 1.50, .024), 10.05, kind='checking claim harmonic support')
for j, at in enumerate([10.00, 11.55, 12.92]):
    add(sound, tactile(j+1), at, .32, .18*(-1 if j%2 else 1), 'claim typographic accent')

# 13.5--16.8: benefit. A warmer, wider chord supplies relief while the bass
# motif remains the identity. No plucked melody or generic notification runs.
add(music, chord([48, 55, 59, 62, 67], 2.1, .042), 13.50, kind='benefit warm Cmaj9 colour')
add(music, chord([50, 57, 62, 64, 66], 1.8, .035), 15.30, kind='benefit Dadd9 lift')
add(sound, pressure(.19, .065)[::-1], 16.58, kind='brand transition breath')

# 16.8--20: one confident brand landing, with the musical pulse settling.
impact(16.80, .80)
kick_at(16.80, .80)
add(bassbus, bass(40, 1.00), 16.80, 1., kind='brand resolved tonic', note=40)
add(music, chord([52, 59, 62, 66, 67], 2.80, .045), 16.80, kind='brand Em9 resolved colour')
add(sound, strike(76, 1.8), 16.80, .25, 0, 'quiet signature recall', 76)
add(bassbus, bass(40, .36), 17.7375, .55, kind='brand last low pulse', note=40)
add(drums, tactile(0), 17.7375, .18, 0, 'brand final contact')


def space(bus, amount=1.):
    """Computed short reflections; no sampled acoustic impulse response."""
    y = np.zeros_like(bus)
    for delay, gain, swap in [(.071, .10, True), (.131, .075, False), (.227, .052, True), (.347, .028, True), (.491, .013, False)]:
        d = round(delay*SR)
        source = bus[:, ::-1] if swap else bus
        y[d:] += source[:-d] * gain * amount
    return filt(y, [450, 6500], 'bandpass')


# Keep the low end centered and dry. A short duck lets the kick through
# without making the entire track pump or lose its physical weight.
bassbus *= (1 - .38*kick_duck)[:, None]
music *= (1 - .18*kick_duck)[:, None]
mix = bassbus + drums + music + space(music, .32) + sound + space(sound, .44)
# Reserve the final 100 ms before impact. The launch ends at 5.55, followed
# by a literal near-silent suspension rather than a continuous noisy riser.
tall = np.arange(N)/SR
gap = np.ones(N)
gap[(tall >= 5.55) & (tall < 5.65)] = .005
fadeout = (tall >= 5.545) & (tall < 5.55)
gap[fadeout] = np.linspace(1, .005, fadeout.sum())
mix *= gap[:, None]
mix = filt(mix, 28, 'highpass')
mix = filt(np.tanh(mix*1.08)/1.08, 17400)
# The close is fully settled by 19.8, with no chopped reverb or edge click.
end = np.clip((19.8-tall)/.60, 0, 1)**1.6
end *= np.minimum(tall/.002, 1)
mix *= end[:, None]
mix *= .86/max(.86, float(np.max(np.abs(mix))))


def write24(path, samples):
    pcm = (np.clip(samples, -1, 1)*(2**23-1)).astype(np.int32)
    packed = np.stack([pcm & 255, (pcm>>8)&255, (pcm>>16)&255], axis=-1).astype(np.uint8)
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(2)
        f.setsampwidth(3)
        f.setframerate(SR)
        f.writeframes(packed.tobytes())


def measure(path):
    proc = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(path), '-af',
                           'loudnorm=I=-14:TP=-1.2:LRA=10:print_format=json',
                           '-f', 'null', '-'], capture_output=True, text=True, check=True)
    return json.loads(re.findall(r'\{[^{}]*\}', proc.stderr)[-1])


raw = OUT/'jjintern-slick-premaster.wav'
write24(raw, mix)
first = measure(raw)
options = 'loudnorm=I=-14:TP=-1.2:LRA=10:' + ':'.join([
    f'measured_I={first["input_i"]}', f'measured_TP={first["input_tp"]}',
    f'measured_LRA={first["input_lra"]}', f'measured_thresh={first["input_thresh"]}',
    f'offset={first["target_offset"]}', 'linear=false', 'print_format=json',
])
final = OUT/'jjintern-slick-original-score.wav'
subprocess.run(['ffmpeg', '-hide_banner', '-y', '-i', str(raw), '-af', options,
                '-ar', str(SR), '-c:a', 'pcm_s24le', str(final)], capture_output=True, text=True, check=True)
measured = measure(final)
manifest = {
    'title': 'Weight / Direction', 'revision': 'V4 slick product-ad score',
    'duration_seconds': SECS, 'sample_rate': SR, 'channels': 2, 'bits_per_sample': 24,
    'tempo_bpm': BPM, 'main_groove_downbeat_s': 5.65,
    'tonal_centre': 'E minor, warmer Cmaj9 / Dadd9 benefit colours',
    'originality': 'All tones, bass, kick, percussion, metallic/glass hit, pressure, stereo launch, impact and reflections are procedurally synthesized. No samples, recordings, stock loops, vocals, external music generators or sampled IRs.',
    'seed': 41171026,
    'synthesis': {
        'bass': 'Bandlimited additive saw and sine/FM body plus octave-down sub, decaying brightness, centered',
        'kick': 'Exponential pitch-envelope sine plus newly generated filtered-noise transient',
        'percussion': 'Filtered generated noise and decaying resonators',
        'signature_strike': 'One original FM-glass/inharmonic-partial strike, not a notification tune',
        'fold': 'Resonant clicks, noise pressure and tuned contact transients',
        'launch': 'Shaped generated noise, falling oscillator and continuous equal-power left-to-right pan',
        'space': 'Short computed delay/reflection taps, no recorded IR',
    },
    'cues': [
        {'s': 0, 'cue': 'Restrained pressure'},
        {'s': 1.05, 'cue': 'Example posting signature strike'},
        {'s': 3.2, 'cue': 'Physical fold/compression with tactile contacts'},
        {'s': 4.65, 'cue': 'One-second packet travel window; stereo left-to-right launch'},
        {'s': 5.55, 'cue': '100 ms near silence before destination'},
        {'s': 5.65, 'cue': 'Website/feed impact and full bass-led groove'},
        {'s': 9.5, 'cue': 'Type transition snap'},
        {'s': 10, 'cue': 'Checking claim with rhythmic intent'},
        {'s': 13.5, 'cue': 'Benefit: warmer harmonic lift'},
        {'s': 16.8, 'cue': 'Brand landing and rhythmic settle'},
        {'s': 19.8, 'cue': 'Fully settled clean ending'},
    ],
    'premaster': { 'integrated_lufs': float(first['input_i']), 'true_peak_dbtp': float(first['input_tp']), 'loudness_range_lu': float(first['input_lra']) },
    'master': { 'file': final.name, 'integrated_lufs': float(measured['input_i']), 'true_peak_dbtp': float(measured['input_tp']), 'loudness_range_lu': float(measured['input_lra']), 'method': 'Two-pass ffmpeg EBU R128; -14 LUFS / -1.2 dBTP targets' },
    'build_seconds': round(time.perf_counter()-START, 3),
    'events': sorted(events, key=lambda event: event['s']),
}
(OUT/'score-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
final_sr, final_samples = wavfile.read(final)
final_samples = final_samples.astype(np.float64)/2**31
verification = {
    'samples':len(final_samples), 'duration_s':len(final_samples)/final_sr,
    'stereo_correlation':round(float(np.corrcoef(final_samples.T)[0,1]),4),
    'last_sample':final_samples[-1].tolist(),
    'end_after_19_8_peak_dbfs':float(20*np.log10(max(1e-12,np.max(np.abs(final_samples[round(19.8*SR):]))))),
    'segments':[],
}
for a,b in [(0,1),(1.05,1.55),(3.2,4.65),(4.65,5.54),(5.565,5.645),(5.65,9.5),(10,13.5),(13.5,16.8),(16.8,19.8)]:
    segment=final_samples[round(a*SR):round(b*SR)]
    verification['segments'].append({
        'start':a, 'end':b,
        'rms_dbfs':round(float(20*np.log10(max(1e-12,np.sqrt(np.mean(segment**2))))),2),
        'peak_dbfs':round(float(20*np.log10(max(1e-12,np.max(np.abs(segment))))),2),
    })
(OUT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
print(json.dumps({key:manifest[key] for key in ['title','duration_seconds','tempo_bpm','premaster','master','build_seconds']}, indent=2))
print(final)
