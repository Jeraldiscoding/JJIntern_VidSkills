from pathlib import Path
import json,subprocess,hashlib,time
r=Path(__file__).resolve().parents[1]/'slick'
results=[]
for name,fps,count in [('JJIntern-Slick-120fps-master.mp4',120,2400),('JJIntern-Slick-TikTok-60fps.mp4',60,1200)]:
 p=r/name
 data=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)],text=True))
 v=next(s for s in data['streams'] if s['codec_type']=='video');a=next(s for s in data['streams'] if s['codec_type']=='audio')
 assert(v['width'],v['height'])==(1080,1920)
 assert v['r_frame_rate']==v['avg_frame_rate']==f'{fps}/1'
 assert int(v['nb_frames'])==int(v['nb_read_frames'])==count
 assert v['sample_aspect_ratio']=='1:1' and v['display_aspect_ratio']=='9:16'
 assert float(data['format']['duration'])==20
 assert v['codec_name']=='h264' and v['pix_fmt']=='yuv420p'
 assert v['color_space']==v['color_transfer']==v['color_primaries']=='bt709'
 assert a['codec_name']=='aac' and a['sample_rate']=='48000' and a['channels']==2
 decoded=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True,check=True)
 assert not decoded.stderr.strip(),decoded.stderr
 result={'file':name,'status':'PASS','fps':fps,'frames':count,'dimensions':[1080,1920],'duration':20,'size_MB':round(p.stat().st_size/1e6,2),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'full_decode_errors':decoded.stderr,'media':data}
 results.append(result)
 if fps==120:
  native=subprocess.check_output(['ffmpeg','-v','error','-ss','5','-i',str(p),'-frames:v','6','-vf','scale=108:192','-pix_fmt','rgb24','-f','rawvideo','-'])
  frame_bytes=108*192*3
  hashes=[hashlib.sha256(native[i:i+frame_bytes]).hexdigest() for i in range(0,len(native),frame_bytes)]
  assert len(hashes)==len(set(hashes))==6,'Moving section has duplicated adjacent native frames'
  result['native_motion_check']={'start_s':5.0,'consecutive_native_frames':6,'unique_frame_hashes':len(set(hashes)),'result':'PASS: six distinct consecutive 120 fps motion frames'}
 for t,label in [(.65,'intro'),(2.8,'posting'),(3.95,'fold'),(4.6,'packet'),(5.12,'flight'),(5.65,'arrival'),(7.,'feed'),(11.2,'cadence'),(15.8,'benefit'),(19.98333,'final')]:
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(p),'-frames:v','1',str(r/'stills'/f'encoded-{fps}-{label}.png')],check=True)
 if fps==60:
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(p),'-vf','fps=2,scale=216:384,tile=5x4','-frames:v','2',str(r/'review'/'final-timeline-%02d.png')],check=True)
  l=subprocess.run(['ffmpeg','-hide_banner','-i',str(p),'-vn','-af','loudnorm=I=-14:TP=-1:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True).stderr
  result['encoded_audio_loudness']=json.loads(l[l.rfind('{'):l.rfind('}')+1]);assert float(result['encoded_audio_loudness']['input_tp'])<0
report={'checked_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'files':results,'video_source':'Native120fps deterministic geometry.60fps encode selects original alternate PNG frames; no interpolation, duplication or intermediatevideo transcode.','audio_source':'New V4 original 20-second bass-led composition; synthesized posting strike, fold contacts, one-second stereo launch, arrival and resolution; no samples.','limits':'Visual samples and automated playback do not certify physicalphone or actualTikTok uploadpreview.'}
(r/'review'/'final-qa.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([{k:x[k] for k in ['file','status','fps','frames','dimensions','duration','size_MB']} for x in results],indent=2))
