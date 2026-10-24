import fs from 'node:fs/promises';
import {connect} from '../../../../scripts/cdp.mjs';
const cdp=await connect(process.argv[2]||'9372'),root=new URL('../',import.meta.url);
const report={scope:'Real-time local browser decode with muted and audio-enabled passes; screenshots from the decoded media. Not subjective listening or physical-phone playback.',passes:[]};
try{
 for(const format of ['wide','vertical']){
  const vertical=format==='vertical',width=vertical?360:960,height=vertical?640:540;
  const page=new URL(`review/playback-check-${format}.html`,root);await fs.writeFile(page,`<!doctype html><meta charset="utf-8"><style>*{box-sizing:border-box}body{margin:0;background:#edf3ff}video{display:block;width:${width}px;height:${height}px}</style><video playsinline preload="auto" src="../JJIntern-Find-your-focus-${format}.mp4"></video>`);
  await cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});
  await cdp.send('Page.navigate',{url:page.href});
  for(let i=0;i<100;i++){if(await cdp.evaluate('!!document.querySelector("video")&&document.querySelector("video").readyState>=2'))break;await new Promise(r=>setTimeout(r,100))}
  for(const muted of [true,false]){
   const play=await cdp.send('Runtime.evaluate',{expression:`(()=>{const v=document.querySelector('video');v.muted=${muted};v.currentTime=0;return v.play()})()`,userGesture:true,awaitPromise:true,returnByValue:true});if(play.exceptionDetails)throw Error(JSON.stringify(play.exceptionDetails));
   const observations=[];
   for(let i=0;i<17;i++){
    await new Promise(r=>setTimeout(r,1950));
    const state=await cdp.evaluate(`(()=>{const v=document.querySelector('video'),q=v.getVideoPlaybackQuality();return {time:v.currentTime,duration:v.duration,ended:v.ended,readyState:v.readyState,error:v.error?.message??null,decodedFrames:q.totalVideoFrames,droppedFrames:q.droppedVideoFrames,muted:v.muted}})()`);observations.push(state);
    if(muted){const shot=await cdp.send('Page.captureScreenshot',{format:'png'});await fs.writeFile(new URL(`review/playback-${format}-${String(i).padStart(2,'0')}.png`,root),Buffer.from(shot.data,'base64'))}
   }
   report.passes.push({format,muted,observations});console.log(JSON.stringify({format,muted,last:observations.at(-1)}));
   await fs.writeFile(new URL('review/browser-playback.json',root),JSON.stringify(report,null,2));
  }
 }
}finally{cdp.close()}
