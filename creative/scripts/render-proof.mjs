import fs from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import http from 'node:http';
import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import os from 'node:os';
import { connect } from './cdp.mjs';

const cdp=await connect(process.argv[2]);
const scene=new URL('../examples/proof/scene.html',import.meta.url);
const output=new URL('../examples/proof/company-search-rough.mp4',import.meta.url);
// Serve only the scene and named public captures, on loopback. Never serve the workspace root.
const server=http.createServer(async(req,res)=>{
  const pathname=new URL(req.url,'http://localhost').pathname;
  let file;
  if(pathname==='/examples/proof/scene.html') file=scene;
  else if(/^\/assets\/captures\/directory-(empty|\d{2})\.png$/.test(pathname))
    file=new URL(`..${pathname}`,import.meta.url);
  else {res.writeHead(404);res.end();return;}
  try {
    const data=await fs.readFile(file);
    res.setHeader('Content-Type',pathname.endsWith('.png')?'image/png':'text/html; charset=utf-8');
    res.end(data);
  } catch {res.writeHead(404);res.end();}
});
server.listen(0,'127.0.0.1');await once(server,'listening');
let ffmpeg;
try {
  await cdp.send('Emulation.setDeviceMetricsOverride',{width:1080,height:1920,deviceScaleFactor:1,mobile:false});
  await cdp.send('Page.navigate',{url:`http://127.0.0.1:${server.address().port}/examples/proof/scene.html`});
  let ready=false;
  for(let i=0;i<30;i++) {
    if(await cdp.evaluate('typeof window.ready !== "undefined"')) {ready=true;break;}
    await new Promise(r=>setTimeout(r,100));
  }
  if(!ready) throw new Error('Scene failed to load.');
  await cdp.evaluate('window.ready.then(()=>true)');
  ffmpeg=spawn('ffmpeg',[
    '-hide_banner','-loglevel','error','-y','-f','image2pipe','-framerate','30','-vcodec','png','-i','pipe:0',
    '-an','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',output.pathname,
  ],{stdio:['pipe','inherit','inherit']});
  let processError;
  ffmpeg.on('error',error=>{processError=error;});
  ffmpeg.stdin.on('error',error=>{processError=error;});
  const completion=once(ffmpeg,'close');
  for(let frame=0;frame<360;frame++) {
    if(processError) throw processError;
    const png=await cdp.evaluate(`(window.drawScene(${frame}/30),document.querySelector('canvas').toDataURL('image/png').split(',')[1])`);
    if(!ffmpeg.stdin.write(Buffer.from(png,'base64'))) await once(ffmpeg.stdin,'drain');
    if(frame%90===0) console.log(`Rendered ${frame}/360 frames`);
  }
  ffmpeg.stdin.end();
  const [code]=await completion;
  if(code!==0) throw new Error(`FFmpeg exit ${code}`);
  const checkpoints=[0,2.5,4.75,6.5,9,11];
  for(const [i,t] of checkpoints.entries()) {
    const png=await cdp.evaluate(`(window.drawScene(${t}),document.querySelector('canvas').toDataURL('image/png').split(',')[1])`);
    await fs.writeFile(new URL(`../examples/proof/frame-${i}.png`,import.meta.url),Buffer.from(png,'base64'));
  }
  // Independent phone-size contact sheet for visual review of all narrative beats.
  const sheet=await cdp.evaluate(`(() => {
    const sheet=document.createElement('canvas');sheet.width=1080;sheet.height=1332;
    const s=sheet.getContext('2d');s.fillStyle='#fff';s.fillRect(0,0,1080,1332);
    ${JSON.stringify(checkpoints)}.forEach((t,i)=>{
      window.drawScene(t);const x=(i%3)*360,y=Math.floor(i/3)*666;
      s.drawImage(document.querySelector('canvas'),x,y,360,640);
      s.fillStyle='#111';s.font='16px Arial';s.fillText(t.toFixed(2)+'s',x+10,y+660);
    });
    return sheet.toDataURL('image/png').split(',')[1];
  })()`);
  await fs.writeFile(new URL('../examples/proof/contact-sheet.png',import.meta.url),Buffer.from(sheet,'base64'));
  const run=promisify(execFile);
  const probe=JSON.parse((await run('ffprobe',['-v','error','-show_entries',
    'format=duration,size:stream=codec_name,width,height,pix_fmt,avg_frame_rate,nb_frames','-of','json',output.pathname])).stdout);
  if(probe.format.duration!=='12.000000' || probe.streams[0].nb_frames!=='360')
    throw new Error('Unexpected output duration/frame count; inspect before handoff.');
  const capture=JSON.parse(await fs.readFile(new URL('../assets/captures/capture-record.json',import.meta.url),'utf8'));
  const names=[
    'creative/scripts/cdp.mjs','creative/scripts/capture-public.mjs','creative/scripts/render-proof.mjs',
    'creative/examples/proof/scene.html','creative/examples/proof/company-search-rough.mp4',
    'creative/examples/proof/transcript.vtt','creative/examples/proof/caption.txt',
    'creative/brand/tokens.json','creative/assets/captures/capture-record.json',
    ...capture.states.map(state=>`creative/assets/captures/${state.file}`),
  ];
  const root=new URL('../../',import.meta.url);
  const sources=[];
  for(const path of names) {
    const bytes=await fs.readFile(new URL(path,root));
    sources.push({path,sha256:createHash('sha256').update(bytes).digest('hex'),bytes:bytes.length});
  }
  const manifest={
    captureChecked:capture.checked,
    intendedPlacement:'Organic Instagram Reel; actual placement preview pending',
    purpose:'Local timing proof using discrete real public UI states; no latency/vacancy/outcome claim',
    tools:{node:process.version,host:`${os.type()} ${os.release()} ${process.arch}`,
      chrome:await cdp.send('Browser.getVersion'),ffmpeg:(await run('ffmpeg',['-version'])).stdout.split('\n')[0]},
    reproduction:'node creative/scripts/render-proof.mjs PORT',
    crop:{raw:{x:32,y:430,width:716,height:490},canvas:{x:90,y:610,width:804,height:550}},
    sound:'No audio; silent comprehension intentional',media:probe,sources,
  };
  await fs.writeFile(new URL('../examples/proof/render-manifest.json',import.meta.url),JSON.stringify(manifest,null,2)+'\n');
  console.log(`Exported ${output.pathname}`);
} catch(error) {
  ffmpeg?.kill();
  throw error;
} finally {cdp.close();server.close();}
