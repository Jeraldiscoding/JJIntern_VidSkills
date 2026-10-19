#!/usr/bin/env python3
"""Fresh 12-second revision06 cue, synthesized without external audio inputs.

Python standard library performs all synthesis. FFmpeg masters and encodes.
Run: python3 creative/archive/rectangle/revision-06/audio/build_score.py
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
SR, DURATION, SEED = 48000, 12.000, 60182460
N = round(SR * DURATION)
TAU = 2 * math.pi
BUS = [array('f', [0]) * N, array('f', [0]) * N]
EVENTS = []


def smooth(v):
    v = max(0., min(1., v))
    return v * v * (3 - 2 * v)


def envelope(t, duration, attack=.004, release=.04):
    return smooth(t / attack) * smooth((duration - t) / release)


def hz(note):
    return 440 * 2 ** ((note - 69) / 12)


def event(start, duration, synth, gain, pan, kind, **parameters):
    begin, length = round(start * SR), min(round(duration * SR), N - round(start * SR))
    lg, rg = gain * math.cos((pan + 1) * math.pi / 4), gain * math.sin((pan + 1) * math.pi / 4)
    for i in range(length):
        sample = synth(i / SR)
        BUS[0][begin + i] += sample * lg
        BUS[1][begin + i] += sample * rg
    EVENTS.append(dict(start_s=start, duration_s=duration, kind=kind, gain=gain, pan=pan, **parameters))


def kick(start, gain=.15, length=.255, body=56):
    def synth(t):
        phase = TAU * (body * t + 104 * .013 * (1 - math.exp(-t / .013)))
        core = math.sin(phase) * math.exp(-t / .075)
        transient = .07 * math.sin(TAU * 1140 * t) * math.exp(-t / .003)
        return (core + transient) * envelope(t, length, .0011, .035)
    event(start, length, synth, gain, 0, 'short sine kick', body_hz=body)


def click(start, gain=.024, pan=0, length=.045, dark=False, kind='dry tactile click'):
    rng = random.Random(SEED + round(start * SR) + (113 if dark else 127))
    low = 0.
    a = 1 - math.exp(-TAU * (1300 if dark else 3600) / SR)
    def synth(t):
        nonlocal low
        white = rng.uniform(-1, 1)
        low += a * (white - low)
        body = math.sin(TAU * (620 if dark else 1830) * t)
        return (.60 * low + .40 * body) * math.exp(-t / .0085) * envelope(t, length, .0006, .01)
    event(start, length, synth, gain, pan, kind, low_pass_hz=1300 if dark else 3600)


def hat(start, gain=.012, pan=-.25, length=.055):
    rng = random.Random(SEED * 2 + round(start * SR))
    low = 0.
    a = 1 - math.exp(-TAU * 5000 / SR)
    def synth(t):
        nonlocal low
        white = rng.uniform(-1, 1)
        low += a * (white - low)
        return (white - low) * math.exp(-t / .011) * envelope(t, length, .0007, .01)
    event(start, length, synth, gain, pan, 'short high-passed noise tick')


def bass(start, note, length=.30, gain=.095):
    f = hz(note)
    def synth(t):
        # Two harmonic-rich oscillators; the low fundamental stays centred.
        p = TAU * f * t
        body = math.sin(p) + .29 * math.sin(2 * p) + .12 * math.sin(3 * p)
        return math.tanh(1.15 * body) * (.76 + .24 * math.exp(-t / .045)) * envelope(t, length, .007, .075)
    event(start, length, synth, gain, 0, 'warm clipped-sine bass', midi=note, fundamental_hz=f)


def pluck(start, note, gain=.032, length=.50, pan=0, kind='muted FM oscillator pluck'):
    f = hz(note)
    def synth(t):
        p = TAU * f * t
        phase = p + .42 * math.sin(2 * p) * math.exp(-t / .055)
        return (math.sin(phase) + .10 * math.sin(3 * p)) * math.exp(-t / .14) * envelope(t, length, .003, .055)
    event(start, length, synth, gain, pan, kind, midi=note, fundamental_hz=f)


def harmony(start, length, notes, gain=.022, label='', attack=.11):
    for k, note in enumerate(notes):
        f = hz(note)
        detune = [-.0011, .0013, -.0006, .0008, -.0014][k % 5]
        pan = [-.40, .36, -.18, .21, .05][k % 5]
        def synth(t, f=f, k=k, detune=detune):
            p = TAU * f * t
            wave = .71 * math.sin(p) + .29 * math.sin(p * (1 + detune)) + .10 * math.sin(2 * p)
            movement = .94 + .06 * math.sin(TAU * .19 * t + k * .5)
            return wave * movement * envelope(t, length, attack, .46)
        event(start, length, synth, gain, pan, 'soft evolving oscillator harmony', midi=note, harmony=label)


def source_ding():
    f, length = hz(88), .73
    def synth(t):
        wave = math.sin(TAU * f * t) * math.exp(-t / .17)
        overtone = .09 * math.sin(TAU * 2.007 * f * t) * math.exp(-t / .065)
        return (wave + overtone) * envelope(t, length, .003, .08)
    event(.12, length, synth, .039, -.06, 'one source entrance ding', fundamental_hz=f)


def compression():
    start, length = 1.8, .24
    rng = random.Random(SEED + 180)
    high = low = 0.
    a, b = 1 - math.exp(-TAU * 2800 / SR), 1 - math.exp(-TAU * 420 / SR)
    def synth(t):
        nonlocal high, low
        white = rng.uniform(-1, 1)
        high += a * (white - high)
        low += b * (white - low)
        u = t / length
        friction = (high - low) * (.20 + .80 * u * u)
        bend = .18 * math.sin(TAU * (530 * t - 280 * t * t / (2 * length)))
        return (friction + bend) * envelope(t, length, .008, .009)
    event(start, length, synth, .060, -.20, 'fast friction squeeze', tone_sweep_hz=[530, 250])
    click(1.8, .025, -.13, .035, True, 'compression contact tick')
    click(2.025, .040, -.10, .045, True, 'packet closure snap')


def flight():
    start, length = 2.04, .60
    rng = random.Random(SEED + 204)
    low = high = 0.
    phase = 0.
    for j in range(round(length * SR)):
        t, u = j / SR, j / SR / length
        white = rng.uniform(-1, 1)
        # Bandwidth opens quickly and the tone falls past camera late in flight.
        cutoff = 2600 + 7200 * u * u
        high += (1 - math.exp(-TAU * cutoff / SR)) * (white - high)
        low += (1 - math.exp(-TAU * 1000 / SR)) * (white - low)
        f = (1100 + 1450 * smooth(u / .68)) * (1 - .70 * smooth((u - .68) / .32))
        phase += TAU * f / SR
        rush = .84 * (high - low) + .10 * math.sin(phase)
        level = (.14 + .86 * u ** 1.6) * envelope(t, length, .008, .005)
        pan = -.60 + 1.20 * u
        sample = rush * level * .085
        index = round(start * SR) + j
        BUS[0][index] += sample * math.cos((pan + 1) * math.pi / 4)
        BUS[1][index] += sample * math.sin((pan + 1) * math.pi / 4)
    EVENTS.append(dict(start_s=start, duration_s=length, kind='fast stereo filtered air with oscillator Doppler fall',
                       gain=.085, pan_sweep=[-.6, .6], noise_seed=SEED + 204,
                       bandwidth_sweep_hz=[2600, 9800], pre_impact_gap_s=[2.605, 2.64]))
    click(2.04, .027, -.40, .026, False, 'launch edge transient')


def compose():
    source_ding()
    # New 125 BPM rhythm, cut around the motion rather than stretched from rev05.
    for t, g in [(.24, .138), (1.20, .145), (1.56, .095),
                 (2.64, .19), (3.60, .15), (4.20, .145), (5.16, .15),
                 (6.12, .15), (6.84, .11), (7.08, .15), (8.04, .15), (8.76, .115), (9.20, .14)]:
        kick(t, g, .29 if t == 2.64 else .255, 50 if t == 2.64 else 56)
    for t in [.72, 1.68, 3.12, 4.08, 4.68, 5.64, 6.60, 7.56, 8.52]:
        click(t, .042, .15, .060, False, 'dry oscillator rim')
    for k, t in enumerate([.48, .96, 1.44, 2.88, 3.36, 3.84,
                           4.44, 4.92, 5.40, 5.88, 6.36, 6.84, 7.32, 7.80, 8.28, 8.76]):
        hat(t, .012 if k % 2 else .016, .25 if k % 2 else -.25)
    for t in [3.72, 6.48, 8.40]:
        hat(t, .008, .1, .035)
    for t, n, length, g in [
        (.24, 40, .36, .092), (1.20, 40, .31, .092), (1.56, 47, .20, .075),
        (2.64, 33, .43, .108), (3.60, 40, .32, .093),
        (4.20, 40, .39, .096), (5.16, 47, .33, .087), (6.12, 40, .34, .098),
        (6.84, 47, .19, .068), (7.08, 37, .40, .094), (8.04, 44, .32, .085),
        (8.76, 47, .22, .076), (9.20, 40, .88, .100)]:
        bass(t, n, length, g)
    harmony(.22, 1.60, [52, 59, 63, 66, 68], .021, 'Emaj9', .10)
    harmony(2.64, 1.62, [45, 52, 56, 59, 63], .025, 'Amaj9', .07)
    harmony(4.20, 2.94, [52, 59, 64, 66, 68], .025, 'Eadd9', .08)
    harmony(7.08, 2.20, [49, 56, 59, 63, 64], .023, 'C#m9', .10)
    harmony(9.20, 2.80, [52, 59, 61, 66, 68], .026, 'E6add9 final resolution', .055)
    for t, n, p in [(.96, 83, -.17), (1.44, 80, .17), (3.36, 75, -.20),
                     (5.40, 80, .18), (6.36, 78, -.16), (7.80, 75, .18)]:
        pluck(t, n, .023, .43, p)
    compression()
    flight()
    # Single compact arrival: a tactile broadband edge on the bass/kick body.
    click(2.64, .072, .08, .045, True, 'precise arrival click')
    pluck(2.64, 64, .034, .40, -.08, 'arrival tonal body')
    pluck(2.64, 71, .022, .36, .10, 'arrival upper partial')
    for note, gain, pan in [(76, .035, -.18), (80, .030, .12), (83, .020, .23)]:
        pluck(4.20, note, gain, .64, pan, 'Found harmonic opening')
    # Two quiet edit ticks support the ordered lines without competing with reading.
    click(4.82, .018, -.12, .030, True, 'first payoff line tick')
    click(5.04, .014, .12, .030, True, 'second payoff line tick')
    for note, gain, pan in [(64, .038, -.15), (71, .025, .10), (80, .018, .20)]:
        pluck(9.20, note, gain, .90, pan, 'final sign-off resolution')


def write_raw():
    raw = ROOT / '.synthesis-f32le.raw'
    samples = array('f')
    highpass_state = [0., 0.]
    a = 1 - math.exp(-TAU * 24 / SR)
    peak, sum_squared, pocket_peak = 0., 0., 0.
    for i in range(N):
        t = i / SR
        fade = smooth(t / .010) * smooth((DURATION - t - 1 / SR) / .78)
        # The final 35 ms before the hit is silent, with a 6 ms lead-in ramp.
        if 2.599 <= t < 2.605:
            pocket = 1 - smooth((t - 2.599) / .006)
        elif 2.605 <= t < 2.64:
            pocket = 0.
        elif 2.64 <= t < 2.6405:
            pocket = smooth((t - 2.64) / .0005)
        else:
            pocket = 1.
        for ch in range(2):
            highpass_state[ch] += a * (BUS[ch][i] - highpass_state[ch])
            sample = (BUS[ch][i] - highpass_state[ch]) * fade * pocket
            samples.append(sample)
            peak = max(peak, abs(sample))
            sum_squared += sample * sample
            if 2.605 <= t < 2.64:
                pocket_peak = max(pocket_peak, abs(sample))
    if sys.byteorder != 'little':
        samples.byteswap()
    raw.write_bytes(samples.tobytes())
    return raw, dict(peak_dbfs=20 * math.log10(peak), rms_dbfs=10 * math.log10(sum_squared / (2 * N)),
                     pre_impact_pocket_peak_linear=pocket_peak)


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
    measure_filter = 'loudnorm=I=-15:TP=-1:LRA=8:print_format=json'
    measured = report(ffmpeg([*inp, '-af', measure_filter, '-f', 'null', '-']))
    af = ('loudnorm=I=-15:TP=-1:LRA=8:linear=true:print_format=json'
          f':measured_I={measured["input_i"]}:measured_TP={measured["input_tp"]}'
          f':measured_LRA={measured["input_lra"]}:measured_thresh={measured["input_thresh"]}'
          f':offset={measured["target_offset"]}')
    output = ROOT / 'jjintern-revision-06-original-score.wav'
    normalization = report(ffmpeg(['-y', *inp, '-af', af, '-ar', str(SR), '-ac', '2',
                                   '-c:a', 'pcm_s24le', '-t', '12.000', str(output)]))
    validation = report(ffmpeg(['-i', str(output), '-af', measure_filter, '-f', 'null', '-']))
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
    # Exclude the sub-millisecond antialiasing edge of resampling when measuring silence.
    pocket = samples[2 * round(2.607 * SR):2 * round(2.638 * SR)]
    pocket_peak = max(abs(v) for v in pocket)
    aac = ROOT / '.aac-check.m4a'
    ffmpeg(['-y', '-i', str(output), '-c:a', 'aac', '-b:a', '256k', str(aac)])
    aac_report = report(ffmpeg(['-i', str(aac), '-af', measure_filter, '-f', 'null', '-']))
    aac.unlink()
    ffmpeg(['-y', '-i', str(output), '-filter_complex',
            'showwavespic=s=1800x420:split_channels=1:colors=0071e3|203145',
            '-frames:v', '1', '-update', '1', str(ROOT / 'waveform.png')])
    manifest = {
        'title': 'JJIntern revision06 — crisp 12-second motion score',
        'source': 'build_score.py', 'output': output.name,
        'provenance': 'Fresh composition synthesized for revision06. All audio originates from analytic oscillators, seeded pseudorandom noise, one-pole filters, soft saturation and envelopes. No samples, recordings, loops, voiceover, earlier score WAV or impulse responses are read. Basic oscillator implementation is adapted from the original revision05 synthesizer; rhythm, harmony, motif, transitions and timing are newly composed.',
        'external_audio_inputs': [], 'voiceover': False,
        'duration_seconds': DURATION, 'samples_per_channel': N,
        'sample_rate_hz': SR, 'channels': 2, 'pcm_bit_depth': 24,
        'tempo_bpm': 125, 'pulse_seconds': .48, 'random_seed': SEED,
        'harmony': ['Emaj9', 'Amaj9', 'Eadd9', 'C#m9', 'E6add9'],
        'design': 'Minimal energetic groove. Very short dry drum envelopes and warm saturated oscillator bass. Compression is a 240 ms squeeze/snap, launch has a crisp edge, flight opens its noise bandwidth and drops oscillator pitch. A 35 ms full-mix pocket precedes the tactile arrival. Restrained harmony supports readable holds; percussion ends at sign-off.',
        'synchronization': [
            {'at_s': .12, 'event': 'one small source ding'},
            {'from_s': 1.8, 'to_s': 2.04, 'event': 'fast friction squeeze and closure snap'},
            {'at_s': 2.04, 'event': 'launch transient'},
            {'from_s': 2.04, 'to_s': 2.64, 'event': 'stereo accelerating air and Doppler pitch fall'},
            {'from_s': 2.605, 'to_s': 2.64, 'event': '35 ms full-mix pre-impact pocket; 6 ms preceding ramp'},
            {'at_s': 2.64, 'event': 'single tactile click plus low kick/bass and short tonal body'},
            {'at_s': 4.2, 'event': 'small E harmony opening for Found'},
            {'at_s': 4.82, 'event': 'first payoff line tick'},
            {'at_s': 5.04, 'event': 'second payoff line tick'},
            {'at_s': 9.2, 'event': 'resolved E6add9 sign-off; no further percussion'},
            {'from_s': 11.22, 'to_s': 12.0, 'event': 'smooth closing tail to zero'}],
        'mastering': {'target_integrated_lufs': -15, 'true_peak_ceiling_dbtp': -1,
                      'normalization_type': normalization['normalization_type'], 'raw_synthesis_stats': raw_stats},
        'measured_final': {'integrated_lufs': float(validation['input_i']),
                           'true_peak_dbtp': float(validation['input_tp']),
                           'loudness_range_lu': float(validation['input_lra']),
                           'sample_peak_dbfs': 20 * math.log10(peak),
                           'duration_seconds': float(probe['streams'][0]['duration']),
                           'samples_per_channel': len(samples) // 2,
                           'last_stereo_sample': list(samples[-2:]),
                           'pre_impact_pocket_interior_peak_linear': pocket_peak,
                           'clipped_samples': sum(abs(v) >= 1 for v in samples)},
        'aac_256k_roundtrip_check': {'integrated_lufs': float(aac_report['input_i']),
                                    'true_peak_dbtp': float(aac_report['input_tp'])},
        'inspection': {'performed': ['duration and sample count', 'codec and channel count',
                                     'loudness and oversampled true peak', 'endpoints, clipping and impact-pocket silence',
                                     '256 kbps AAC round-trip loudness and true peak', 'waveform generated for inspection'],
                       'not_performed': ['subjective listening on headphones/speakers', 'physical-phone playback'],
                       'limitation': 'Measured and source-reviewed; subjective listening is not claimed.'},
        'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'events': sorted(EVENTS, key=lambda event: event['start_s'])}
    (ROOT / 'audio-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (ROOT / 'loudness-analysis.json').write_text(json.dumps(dict(first_pass=measured, normalization=normalization,
                                                              final_measurement=validation,
                                                              aac_256k_roundtrip=aac_report), indent=2) + '\n')
    raw.unlink()
    print(json.dumps(dict(output=str(output), measured_final=manifest['measured_final'],
                         aac_256k_roundtrip=manifest['aac_256k_roundtrip_check']), indent=2))


if __name__ == '__main__':
    main()
