import fs from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {once} from 'node:events';
import {promisify} from 'node:util';
import {createHash} from 'node:crypto';
import {connect} from '../../scripts/cdp.mjs';
const run=promisify(execFile),root=new URL('../vertical/',import.meta.url);
const mode=process.argv[3]||'stills',cdp=await connect(process.argv[2]||'9345');
let html=await fs.readFile(new URL('vertical-scene.html',import.meta.url),'utf8');
for(const [name,mime] of [['instrument-serif-latin-italic-400.woff2','font/woff2'],['logo-mark.png','image/png']]){
 const bytes=await fs.readFile(new URL(`../../assets/evidence/product/${name}`,import.meta.url));html=html.replace(`../../assets/evidence/product/${name}`,`data:${mime};base64,${bytes.toString('base64')}`);
}
// Replace the generated image URL template with an explicit embedded asset map.
const names=['directory-empty',...Array.from({length:9},(_,i)=>`directory-${String(i+1).padStart(2,'0')}`)],urls={};
for(const name of names)urls[name]=`data:image/png;base64,${(await fs.readFile(new URL(`product/${name}.png`,root))).toString('base64')}`;
html=html.replace('i.src=`../vertical/product/${n}.png`',`i.src=(${JSON.stringify(urls)})[n]`);
let encoder;const started=Date.now();
try{
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:1080,height:1920,deviceScaleFactor:1,mobile:false});
 await cdp.send('Page.navigate',{url:`data:text/html;base64,${Buffer.from(html).toString('base64')}`});
 let ready=false;for(let i=0;i<100;i++){if(await cdp.evaluate('typeof window.ready!=="undefined"')){ready=true;break}await new Promise(r=>setTimeout(r,100))}
 if(!ready)throw Error('Vertical scene did not initialise');const scene=await cdp.evaluate('window.ready');console.log(JSON.stringify(scene));
 const take=async t=>Buffer.from(await cdp.evaluate(`(drawScene(${t}),document.querySelector('canvas').toDataURL('image/png').split(',')[1])`),'base64');
 if(mode==='stills'){
  const times=[.8,2.2,3.6,4.8,5.9,7.4,9,10.8,12.3,14.3,15.6,17.8,19.95];
  for(const t of times)await fs.writeFile(new URL(`stills/${t.toFixed(2)}s.png`,root),await take(t));
  for(let page=0;page<3;page++){
   const selected=times.slice(page*5,page*5+5);
   const data=await cdp.evaluate(`(()=>{const s=document.createElement('canvas');s.width=1800;s.height=670;const x=s.getContext('2d');x.fillStyle='#242426';x.fillRect(0,0,s.width,s.height);${JSON.stringify(selected)}.forEach((t,i)=>{drawScene(t);x.drawImage(document.querySelector('canvas'),i*360,0,360,640);x.fillStyle='#fff';x.font='18px -apple-system';x.fillText(t.toFixed(2)+'s',i*360+12,662)});return s.toDataURL().split(',')[1]})()`);
   await fs.writeFile(new URL(`stills/storyboard-${page+1}.png`,root),Buffer.from(data,'base64'));
  }console.log('Vertical storyboard exported');
 }else{
  const fps=mode==='rough'?24:120,count=fps*20;
  const output=new URL(mode==='rough'?'JJIntern-vertical-rough.mp4':'JJIntern-TikTok-1080x1920-120fps-master.mp4',root);
  const args=['-hide_banner','-loglevel','error','-y','-f','image2pipe','-framerate',String(fps),'-vcodec','png','-i','pipe:0','-i',new URL('../audio/jjintern-original-score.wav',root).pathname,'-map','0:v:0','-map','1:a:0','-vf','scale=in_range=full:out_range=limited:out_color_matrix=bt709,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709,setsar=1','-c:v','libx264','-preset',mode==='rough'?'veryfast':'medium','-crf',mode==='rough'?'20':'15','-pix_fmt','yuv420p','-profile:v','high','-level:v',mode==='rough'?'4.2':'5.1','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','320k','-ar','48000','-movflags','+faststart','-t','20',output.pathname];
  // Both encodes receive the original PNG stream. The upload copy selects alternate native frames.
  if(mode!=='rough')args.push('-map','0:v:0','-map','1:a:0','-vf','fps=60,scale=in_range=full:out_range=limited:out_color_matrix=bt709,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709,setsar=1','-c:v','libx264','-preset','medium','-crf','15','-pix_fmt','yuv420p','-profile:v','high','-level:v','4.2','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','320k','-ar','48000','-movflags','+faststart','-t','20',new URL('JJIntern-TikTok-1080x1920-60fps.mp4',root).pathname);
  encoder=spawn('ffmpeg',args,{stdio:['pipe','inherit','inherit']});let err;encoder.on('error',e=>err=e);encoder.stdin.on('error',e=>err=e);const ended=once(encoder,'close');
  for(let i=0;i<count;i++){if(err)throw err;const frame=await take(i/fps);if(!encoder.stdin.write(frame))await once(encoder.stdin,'drain');if(i%120===0)console.log(`${i}/${count} frames; ${((Date.now()-started)/1000).toFixed(1)}s elapsed`)}
  encoder.stdin.end();const [code]=await ended;if(code!==0)throw Error('FFmpeg '+code);
  const media=JSON.parse((await run('ffprobe',['-v','error','-show_streams','-show_format','-of','json',output.pathname])).stdout),bytes=await fs.readFile(output);
  const manifest={mode,scene,frames:count,fps,renderSeconds:(Date.now()-started)/1000,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex'),media,browser:await cdp.send('Browser.getVersion'),command:args};
  if(mode!=='rough'){
   const upload=new URL('JJIntern-TikTok-1080x1920-60fps.mp4',root),b=await fs.readFile(upload);
   manifest.tiktokCopy={frames:1200,fps:60,source:'Alternate original PNG frames, without double compression or optical flow',bytes:b.length,sha256:createHash('sha256').update(b).digest('hex'),media:JSON.parse((await run('ffprobe',['-v','error','-show_streams','-show_format','-of','json',upload.pathname])).stdout)};
  }
  await fs.writeFile(new URL(mode==='rough'?'rough-render.json':'render-manifest.json',root),JSON.stringify(manifest,null,2)+'\n');
  console.log(`Rendered ${output.pathname} in ${manifest.renderSeconds.toFixed(1)} seconds`);
 }
}catch(e){encoder?.kill();throw e}finally{cdp.close()}
