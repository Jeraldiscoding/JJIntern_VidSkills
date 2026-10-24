#!/usr/bin/env python3
"""Inspect encoded media, decode every frame and preserve representative evidence."""
import hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'review'
def run(args):
    return subprocess.run(args,check=True,capture_output=True,text=True)
def probe(p):
    return json.loads(run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]).stdout)
def boxes(p):
    raw=p.read_bytes();out=[];pos=0
    while pos+8<=len(raw):
        size,name=struct.unpack('>I4s',raw[pos:pos+8]);name=name.decode('ascii',errors='replace')
        if size==1:size=struct.unpack('>Q',raw[pos+8:pos+16])[0]
        if size==0:size=len(raw)-pos
        if size<8:break
        out.append({'type':name,'offset':pos,'size':size});pos+=size
    return out
results=[]
for fmt in ['wide','vertical']:
    path=ROOT/f'JJIntern-Find-your-focus-{fmt}.mp4';m=probe(path)
    video=next(s for s in m['streams'] if s['codec_type']=='video');aud=next(s for s in m['streams'] if s['codec_type']=='audio')
    dims=(1920,1080) if fmt=='wide' else (1080,1920)
    checks={'dimensions':(video['width'],video['height'])==dims,'duration':abs(float(m['format']['duration'])-32)<.001,'native_60fps':video['r_frame_rate']=='60/1' and video['avg_frame_rate']=='60/1','frames_1920':int(video['nb_read_frames'])==1920,'h264_yuv420p':video['codec_name']=='h264' and video['pix_fmt']=='yuv420p','bt709':all(video.get(x)=='bt709' for x in ['color_space','color_transfer','color_primaries']),'aac_stereo_48k':aud['codec_name']=='aac' and aud['sample_rate']=='48000' and aud['channels']==2}
    atoms=boxes(path);types=[a['type'] for a in atoms];checks['faststart']=types.index('moov')<types.index('mdat')
    decoded=run(['ffmpeg','-v','error','-i',str(path),'-f','null','-']);checks['full_decode']=decoded.stderr.strip()==''
    for t in [.8,4.3,7.12,7.25,7.6,9.75,11.75,12.2,13.9,14.4,14.55,14.9,15.58,17.983333,18.15,20.5,22,22.35,24.6,28.1,31.983333]:
        run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(path),'-frames:v','1',str(REVIEW/f'encoded-{fmt}-{t:.3f}.png')])
    run(['ffmpeg','-v','error','-y','-i',str(path),'-vf','fps=1,scale=240:-1,tile=8x4:padding=4:margin=4:color=0x203145','-frames:v','1',str(REVIEW/f'encoded-{fmt}-overview.png')])
    hold=[];hold_pixels=[]
    for t in [30,31,31.983333]:
        raw=subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(path),'-frames:v','1','-vf','scale=480:-1','-f','rawvideo','-pix_fmt','gray','pipe:1'],check=True,capture_output=True).stdout
        hold.append({'time':t,'sha256':hashlib.sha256(raw).hexdigest()});hold_pixels.append(raw)
    residuals=[]
    for current in hold_pixels[1:]:
        diffs=[abs(a-b) for a,b in zip(hold_pixels[0],current)]
        residuals.append({'mean_absolute_luma_difference':sum(diffs)/len(diffs),'fraction_over_3_levels':sum(d>3 for d in diffs)/len(diffs)})
    # Lossy H.264 may reconstruct static edges differently across GOPs.
    # Tolerance checks visible stability, rather than requiring identical decoded bytes.
    checks['stable_final_hold']=all(r['mean_absolute_luma_difference']<.05 and r['fraction_over_3_levels']<.001 for r in residuals)
    result={'format':fmt,'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'checks':checks,'media':m,'final_hold':hold,'static_hold_codec_residuals':residuals,'mp4_atoms':atoms}
    results.append(result)
    print(fmt,json.dumps(checks))
report={'outputs':results,'all_pass':all(all(r['checks'].values()) for r in results),'limits':'Technical decode and encoded still generation. Does not establish subjective sound, physical-phone viewing or platform upload preview.'}
(REVIEW/'technical-qa.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['all_pass'],'A technical check failed; inspect report.'
