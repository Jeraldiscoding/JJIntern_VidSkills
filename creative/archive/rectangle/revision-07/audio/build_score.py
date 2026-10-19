#!/usr/bin/env python3
"""Fresh 18-second revision07 cue, synthesized without external audio inputs.

Python standard library performs all synthesis. FFmpeg masters and encodes.
Run: python3 creative/archive/rectangle/revision-07/audio/build_score.py
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
SR, DURATION, SEED = 48000, 18.000, 70224370
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
    f, length = hz(89), .90
    def synth(t):
        wave = math.sin(TAU * f * t) * math.exp(-t / .22)
        overtone = .09 * math.sin(TAU * 2.007 * f * t) * math.exp(-t / .065)
        return (wave + overtone) * envelope(t, length, .003, .08)
    event(.12, length, synth, .035, -.06, 'one source entrance ding', fundamental_hz=f)


def compression():
    start, length = 2.0, .24
    rng = random.Random(SEED + 200)
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
    event(start, length, synth, .048, -.20, 'fast friction squeeze', tone_sweep_hz=[530, 250])
    click(2.0, .022, -.13, .035, True, 'compression contact tick')
    click(2.225, .030, -.10, .045, True, 'packet closure snap')


def flight_tick(start, progress):
    length = .052
    cutoff = 2100 + 6000 * progress * progress
    rng = random.Random(SEED + round(start * SR) + 399)
    high = low = 0.
    a, b = 1 - math.exp(-TAU * cutoff / SR), 1 - math.exp(-TAU * 900 / SR)
    def synth(t):
        nonlocal high, low
        white = rng.uniform(-1, 1)
        high += a * (white - high)
        low += b * (white - low)
        return (high - low + .10 * math.sin(TAU * (1400 + 1700 * progress) * t)) * math.exp(-t / .012) * envelope(t, length, .0012, .012)
    event(start, length, synth, .014 + .014 * progress, -.20 + .40 * progress,
          'progressively faster flight rhythm tick', normalized_flight_progress=progress,
          upper_filter_hz=cutoff)


def flight():
    start, length = 3.0, 4.0
    rng = random.Random(SEED + 300)
    low = high = 0.
    phase = 0.
    for j in range(round(length * SR)):
        t, u = j / SR, j / SR / length
        white = rng.uniform(-1, 1)
        # A quiet continuous air bed opens with increasing speed; never a flat roar.
        cutoff = 1400 + 8200 * u * u
        high += (1 - math.exp(-TAU * cutoff / SR)) * (white - high)
        low += (1 - math.exp(-TAU * 620 / SR)) * (white - low)
        f = (640 + 1100 * u * u) * (1 - .32 * smooth((u - .88) / .12))
        phase += TAU * f / SR
        rush = .89 * (high - low) + .055 * math.sin(phase)
        level = (.07 + .93 * u ** 2.15) * envelope(t, length, .065, .012)
        pan = -.45 + .90 * u
        sample = rush * level * .066
        index = round(start * SR) + j
        BUS[0][index] += sample * math.cos((pan + 1) * math.pi / 4)
        BUS[1][index] += sample * math.sin((pan + 1) * math.pi / 4)
    EVENTS.append(dict(start_s=start, duration_s=length, kind='continuous accelerating stereo air and restrained oscillator sweep',
                       gain=.066, pan_sweep=[-.45, .45], noise_seed=SEED + 300,
                       bandwidth_sweep_hz=[1400, 9600], level_exponent=2.15))
    click(3.0, .019, -.30, .030, True, 'restrained launch edge')
    # Integrated tick frequency is phase(u)=4*(1.3*u+5.9*u^3/3).
    # Each integer crossing adds a tick. Its instantaneous rate rises from
    # 1.3 to 7.2 Hz, so interval length falls smoothly throughout the full flight.
    phase = lambda u: 4 * (1.3 * u + 5.9 * u ** 3 / 3)
    for target in range(1, math.floor(phase(1)) + 1):
        lo, hi = 0., 1.
        for _ in range(40):
            mid = (lo + hi) / 2
            if phase(mid) < target:
                lo = mid
            else:
                hi = mid
        u = (lo + hi) / 2
        # Preserve the arrival as a discrete tactile hit after the last rhythm tick.
        if start + length * u < 6.95:
            flight_tick(start + length * u, u)


def update_tone():
    f, length = hz(77), .46
    def synth(t):
        p = TAU * f * t
        return (math.sin(p) + .10 * math.sin(2 * p)) * math.exp(-t / .115) * envelope(t, length, .004, .06)
    event(8.35, length, synth, .027, .12, 'small abstract-update tone', fundamental_hz=f)


def compose():
    source_ding()
    # A calm 100 BPM half-time foundation leaves the reading beats spacious.
    # Flight gets progressively shorter tick intervals, not an overall fast recut.
    for t, g in [(.45, .13), (1.65, .13), (3.0, .125), (4.5, .13),
                 (5.7, .13), (6.5, .12), (7.0, .16),
                 (9.5, .13), (10.7, .13), (11.9, .13), (13.1, .13),
                 (14.3, .13), (15.3, .13)]:
        kick(t, g, .30 if t == 7.0 else .28, 50 if t == 7.0 else 56)
    for t in [1.05, 4.05, 5.25, 6.15, 10.1, 11.3, 12.5, 13.7, 14.9]:
        click(t, .032, .12, .065, False, 'dry restrained oscillator rim')
    for k, t in enumerate([.75, 1.35, 1.95, 9.8, 10.4, 11.0, 11.6,
                           12.2, 12.8, 13.4, 14.0, 14.6]):
        hat(t, .010 if k % 2 else .013, .20 if k % 2 else -.20)
    for t, n, length, g in [
        (.45, 41, .47, .086), (1.65, 48, .35, .079),
        (2.40, 41, .38, .063), (3.0, 38, .53, .082), (4.5, 45, .45, .077),
        (5.7, 38, .39, .084), (6.5, 45, .29, .076), (7.0, 34, .55, .092),
        (9.5, 36, .51, .087), (10.7, 41, .42, .084), (11.9, 36, .46, .087),
        (13.1, 41, .43, .084), (14.3, 48, .42, .076), (15.3, 41, .90, .092)]:
        bass(t, n, length, g)
    harmony(.28, 2.94, [53, 60, 64, 67, 69], .022, 'Fmaj9; sustains through packet hold', .25)
    harmony(3.0, 4.28, [50, 57, 60, 64, 65], .022, 'Dm9; continuous through flight', .24)
    harmony(7.0, 2.78, [46, 53, 57, 60, 62], .023, 'Bbmaj9; arrival and update hold', .11)
    harmony(9.5, 6.10, [48, 53, 55, 57, 64], .024, 'Fmaj9/C; reading hold', .13)
    harmony(15.3, 2.70, [53, 60, 62, 67, 69], .025, 'F6add9 final resolution', .10)
    for t, n, p in [(1.35, 81, -.16), (2.50, 79, .16),
                     (10.8, 77, -.15), (11.15, 79, .15), (12.8, 81, -.12), (14.0, 76, .12)]:
        pluck(t, n, .021, .60, p)
    compression()
    flight()
    # Arrival is connected to the rising air, with no full-mix silence or jump cut.
    click(7.0, .049, .06, .050, True, 'short connected arrival click')
    pluck(7.0, 65, .032, .58, -.08, 'arrival tonal body')
    pluck(7.0, 72, .020, .50, .10, 'arrival upper partial')
    update_tone()
    for note, gain, pan in [(77, .033, -.18), (81, .027, .12), (84, .019, .23)]:
        pluck(9.5, note, gain, .82, pan, 'Found harmonic opening')
    for note, gain, pan in [(65, .036, -.15), (72, .023, .10), (81, .017, .20)]:
        pluck(15.3, note, gain, 1.05, pan, 'final sign-off resolution')


def write_raw():
    raw = ROOT / '.synthesis-f32le.raw'
    samples = array('f')
    highpass_state = [0., 0.]
    a = 1 - math.exp(-TAU * 24 / SR)
    peak, sum_squared = 0., 0.
    for i in range(N):
        t = i / SR
        fade = smooth(t / .010) * smooth((DURATION - t - 1 / SR) / .90)
        for ch in range(2):
            highpass_state[ch] += a * (BUS[ch][i] - highpass_state[ch])
            sample = (BUS[ch][i] - highpass_state[ch]) * fade
            samples.append(sample)
            peak = max(peak, abs(sample))
            sum_squared += sample * sample
    if sys.byteorder != 'little':
        samples.byteswap()
    raw.write_bytes(samples.tobytes())
    return raw, dict(peak_dbfs=20 * math.log10(peak), rms_dbfs=10 * math.log10(sum_squared / (2 * N)))


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
    measure_filter = 'loudnorm=I=-16:TP=-1:LRA=8:print_format=json'
    measured = report(ffmpeg([*inp, '-af', measure_filter, '-f', 'null', '-']))
    af = ('loudnorm=I=-16:TP=-1:LRA=8:linear=true:print_format=json'
          f':measured_I={measured["input_i"]}:measured_TP={measured["input_tp"]}'
          f':measured_LRA={measured["input_lra"]}:measured_thresh={measured["input_thresh"]}'
          f':offset={measured["target_offset"]}')
    output = ROOT / 'jjintern-revision-07-original-score.wav'
    normalization = report(ffmpeg(['-y', *inp, '-af', af, '-ar', str(SR), '-ac', '2',
                                   '-c:a', 'pcm_s24le', '-t', '18.000', str(output)]))
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
    flight_ticks = [e['start_s'] for e in EVENTS if e['kind'] == 'progressively faster flight rhythm tick']
    tick_intervals = [b - a for a, b in zip(flight_ticks, flight_ticks[1:])]
    assert all(b < a for a, b in zip(tick_intervals, tick_intervals[1:]))
    aac = ROOT / '.aac-check.m4a'
    ffmpeg(['-y', '-i', str(output), '-c:a', 'aac', '-b:a', '256k', str(aac)])
    aac_report = report(ffmpeg(['-i', str(aac), '-af', measure_filter, '-f', 'null', '-']))
    aac.unlink()
    ffmpeg(['-y', '-i', str(output), '-filter_complex',
            'showwavespic=s=1800x420:split_channels=1:colors=0071e3|203145',
            '-frames:v', '1', '-update', '1', str(ROOT / 'waveform.png')])
    manifest = {
        'title': 'JJIntern revision07 — measured holds and four-second acceleration',
        'source': 'build_score.py', 'output': output.name,
        'provenance': 'Fresh composition synthesized for revision07. All audio originates from analytic oscillators, seeded pseudorandom noise, one-pole filters, soft saturation and envelopes. No samples, recordings, loops, voiceover, earlier score WAV or impulse responses are read. Basic oscillator implementation is adapted from the original revision06 synthesizer; rhythm, harmony, motif, four-second acceleration design, transitions and timing are newly composed.',
        'external_audio_inputs': [], 'voiceover': False,
        'duration_seconds': DURATION, 'samples_per_channel': N,
        'sample_rate_hz': SR, 'channels': 2, 'pcm_bit_depth': 24,
        'tempo_bpm': 100, 'pulse_seconds': .60, 'random_seed': SEED,
        'harmony': ['Fmaj9', 'Dm9', 'Bbmaj9', 'Fmaj9/C', 'F6add9'],
        'design': 'Measured half-time groove with sparse dry percussion and warm oscillator bass. Only compression is a quick 240 ms gesture; sustained harmony and a quiet pluck leave space for the packet hold. Four seconds of continuous low-level air open in bandwidth and intensity, with progressively shorter rhythm-tick intervals. The arrival connects without a full-mix gap. Update, Found and sign-off have small distinct cues. The payoff remains calm and readable, with percussion ending at 15.3 seconds.',
        'synchronization': [
            {'at_s': .12, 'event': 'one small source ding'},
            {'from_s': 2.0, 'to_s': 2.24, 'event': 'quick friction squeeze and closure snap'},
            {'from_s': 2.24, 'to_s': 3.0, 'event': 'quiet sustained harmony and single pluck support packet pause'},
            {'at_s': 3.0, 'event': 'restrained launch edge'},
            {'from_s': 3.0, 'to_s': 7.0, 'event': 'continuous accelerating air with progressive brightness and rhythm rate'},
            {'at_s': 7.0, 'event': 'short connected arrival click plus low body'},
            {'at_s': 8.35, 'event': 'small abstract-update tone'},
            {'at_s': 9.5, 'event': 'small F harmony opening for Found'},
            {'at_s': 10.8, 'event': 'soft pluck supports first payoff line'},
            {'at_s': 11.15, 'event': 'soft pluck supports second payoff line'},
            {'at_s': 15.3, 'event': 'resolved F6add9 sign-off; no further percussion'},
            {'from_s': 17.1, 'to_s': 18.0, 'event': 'smooth closing tail to zero'}],
        'flight_rhythm': {'instantaneous_rate_hz_start_end': [1.3, 7.2],
                          'integrated_phase': '4 * (1.3*u + 5.9*u^3/3)',
                          'tick_times_s': flight_ticks, 'intervals_s': tick_intervals,
                          'strictly_decreasing_intervals_verified': True},
        'mastering': {'target_integrated_lufs': -16, 'true_peak_ceiling_dbtp': -1,
                      'normalization_type': normalization['normalization_type'], 'raw_synthesis_stats': raw_stats},
        'measured_final': {'integrated_lufs': float(validation['input_i']),
                           'true_peak_dbtp': float(validation['input_tp']),
                           'loudness_range_lu': float(validation['input_lra']),
                           'sample_peak_dbfs': 20 * math.log10(peak),
                           'duration_seconds': float(probe['streams'][0]['duration']),
                           'samples_per_channel': len(samples) // 2,
                           'last_stereo_sample': list(samples[-2:]),
                           'clipped_samples': sum(abs(v) >= 1 for v in samples)},
        'aac_256k_roundtrip_check': {'integrated_lufs': float(aac_report['input_i']),
                                    'true_peak_dbtp': float(aac_report['input_tp'])},
        'inspection': {'performed': ['duration and sample count', 'codec and channel count',
                                     'loudness and oversampled true peak', 'endpoints and clipping',
                                     'strictly decreasing flight rhythm intervals across four-second flight',
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
