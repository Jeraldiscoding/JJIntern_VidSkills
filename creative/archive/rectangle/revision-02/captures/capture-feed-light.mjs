import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {connect} from '../../../../scripts/cdp.mjs';
const c=await connect(Number(process.argv[2]||9356));
const out=new URL('./',import.meta.url),states=[],interactions=[];
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const inspect=`(()=>{const bounds=e=>e.getBoundingClientRect().toJSON();return{url:location.href,title:document.title,scrollY,viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},text:document.body.innerText,query:document.querySelector('input[placeholder="Search company or role"]')?.value,style:{background:getComputedStyle(document.body).backgroundColor,rootClass:document.documentElement.className},buttons:[...document.querySelectorAll('button')].map(e=>({text:e.innerText,aria:e.getAttribute('aria-label'),title:e.getAttribute('title'),bounds:bounds(e),class:e.className})).filter(e=>e.bounds.width>0),headers:[...document.querySelectorAll('header')].map(e=>({text:e.innerText,bounds:bounds(e),position:getComputedStyle(e).position})),fixedOrSticky:[...document.querySelectorAll('body *')].filter(e=>['fixed','sticky'].includes(getComputedStyle(e).position)).map(e=>({tag:e.tagName,class:e.className,text:e.innerText.slice(0,300),position:getComputedStyle(e).position,bounds:bounds(e)}))}})()`;
async function capture(file){const state=await c.evaluate(inspect);if(state.viewport.width!==430||state.viewport.height!==840||state.viewport.dpr!==4)throw Error('Unexpected capture viewport');const shot=await c.send('Page.captureScreenshot',{format:'png'}),b=Buffer.from(shot.data,'base64');await fs.writeFile(new URL(file,out),b);const entry={file,sha256:createHash('sha256').update(b).digest('hex'),bytes:b.length,...state};states.push(entry);return entry;}
async function click(expression,label){const r=await c.evaluate(expression);if(!r?.width||!r?.height)throw Error('No visible actual '+label);const x=r.x+r.width/2,y=r.y+r.height/2;await c.send('Input.dispatchMouseEvent',{type:'mousePressed',x,y,button:'left',clickCount:1});await c.send('Input.dispatchMouseEvent',{type:'mouseReleased',x,y,button:'left',clickCount:1});interactions.push({type:'actual pointer click',label,x,y});}
try{
 await c.send('Page.enable');
 await c.send('Emulation.setDeviceMetricsOverride',{width:430,height:840,deviceScaleFactor:4,mobile:true});
 await c.evaluate('window.scrollTo(0,0)');
 await delay(700);
 if(await c.evaluate('location.href')!=='https://jjintern.com/feed')throw Error('Expected isolated public feed already opened');
 await c.evaluate('document.fonts.ready.then(()=>true)');
 if(await c.evaluate('document.documentElement.className.includes("light")')){
  await click(`[...document.querySelectorAll('button[aria-label="Switch to dark mode"]')].find(e=>e.getBoundingClientRect().width>0)?.getBoundingClientRect().toJSON()`,'Switch to dark mode to restore before state');
  await delay(500);
 }
 await click(`[...document.querySelectorAll('button')].find(e=>e.innerText==='All roles' && e.getBoundingClientRect().width>0)?.getBoundingClientRect().toJSON()`,'All roles to restore before state');
 await delay(500);
 for(let i=0;i<40;i++){if(await c.evaluate('document.body.innerText.includes("ByteDance") && document.body.innerText.includes("Set status")'))break;await delay(500);}
 if(!await c.evaluate('document.body.innerText.includes("ByteDance")'))throw Error('No loaded roles');
 await capture('feed-dark-before.png');
 await click(`[...document.querySelectorAll('button[aria-label="Switch to light mode"]')].find(e=>e.getBoundingClientRect().width>0)?.getBoundingClientRect().toJSON()`,'Switch to light mode');
 await delay(700);
 const light=await capture('feed-light-all.png');
 if(light.style.rootClass.includes('dark'))throw Error('Actual theme click did not enter light theme');
 await click(`[...document.querySelectorAll('button')].find(e=>e.innerText==='Tech' && e.getBoundingClientRect().width>0)?.getBoundingClientRect().toJSON()`,'Tech category');
 await delay(400);
 for(let i=0;i<60;i++){if(await c.evaluate('document.body.innerText.includes("Tencent") && document.body.innerText.includes("Set status") && !document.body.innerText.includes("ByteDance")'))break;await delay(500);}
 if(!await c.evaluate('document.body.innerText.includes("Tencent") && document.body.innerText.includes("Set status") && !document.body.innerText.includes("ByteDance")'))throw Error('Tech category did not produce loaded filtered roles');
 await delay(700);
 const tech=await capture('feed-light-tech.png');
 await c.evaluate('window.scrollTo(0,100)');
 interactions.push({type:'actual scroll',scrollY:100,purpose:'Move aggregate metrics out while genuine sticky header and filters remain'});
 await delay(500);
 await capture('feed-light-tech-scrolled.png');
 await fs.writeFile(new URL('feed-light-tech-dom.html',out),await c.evaluate('document.documentElement.outerHTML'));
 const record={checked:'2026-10-17',timezone:'Europe/Stockholm',captured_at_utc:new Date().toISOString(),source:'https://jjintern.com/feed',session:'Fresh isolated logged-out Chrome profile /tmp/jjintern-rectangle-revision02-public-9356; no account or personal data. System dark preference emulated before real theme-toggle click.',scope:'Loaded public feed; actual theme toggle and actual Tech category button. Existing roles only; no Microsoft search, role opening, handoff, application, notification, source ingestion or data write.',interactions,states};
 await fs.writeFile(new URL('capture-record.json',out),JSON.stringify(record,null,2)+'\n');
 console.log(JSON.stringify(states.map(s=>({file:s.file,viewport:s.viewport,style:s.style,text:s.text.slice(0,1500),fixedOrSticky:s.fixedOrSticky})),null,2));
}finally{c.close();}
