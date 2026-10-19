import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {connect} from '../../../scripts/cdp.mjs';
const port=Number(process.argv[2]||9352), c=await connect(port);
const out=new URL('./',import.meta.url), states=[];
const delay=ms=>new Promise(r=>setTimeout(r,ms));
try{
 await c.send('Page.enable');
 if(await c.evaluate('location.href')!=='https://careers.microsoft.com/v2/global/en/students'){
  await c.send('Page.navigate',{url:'https://careers.microsoft.com/v2/global/en/students'});
  await delay(8000);
 }
 const reject=await c.evaluate(`[...document.querySelectorAll('button')].find(e=>e.innerText==='Reject')?.getBoundingClientRect().toJSON()`);
 if(reject&&reject.width){
  const x=reject.x+reject.width/2,y=reject.y+reject.height/2;
  await c.send('Input.dispatchMouseEvent',{type:'mousePressed',x,y,button:'left',clickCount:1});
  await c.send('Input.dispatchMouseEvent',{type:'mouseReleased',x,y,button:'left',clickCount:1});
 }
 for(const [name,width,height] of [['microsoft-internship-programmes',620,740],['microsoft-internship-programmes-540',540,780]]){
  await c.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:3,mobile:true});
  await c.evaluate('document.fonts.ready.then(()=>true)');
  await delay(700);
  await c.evaluate(`window.scrollTo(0,[...document.querySelectorAll('h2')].find(e=>e.innerText==='Internship programs').getBoundingClientRect().top+window.scrollY-8)`);
  await delay(600);
  const state=await c.evaluate(`({url:location.href,title:document.title,scrollY,innerWidth,innerHeight,devicePixelRatio,text:document.body.innerText,section:[...document.querySelectorAll('h2')].find(e=>e.innerText==='Internship programs').parentElement.outerHTML,headingBounds:[...document.querySelectorAll('h2,h3')].filter(e=>['Internship programs','Global university internships','Discovery program'].includes(e.innerText)).map(e=>({text:e.innerText,rect:e.getBoundingClientRect().toJSON()})),headerPosition:[...document.querySelectorAll('header')].map(e=>({position:getComputedStyle(e).position,rect:e.getBoundingClientRect().toJSON()}))})`);
  if(state.innerWidth!==width||state.innerHeight!==height)throw Error('Unexpected screenshot layout dimensions');
  const shot=await c.send('Page.captureScreenshot',{format:'png'}),bytes=Buffer.from(shot.data,'base64');
  await fs.writeFile(new URL(name+'.png',out),bytes);
  states.push({file:name+'.png',viewport:{width,height,deviceScaleFactor:3,mobile:true},sha256:createHash('sha256').update(bytes).digest('hex'),bytes:bytes.length,...state});
 }
 await fs.writeFile(new URL('microsoft-programmes-capture-record.json',out),JSON.stringify({checked:'2026-10-17',timezone:'Europe/Stockholm',captured_at_utc:new Date().toISOString(),source:'https://careers.microsoft.com/v2/global/en/students',session:'Isolated headless Chrome temporary profile, public logged-out session; optional cookies rejected. No personal account, role submission or content mutation.',scope:'Actual responsive public programme section. This establishes internship programme context, not a newly posted individual vacancy or JJIntern ingestion. Header is static and out of view after real scroll; do not transplant it.',states},null,2)+'\n');
 console.log(JSON.stringify(states.map(s=>({file:s.file,viewport:s.viewport,bounds:s.headingBounds})),null,2));
}finally{c.close()}
