import fs from 'node:fs/promises';
import {connect} from '../../../../scripts/cdp.mjs';
const cdp=await connect(process.argv[2]||'9356'),mode=process.argv[3]||'test',root=new URL('../',import.meta.url);
const name=mode==='test'?'JJIntern-revision06-motion-test.mp4':'JJIntern-revision06-60fps.mp4';
const page=new URL(mode==='test'?'motion-test-playback.html':'playback.html',root);
await fs.writeFile(page,`<!doctype html><meta charset="utf-8"><title>JJIntern revision 06</title><style>html,body{margin:0;height:100%;background:#edf3ff}body{display:grid;place-items:center}video{display:block;height:96vh;max-width:100%;object-fit:contain}</style><video controls playsinline preload="auto" src="${name}"></video>`);
const report={kind:'Actual real-time browser playback and decoded-frame capture; no claim of subjective audio audition',mode,passes:[]};
try{
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:1080,height:1920,deviceScaleFactor:1,mobile:false});
 await cdp.send('Page.navigate',{url:page.href});
 for(let i=0;i<100;i++){if(await cdp.evaluate('!!document.querySelector("video")&&document.querySelector("video").readyState>=2'))break;await new Promise(r=>setTimeout(r,100))}
 await cdp.evaluate(`(()=>{const v=document.querySelector('video');v.controls=false;v.style.cssText='width:1080px;height:1920px;max-width:none;display:block';document.body.style.cssText='display:block;margin:0;width:1080px;height:1920px'})()`);
 for(const muted of (mode==='test'?[true]:[true,false])){
  await cdp.evaluate(`(()=>{const v=document.querySelector('video');v.muted=${muted};v.currentTime=0;return v.play()})()`);
  const observations=[];
  const count=mode==='test'?7:12;
  for(let i=0;i<count;i++){
   await new Promise(r=>setTimeout(r,mode==='test'?510:1020));
   const state=await cdp.evaluate(`(()=>{const v=document.querySelector('video'),q=v.getVideoPlaybackQuality();return {time:v.currentTime,duration:v.duration,ended:v.ended,paused:v.paused,readyState:v.readyState,error:v.error?.message??null,decodedFrames:q.totalVideoFrames,droppedFrames:q.droppedVideoFrames,muted:v.muted}})()`);
   observations.push(state);
   if(muted){const shot=await cdp.send('Page.captureScreenshot',{format:'png',clip:{x:0,y:0,width:1080,height:1920,scale:1/3}});await fs.writeFile(new URL(`review/${mode}-playback-${String(i).padStart(2,'0')}.png`,root),Buffer.from(shot.data,'base64'))}
  }
  report.passes.push({muted,observations});
 }
 await fs.writeFile(new URL(`review/${mode}-browser-playback.json`,root),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report));
}finally{cdp.close()}
