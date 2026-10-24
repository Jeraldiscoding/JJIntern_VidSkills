import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {connect} from '../../../scripts/cdp.mjs';

const c=await connect(Number(process.argv[2]||9347));
const out=new URL('./',import.meta.url),states=[],interactions=[];
const width=Number(process.argv[3]||900),prefix=process.argv[4]||'';
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function waitFor(expression){for(let i=0;i<60;i++){if(await c.evaluate(expression))return;await delay(500);}throw Error('Condition not reached: '+expression);}
async function click(selector,label){const r=await c.evaluate(selector);if(!r?.width||!r?.height)throw Error('Missing '+label);const x=r.x+r.width/2,y=r.y+r.height/2;await c.send('Input.dispatchMouseEvent',{type:'mousePressed',x,y,button:'left',clickCount:1});await c.send('Input.dispatchMouseEvent',{type:'mouseReleased',x,y,button:'left',clickCount:1});interactions.push({type:'pointer click',label,x,y});}
async function capture(name){const file=prefix+name;await c.evaluate('document.fonts.ready.then(()=>true)');const state=await c.evaluate(`(()=>{const rect=e=>e.getBoundingClientRect().toJSON();return{url:location.href,viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},scrollY,rootClass:document.documentElement.className,font:getComputedStyle(document.body).fontFamily,text:document.body.innerText,inputs:[...document.querySelectorAll('input')].map(e=>({type:e.type,placeholder:e.placeholder,value:e.value,rect:rect(e)})),buttons:[...document.querySelectorAll('button')].filter(e=>rect(e).width>0).map(e=>({text:e.innerText,aria:e.getAttribute('aria-label'),rect:rect(e)}))}})()`);const shot=await c.send('Page.captureScreenshot',{format:'png'}),b=Buffer.from(shot.data,'base64');await fs.writeFile(new URL(file,out),b);states.push({file,sha256:createHash('sha256').update(b).digest('hex'),bytes:b.length,...state});console.log(file);}
try{
 await c.send('Page.enable');
 await c.send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:width<600?3:2,mobile:false});
 await c.send('Page.navigate',{url:'https://jjintern.com/companies'});
 await waitFor('document.body.innerText.includes("Shopee") && /[0-9]+ live roles/.test(document.body.innerText)');
 if(await c.evaluate(`[...document.querySelectorAll('button')].some(e=>e.getAttribute('aria-label')==='Switch to light mode')`)){await click(`[...document.querySelectorAll('button[aria-label="Switch to light mode"]')].find(e=>e.getBoundingClientRect().width>0)?.getBoundingClientRect().toJSON()`,'Switch to light mode');await delay(500);}
 await capture('directory-empty.png');
 await click(`document.querySelector('input[type="search"]').getBoundingClientRect().toJSON()`,'Directory search');
 let query='';
 for(const [i,letter] of [...'Microsoft'].entries()){
   await c.send('Input.insertText',{text:letter});query+=letter;interactions.push({type:'text input',text:letter,query});await delay(350);
   await capture(`directory-${String(i+1).padStart(2,'0')}.png`);
 }
 await waitFor('document.body.innerText.includes("Microsoft") && !document.body.innerText.includes("Shopee")');
 await delay(500);await capture('directory-microsoft.png');
 await c.send('Page.navigate',{url:'https://jjintern.com/feed'});
 await waitFor('document.body.innerText.includes("Set status")');await delay(1200);
 if(prefix){await c.evaluate('window.scrollTo(0,125)');interactions.push({type:'scroll',y:125,purpose:'Move metrics out while original sticky controls and first full result remain'});await delay(500);}
 await capture('feed-all.png');
 await click(`[...document.querySelectorAll('button')].find(e=>e.innerText==='Tech' && e.getBoundingClientRect().width>0)?.getBoundingClientRect().toJSON()`,'Feed Tech category');
 await delay(2000);await waitFor('document.body.innerText.includes("Set status")');await capture('feed-tech.png');
 await click(`[...document.querySelectorAll('button')].find(e=>e.innerText==='Finance' && e.getBoundingClientRect().width>0)?.getBoundingClientRect().toJSON()`,'Feed Finance category');
 await delay(2000);await waitFor('document.body.innerText.includes("Set status")');await capture('feed-finance.png');
 await fs.writeFile(new URL(prefix+'capture-record.json',out),JSON.stringify({checked:'2026-10-20',timezone:'Europe/London',context:'Fresh isolated logged-out Chrome profile. Actual input events, category clicks and theme toggle. No DOM content or styling altered. Editorial timing is not product-speed measurement. Roles and counts are JJIntern displays, not independently verified vacancies. No account, save, status, apply, employer-handoff or Telegram action.',interactions,states},null,2)+'\n');
 await fs.writeFile(new URL(prefix+'manifest.json',out),JSON.stringify({checked:'2026-10-20',files:states.map(({file,sha256,bytes})=>({file,sha256,bytes}))},null,2)+'\n');
}finally{c.close();}
