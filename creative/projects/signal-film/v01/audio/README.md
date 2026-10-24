# Find your focus — original score

**Delivery:** [jjintern-find-your-focus-original-score.wav](jjintern-find-your-focus-original-score.wav), 32.000 seconds, 48 kHz stereo, 24-bit PCM. Mux at time zero. The score is authored for the film's 120 BPM timing, with major contact accents at **4, 8, 12, 18, 22 and 28 seconds**.

The original arrangement moves from spatially scattered musical fragments into a syncopated drum-and-bass groove. A short D–A–C–F pluck motif gives the music a recurring identity. Detuned chord stabs open the feature reveal, the product demonstration has fewer top layers, the orbital section adds rotating stereo detail, and the typography climax uses the fullest groove. The brand beat lands at 28 seconds; the final motif resolves to D at 29.875 seconds and reaches silence by 31.5 seconds.

All sounds originate in [build_score.py](build_score.py): analytic oscillators, deterministic noise, filters, envelopes, band-limited tables and short mathematical reflections. No external audio, prior rendered score, sample, loop, recording, soundfont or impulse response is used. There is no voiceover.

Rebuild from the workspace root with Python 3 and ffmpeg/ffprobe on the path:

```sh
python3 creative/projects/signal-film/v01/audio/build_score.py
```

Measured master: **−15.11 LUFS integrated**, **−1.59 dBTP**, **3.5 LU loudness range**, no clipped samples, 1,536,000 samples per channel. A 320 kbps AAC encode/decode measured **−15.13 LUFS** and **−1.41 dBTP**. See [loudness-analysis.json](loudness-analysis.json) for raw analysis and [audio-manifest.json](audio-manifest.json) for provenance, exact musical events and SHA-256.

Source and timing, file format, duration, endpoint silence, loudness, peak headroom and AAC headroom were checked. The [waveform](waveform.png) and [spectrogram](spectrogram.png) were visually inspected: section dynamics and the decaying ending are visible, and the treble energy is transient rather than a continuous noise bed. Subjective listening and physical-phone playback were **not** performed; these technical checks do not substitute for them.
