#!/usr/bin/env python3
"""A Small Advantage — original 10-second JJIntern compact-ad cue.

Composed as ten seconds, never spliced or accelerated from an earlier score.
All oscillator/noise synthesis; no samples, loops, recordings or sampled IRs.
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

START=time.perf_counter()
OUT=Path(__file__).resolve().parent
SR=48000
SECONDS=10.
N=round(SR*SECONDS)
PI=np.pi
RNG=np.random.default_rng(10171026)
low=np.zeros((N,2))
rhythm=np.zeros_like(low)
tonal=np.zeros_like(low)
material=np.zeros_like(low)
duck=np.zeros(N)
events=[]


def tt(length):
    return np.arange(round(length*SR))/SR


def hz(note):
    return 440*2**((note-69)/12)


def filt(x,cutoff,kind='lowpass',order=2):
    return signal.sosfilt(signal.butter(order,cutoff,kind,fs=SR,output='sos'),x,axis=0)


def add(bus,x,at,gain=1.,pan=0.,label=None,note=None):
    if x.ndim==1:
        theta=(pan+1)*PI/4
        x=np.stack([x*np.cos(theta),x*np.sin(theta)],axis=1)
    i=round(at*SR)
    count=min(N-i,len(x))
    bus[i:i+count]+=x[:count]*gain
    if label:
        event={'seconds':at,'event':label,'gain':gain,'pan':pan}
        if note is not None:event['midi_note']=note
        events.append(event)


def envelope(t,attack=.003,decay=.12,release=.025):
    return (1-np.exp(-t/attack))*np.exp(-t/decay)*np.minimum(np.maximum(t[-1]-t,0)/release,1)


def contact(kind=0):
    t=tt(.065)
    f=[460,670,890,1160][kind%4]
    x=np.sin(2*PI*f*t)*np.exp(-t/.006)*.27
    x+=np.sin(2*PI*f*2.43*t)*np.exp(-t/.003)*.045
    x+=filt(RNG.standard_normal(len(t)),[900,6100],'bandpass')*np.exp(-t/.004)*.22
    return x*np.minimum(t/.0003,1)*.27


def initial_note():
    t=tt(.62)
    p=2*PI*587.33*t
    x=np.sin(p+.65*np.exp(-t/.012)*np.sin(p*2.013))*.46
    x+=np.sin(p*2.03)*np.exp(-t/.045)*.065
    return x*envelope(t,.002,.105,.06)*.17


def bass(note,length=.33):
    t=tt(length)
    p=2*PI*hz(note)*t
    # Rounded fundamental and audible second partial, a little transient edge;
    # the cutoff and very small FM index keep it away from buzzy synth arps.
    x=.72*np.sin(p+.12*np.exp(-t/.04)*np.sin(p*2))
    x+=.17*np.sin(p/2)+.14*np.sin(2*p)*np.exp(-t/.16)
    x+=.035*np.sin(3*p)*np.exp(-t/.035)
    shape=(1-np.exp(-t/.004))*(.65+.35*np.exp(-t/.10))
    shape*=np.minimum(np.maximum(length-t,0)/.055,1)
    return filt(np.tanh(x*1.14)/1.14,1250)*shape*.45


def kick():
    t=tt(.30)
    frequency=52+66*np.exp(-t/.012)+12*np.exp(-t/.04)
    phase=2*PI*np.cumsum(frequency)/SR
    x=np.sin(phase)*np.exp(-t/.079)
    n=filt(RNG.standard_normal(len(t)),[2300,6800],'bandpass')
    x+=n*np.exp(-t/.0014)*.050
    return np.tanh(x*1.20)*.66*np.minimum(t/.0004,1)*np.minimum((.30-t)/.025,1)


def kick_at(at,gain=.7):
    add(rhythm,kick(),at,gain,label='compact dry kick')
    i=round(at*SR)
    length=min(N-i,round(.22*SR))
    duck[i:i+length]=np.maximum(duck[i:i+length],np.exp(-np.arange(length)/SR/.058))


def rim():
    t=tt(.11)
    n=filt(RNG.standard_normal(len(t)),[1200,7200],'bandpass')
    x=n*np.exp(-t/.018)*.25+np.sin(2*PI*235*t)*np.exp(-t/.009)*.15
    return x*np.minimum(t/.0003,1)*.35


def hat():
    t=tt(.038)
    n=filt(RNG.standard_normal(len(t)),[7600,15500],'bandpass')
    return n*envelope(t,.0002,.007,.008)*.070


def fold_pressure():
    t=tt(.96)
    q=t/.96
    n=filt(RNG.standard_normal(len(t)),[320,2800],'bandpass')
    return n*np.sin(PI*q)**1.5*(.75+.25*np.sin(2*PI*9*t)**2)*.027


def passby():
    length=1.
    t=tt(length)
    q=t/length
    n=filt(RNG.standard_normal(len(t)),[650,8200],'bandpass')
    p=2*PI*(780*t-470*t*t/2)
    x=(n*.31+np.sin(p)*.018)*np.sin(PI*q)**1.8*.14
    # Full equal-power left-to-right travel over exactly one second.
    pan=-1+2*q
    return np.stack([x*np.sqrt((1-pan)/2),x*np.sqrt((1+pan)/2)],axis=1)


def colour(notes,length,level=.025):
    t=tt(length)
    y=np.zeros((len(t),2))
    for note in notes:
        for ch,offset in enumerate([-.025,.025]):
            p=2*PI*hz(note+offset)*t
            y[:,ch]+=np.sin(p)+.12*np.sin(2*p)
    shape=(1-np.exp(-t/.018))*np.exp(-t/.40)
    shape*=np.minimum(np.maximum(length-t,0)/.22,1)
    return filt(y,1600)*shape[:,None]*level


# Posting reveal. A small original note, not a loud alert or notification tune.
add(material,initial_note(),.18,.60,label='subtle posting material note')
add(material,contact(0),.18,.20,label='posting contact')

# Four light physical contacts explain the fold, without a rattling click run.
add(material,fold_pressure(),1.65,label='fold pressure')
for at,kind,pan in [(1.65,0,-.15),(1.95,1,-.05),(2.28,2,.08),(2.58,0,.16)]:
    add(material,contact(kind),at,.44,pan,'fold contact / packet lock')

# Exactly one second of travel; no added tunnel, long riser or trailer boom.
add(material,passby(),2.65,label='one-second left-to-right packet pass')
add(material,contact(2),2.65,.34,-.45,'packet release')

# Destination: a short contact and the first kick/bass supply the impact.
add(material,contact(0),3.65,.62,0,'website arrival contact')
add(tonal,colour([50,57,61,64],1.18,.028),3.65,label='feed Dmaj9 colour')

# A concise two-bar bass composition, deliberately leaving melodic rests.
# This is freshly sequenced for ten seconds, never cut from an older file.
bass_notes=[
    (3.65,38,.36,.94),(4.40,38,.18,.70),(4.90,45,.25,.75),
    (5.40,49,.17,.66),(5.65,43,.34,.84),(6.40,45,.20,.70),
    (6.90,38,.38,.83),(7.65,38,.27,.73),(8.15,45,.22,.57),
]
for at,note,length,gain in bass_notes:
    add(low,bass(note,length),at,gain,label='short bass motif',note=note)
for at,gain in [(3.65,.81),(4.15,.56),(4.65,.66),(5.15,.53),(5.65,.71),(6.15,.52),(6.65,.62),(7.15,.45),(7.65,.54),(8.15,.39)]:
    kick_at(at,gain)
for at,gain in [(4.15,.64),(5.15,.54),(6.15,.54),(7.15,.38)]:
    add(rhythm,rim(),at,gain,.035,'sparse soft rim')
for i,at in enumerate([3.90,4.90,5.90,6.90,7.90]):
    add(rhythm,hat(),at,.66,.20*(-1 if i%2 else 1),'single tight high detail')
add(tonal,colour([55,59,62,66],1.15,.022),5.65,label='feed warm Gmaj9 answer')

# Benefit/URL close. One warm return; the groove thins and resolves.
add(tonal,colour([50,57,61,64,66],2.75,.033),6.75,label='benefit / URL Dmaj9 resolution')
add(material,contact(1),6.75,.28,0,'benefit contact')
add(low,bass(38,.72),8.65,.52,label='final low resolve',note=38)
add(tonal,colour([57,61,64],1.05,.018),8.65,label='last harmonic punctuation')


def short_space(bus,level):
    y=np.zeros_like(bus)
    for seconds,gain,swap in [(.067,.10,True),(.121,.065,False),(.213,.035,True),(.337,.015,True)]:
        d=round(seconds*SR)
        source=bus[:,::-1] if swap else bus
        y[d:]+=source[:-d]*gain*level
    return filt(y,[500,5800],'bandpass')


low*=np.maximum(.7,1-.27*duck)[:,None]
mix=low+rhythm+tonal+material+short_space(tonal,.45)+short_space(material,.36)
mix=filt(mix,28,'highpass')
mix=filt(np.tanh(mix*1.06)/1.06,17000)
t=np.arange(N)/SR
fade=np.clip((9.90-t)/.48,0,1)**1.5*np.minimum(t/.002,1)
mix*=fade[:,None]


def write24(path,x):
    pcm=(np.clip(x,-1,1)*(2**23-1)).astype(np.int32)
    packed=np.stack([pcm&255,(pcm>>8)&255,(pcm>>16)&255],axis=-1).astype(np.uint8)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(3);w.setframerate(SR);w.writeframes(packed.tobytes())


def measure(path):
    result=subprocess.run(['ffmpeg','-hide_banner','-i',str(path),'-af','loudnorm=I=-14:TP=-1.4:LRA=10:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    return json.loads(re.findall(r'\{[^{}]*\}',result.stderr)[-1])


raw=OUT/'jjintern-compact-premaster.wav'
write24(raw,mix)
first=measure(raw)
settings='loudnorm=I=-14:TP=-1.4:LRA=10:'+':'.join([
    f'measured_I={first["input_i"]}',f'measured_TP={first["input_tp"]}',
    f'measured_LRA={first["input_lra"]}',f'measured_thresh={first["input_thresh"]}',
    f'offset={first["target_offset"]}','linear=true','print_format=json',
])
final=OUT/'jjintern-compact-original-score.wav'
subprocess.run(['ffmpeg','-hide_banner','-y','-i',str(raw),'-af',settings,'-ar',str(SR),'-c:a','pcm_s24le',str(final)],capture_output=True,text=True,check=True)
measured=measure(final)
# Short adverts can gate differently between loudnorm's two passes. Apply
# a final constant gain correction; it changes no musical timing or dynamics.
trim_db=round(-14-float(measured['input_i']),3)
if abs(trim_db)>.08:
    adjusted=OUT/'jjintern-compact-master-adjusted.wav'
    subprocess.run(['ffmpeg','-hide_banner','-y','-i',str(final),'-af',f'volume={trim_db}dB:precision=double','-ar',str(SR),'-c:a','pcm_s24le',str(adjusted)],capture_output=True,text=True,check=True)
    adjusted.replace(final)
    measured=measure(final)
fs,x=wavfile.read(final)
x=x.astype(np.float64)/2**31
manifest={
    'title':'A Small Advantage','revision':'Compact 10-second ad',
    'duration_seconds':10.,'samples':len(x),'sample_rate':fs,'channels':2,'bits_per_sample':24,
    'tempo_bpm':120,'groove_start_seconds':3.65,'key':'D major',
    'composition':'New short bass phrase; sparse rhythm, brief Dmaj9/Gmaj9 colour, resolved benefit close. No high arpeggio melody.',
    'originality':'All sources synthesized with sine/FM/additive oscillators, generated filtered noise and computed stereo reflections. No samples, stock loops, recordings, sampled impulse responses, vocals or external music models. Composed/resequenced for 10 seconds; no audio splice or speed-up.',
    'seed':10171026,
    'cues':[
        {'s':0,'cue':'Posting reveal, restrained original material note at0.18'},
        {'s':1.65,'cue':'Fold: four small contacts and pressure'},
        {'s':2.65,'cue':'Exactly1-second left-to-right travel'},
        {'s':3.65,'cue':'Website contact and bass groove arrival'},
        {'s':6.75,'cue':'Benefit and URL close; groove thins'},
        {'s':8.65,'cue':'Final low resolve'},
        {'s':9.9,'cue':'Fully settled silence'},
    ],
    'premaster':{key:float(first[key]) for key in ['input_i','input_tp','input_lra']},
    'master':{'file':final.name,'integrated_lufs':float(measured['input_i']),'true_peak_dbtp':float(measured['input_tp']),'loudness_range_lu':float(measured['input_lra']),'final_constant_gain_trim_db':trim_db},
    'verification':{'stereo_correlation':round(float(np.corrcoef(x.T)[0,1]),4),'last_sample':x[-1].tolist(),'silent_after_9_9':bool(np.all(x[round(9.9*SR):]==0))},
    'measurement_scope':'Delivery and signal-integrity checks only; these do not prove musical taste or a listening review.',
    'build_seconds':round(time.perf_counter()-START,3),
    'events':sorted(events,key=lambda item:item['seconds']),
}
(OUT/'score-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({key:manifest[key] for key in ['title','duration_seconds','master','verification','build_seconds']},indent=2))
print(final)
