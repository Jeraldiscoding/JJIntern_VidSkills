import fs from 'node:fs/promises';
import {connect} from '../../scripts/cdp.mjs';
const cdp=await connect(process.argv[2]||'9345');
const report={performed:'Full real-time browser playback, muted then sound-enabled. Frame assessment is separate; sound-enabled decode is not a claim of subjective human listening.',passes:[]};
try{
 await cdp.send('Page.navigate',{url:new URL('../slick/playback.html',import.meta.url).href});
 for(let i=0;i<100;i++){if(await cdp.evaluate('!!document.querySelector("video")&&document.querySelector("video").readyState>=2'))break;await new Promise(r=>setTimeout(r,100))}
 for(const muted of [true,false]){
  await cdp.evaluate(`(()=>{const v=document.querySelector('video');v.muted=${muted};v.currentTime=0;v.controls=false;return v.play().then(()=>true)})()`);
  const start=Date.now(),observations=[];
  for(let i=0;i<5;i++){
   await new Promise(r=>setTimeout(r,4100));
   observations.push(await cdp.evaluate(`(()=>{const v=document.querySelector('video'),q=v.getVideoPlaybackQuality();return{time:v.currentTime,ended:v.ended,paused:v.paused,readyState:v.readyState,error:v.error?.message??null,decodedFrames:q.totalVideoFrames,droppedFrames:q.droppedVideoFrames,muted:v.muted}})()`));
  }
  report.passes.push({muted,wallSeconds:(Date.now()-start)/1000,observations});
 }
 await fs.writeFile(new URL('../slick/review/browser-playback.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{cdp.close()}
