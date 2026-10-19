import fs from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {once} from 'node:events';
import {promisify} from 'node:util';
import {createHash} from 'node:crypto';
import {connect} from '../../../../scripts/cdp.mjs';
const run=promisify(execFile),root=new URL('../',import.meta.url),mode=process.argv[3]||'stills';
const cdp=await connect(process.argv[2]||'9355');
const logoURL=new URL('../../../../assets/evidence/product/logo-mark.png',import.meta.url),logo=await fs.readFile(logoURL);
let html=await fs.readFile(new URL('motion.html',import.meta.url),'utf8');html=html.replace('LOGO_IMAGE',`data:image/png;base64,${logo.toString('base64')}`);
let encoder;const started=Date.now();
await fs.mkdir(new URL('stills/',root),{recursive:true});await fs.mkdir(new URL('review/',root),{recursive:true});
try{
 await fs.writeFile(new URL('motion-preview.html',import.meta.url),html);
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:1080,height:1920,deviceScaleFactor:1,mobile:false});
 await cdp.send('Page.navigate',{url:new URL('motion-preview.html',import.meta.url).href});
 for(let i=0;i<100;i++){if(await cdp.evaluate('typeof window.ready!=="undefined"'))break;await new Promise(r=>setTimeout(r,100))}
 const scene=await cdp.evaluate('window.ready');console.log(JSON.stringify(scene));
 const take=async(t,w=1080)=>Buffer.from(await cdp.evaluate(`framePNG(${t},${w})`),'base64');
 if(mode==='stills'){
  const times=[0,.6,2.9,3.3,3.7,4.1,4.5,5,5.5,6,6.49,6.5,6.65,6.8,7.1,9.9,10.3,10.8,11.3,14.99,15.4,17.9916667];
  for(const t of times)await fs.writeFile(new URL(`stills/${t.toFixed(3)}s.png`,root),await take(t));
  for(let page=0;page<4;page++){
   const selected=times.slice(page*6,page*6+6);
   const data=await cdp.evaluate(`(()=>{const s=document.createElement('canvas');s.width=1800;s.height=565;const x=s.getContext('2d');x.fillStyle='#203145';x.fillRect(0,0,s.width,s.height);${JSON.stringify(selected)}.forEach((t,i)=>{drawScene(t);x.drawImage(canvas,i*300,0,300,533);x.fillStyle='#fff';x.font='17px -apple-system';x.fillText(t.toFixed(3)+'s',i*300+14,555)});return s.toDataURL().split(',')[1]})()`);
   await fs.writeFile(new URL(`review/motion-board-${page+1}.png`,root),Buffer.from(data,'base64'));
  }
  const positions=await cdp.evaluate('Array.from({length:241},(_,i)=>({frame:540+i,t:4.5+i/120,...flightState(4.5+i/120)}))');
  await fs.writeFile(new URL('review/flight-positions.json',root),JSON.stringify({scene,positions},null,2)+'\n');
 }else{
  const rough=mode==='test',fps=rough?60:120,start=rough?2.5:0,duration=rough?5:18,count=Math.round(fps*duration),width=rough?720:1080;
  const target=new URL(rough?'JJIntern-revision05-motion-test.mp4':'JJIntern-revision05-120fps-master.mp4',root);
  const conversion='scale=in_range=full:out_range=limited:out_color_matrix=bt709,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709,setsar=1';
  const args=['-hide_banner','-loglevel','error','-y','-f','image2pipe','-framerate',String(fps),'-vcodec','png','-i','pipe:0'];
  if(!rough)args.push('-i',new URL('audio/jjintern-revision-05-original-score.wav',root).pathname);
  function outputArgs(url,rate){args.push('-map','0:v:0');if(!rough)args.push('-map','1:a:0');args.push('-vf',(rate===60&&!rough?"select='not(mod(n,2))',setpts=N/(60*TB),":'')+conversion,'-r',String(rate),'-fps_mode','cfr','-c:v','libx264','-preset',rough?'veryfast':'medium','-crf',rough?'18':'15','-pix_fmt','yuv420p','-profile:v','high','-level:v',rate===120?'5.2':'4.2','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709');if(!rough)args.push('-c:a','aac','-b:a','320k','-ar','48000');args.push('-movflags','+faststart','-t',String(duration),url.pathname)}
  outputArgs(target,fps);if(!rough)outputArgs(new URL('JJIntern-revision05-60fps.mp4',root),60);
  encoder=spawn('ffmpeg',args,{stdio:['pipe','inherit','inherit']});let err;encoder.on('error',e=>err=e);encoder.stdin.on('error',e=>err=e);const ended=once(encoder,'close');
  for(let i=0;i<count;i++){if(err)throw err;const b=await take(start+i/fps,width);if(!encoder.stdin.write(b))await once(encoder.stdin,'drain');if(i%120===0)console.log(`${i}/${count} frames; ${((Date.now()-started)/1000).toFixed(1)}s elapsed`)}
  encoder.stdin.end();const [code]=await ended;if(code!==0)throw Error('FFmpeg exit '+code);
  const manifest={mode,scene,start,duration,fps,frames:count,width,height:width*16/9,renderSeconds:(Date.now()-started)/1000,browser:await cdp.send('Browser.getVersion'),logo:{path:logoURL.pathname,sha256:createHash('sha256').update(logo).digest('hex'),treatment:'Original RGBA asset unchanged; masked reveal and uniform translation only'},sourceSha256:createHash('sha256').update(html).digest('hex'),outputs:[],command:args};
  for(const name of [target.pathname,...(!rough?[new URL('JJIntern-revision05-60fps.mp4',root).pathname]:[])]){const b=await fs.readFile(name);manifest.outputs.push({path:name,bytes:b.length,sha256:createHash('sha256').update(b).digest('hex'),media:JSON.parse((await run('ffprobe',['-v','error','-show_streams','-show_format','-of','json',name])).stdout)})}
  await fs.writeFile(new URL(rough?'motion-test-manifest.json':'render-manifest.json',root),JSON.stringify(manifest,null,2)+'\n');console.log('Completed '+mode);
 }
}catch(e){encoder?.kill();throw e}finally{cdp.close()}
