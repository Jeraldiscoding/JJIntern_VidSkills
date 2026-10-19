from pathlib import Path
import json, subprocess, hashlib, time
root=Path(__file__).resolve().parents[1]
video=root/'JJIntern-Your-Next-Move-1080p60.mp4'
report={'checked_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)],text=True))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'])==(1920,1080)
assert v['avg_frame_rate']=='60/1' and v['r_frame_rate']=='60/1'
assert v['nb_frames']=='1200' and v['nb_read_frames']=='1200'
assert float(probe['format']['duration'])==20.0
assert v['codec_name']=='h264' and v['pix_fmt']=='yuv420p'
assert a['codec_name']=='aac' and a['sample_rate']=='48000' and a['channels']==2
result=subprocess.run(['ffmpeg','-hide_banner','-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True)
assert result.returncode==0 and not result.stderr.strip(),result.stderr
r=subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-af','loudnorm=I=-14:TP=-1:LRA=7:print_format=json','-vn','-f','null','-'],capture_output=True,text=True,check=True)
start=r.stderr.rfind('{');end=r.stderr.rfind('}')+1
loudness=json.loads(r.stderr[start:end])
assert float(loudness['input_tp'])<0
for t,name in [(7.75,'poster'),(19.983333333,'final-frame'),(5.8,'transition-5.8'),(6.05,'transition-6.05'),(9.8,'transition-9.8'),(10.05,'transition-10.05')]:
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',str(root/'stills'/f'{name}.png')],check=True)
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(video),'-vf','fps=2,scale=480:270,tile=4x5','-frames:v','2',str(root/'review'/'final-timeline-%02d.png')],check=True)
report.update({'assertions':'PASS','video':v,'audio':a,'format':probe['format'],'full_decode_errors':result.stderr,'encoded_audio_loudness':loudness,'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'visual_checks':'Encoded contact sheets, transition-adjacent frames and last frame are exported for inspection; scripts do not judge design.'})
(root/'review'/'final-qa.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'result':'PASS','frames':v['nb_read_frames'],'duration':probe['format']['duration'],'size_MB':round(video.stat().st_size/1e6,2),'loudness':loudness},indent=2))
