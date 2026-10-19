import fs from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {once} from 'node:events';
import {promisify} from 'node:util';
import {createHash} from 'node:crypto';
import {connect} from '../../scripts/cdp.mjs';
const root=new URL('../',import.meta.url),run=promisify(execFile);
const mode=process.argv[3]||'stills';
const cdp=await connect(process.argv[2]||'9345');
let html=await fs.readFile(new URL('scene.html',import.meta.url),'utf8');
for(const [name,mime] of [['instrument-serif-latin-italic-400.woff2','font/woff2'],['logo-mark.png','image/png']]){
 const data=await fs.readFile(new URL(`../../assets/evidence/product/${name}`,import.meta.url));
 html=html.replace(`../../assets/evidence/product/${name}`,`data:${mime};base64,${data.toString('base64')}`);
}
let encoder;
const started=Date.now();
try{
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
 await cdp.send('Page.navigate',{url:`data:text/html;base64,${Buffer.from(html).toString('base64')}`});
 let ready=false;
 for(let i=0;i<100;i++){
  if(await cdp.evaluate('typeof window.ready!=="undefined"')){ready=true;break}
  await new Promise(r=>setTimeout(r,100));
 }
 if(!ready)throw Error('Scene failed to initialise');
 const metadata=await cdp.evaluate('window.ready');console.log(JSON.stringify(metadata));
 const take=async(t,quality='png')=>Buffer.from(await cdp.evaluate(`(window.drawScene(${t}),document.querySelector('canvas').toDataURL('image/${quality}',0.99).split(',')[1])`),'base64');
 const checkpoints=[.9,2,3.8,5,6.8,8.2,10.8,12.4,14.3,15.8,17.8,19.9];
 if(mode==='stills'){
  for(const [i,t] of checkpoints.entries())await fs.writeFile(new URL(`stills/frame-${String(i).padStart(2,'0')}-${t.toFixed(1)}s.png`,root),await take(t));
  // Full-frame 16:9 thumbnails: 640x360, plus a 30px label area.
  const sheet2=await cdp.evaluate(`(()=>{const s=document.createElement('canvas');s.width=1920;s.height=1560;const x=s.getContext('2d');x.fillStyle='#242426';x.fillRect(0,0,s.width,s.height);${JSON.stringify(checkpoints)}.forEach((t,i)=>{window.drawScene(t);const xx=i%3*640,yy=Math.floor(i/3)*390;x.drawImage(document.querySelector('canvas'),xx,yy,640,360);x.fillStyle='#fff';x.font='16px -apple-system';x.fillText(t.toFixed(1)+'s',xx+12,yy+382)});return s.toDataURL().split(',')[1]})()`);
  await fs.writeFile(new URL('stills/storyboard.png',root),Buffer.from(sheet2,'base64'));
  console.log('Storyboard exported');
 }else{
  const fps=mode==='rough'?20:60,count=20*fps;
  const output=new URL(mode==='rough'?'JJIntern-motion-rough.mp4':'JJIntern-Your-Next-Move-1080p60.mp4',root);
  const args=['-hide_banner','-loglevel','error','-y','-f','image2pipe','-framerate',String(fps),'-vcodec','png','-i','pipe:0','-i',new URL('audio/jjintern-original-score.wav',root).pathname,'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset',mode==='rough'?'veryfast':'slow','-crf',mode==='rough'?'21':'16','-pix_fmt','yuv420p','-profile:v','high','-level:v','4.2','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','320k','-ar','48000','-movflags','+faststart','-t','20',output.pathname];
  encoder=spawn('ffmpeg',args,{stdio:['pipe','inherit','inherit']});let error;
  encoder.on('error',e=>error=e);encoder.stdin.on('error',e=>error=e);const ended=once(encoder,'close');
  for(let i=0;i<count;i++){
   if(error)throw error;const frame=await take(i/fps);
   if(!encoder.stdin.write(frame))await once(encoder.stdin,'drain');
   if(i%60===0)console.log(`Frame ${i}/${count} / ${((Date.now()-started)/1000).toFixed(1)}s elapsed`);
  }
  encoder.stdin.end();const [code]=await ended;if(code!==0)throw Error('FFmpeg exit '+code);
  const media=JSON.parse((await run('ffprobe',['-v','error','-show_streams','-show_format','-of','json',output.pathname])).stdout);
  const bytes=await fs.readFile(output);
  await fs.writeFile(new URL(mode==='rough'?'rough-render.json':'render-manifest.json',root),JSON.stringify({mode,renderSeconds:(Date.now()-started)/1000,scene:metadata,browser:await cdp.send('Browser.getVersion'),node:process.version,frames:count,fps,sha256:createHash('sha256').update(bytes).digest('hex'),bytes:bytes.length,media,command:args},null,2)+'\n');
  console.log(`Exported ${output.pathname} in ${((Date.now()-started)/1000).toFixed(1)} seconds`);
 }
}catch(e){encoder?.kill();throw e}finally{cdp.close()}
