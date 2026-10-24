import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {connect} from '../../../scripts/cdp.mjs';

const root=new URL('../',import.meta.url), out=new URL('evidence/',root);
const c=await connect(process.argv[2]||9384);
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const click=async r=>{for(const type of ['mousePressed','mouseReleased'])await c.send('Input.dispatchMouseEvent',{type,x:r.x+r.width/2,y:r.y+r.height/2,button:'left',clickCount:1})};
const record={checked:'2026-10-24',timezone:'Europe/Stockholm',context:'Isolated logged-out Chrome, real input and clicks; no application submitted',states:[]};
async function save(name,clip){
  const s=await c.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,...(clip?{clip:{...clip,scale:1}}:{})});
  const b=Buffer.from(s.data,'base64');await fs.writeFile(new URL(name,out),b);
  record.states.push({file:name,sha256:createHash('sha256').update(b).digest('hex'),...(clip?{crop_css_pixels:clip}:{}),...await c.evaluate('({url:location.href,text:document.body.innerText,viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio}})')});
}
try{
  await fs.mkdir(out,{recursive:true});await c.send('Page.enable');
  await c.send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:3,mobile:false});
  await c.send('Page.navigate',{url:'https://jjintern.com/feed'});
  for(let i=0;i<30;i++){if(await c.evaluate(`!!document.querySelector('input[placeholder="Search company or role"]')`))break;await pause(300)}
  await pause(2500);
  const theme=await c.evaluate(`(()=>{const e=[...document.querySelectorAll('button[aria-label="Switch to light mode"]')].find(b=>b.getBoundingClientRect().width);return e?e.getBoundingClientRect().toJSON():null})()`);
  if(theme)await click(theme);await pause(250);
  const input=await c.evaluate(`document.querySelector('input[placeholder="Search company or role"]').getBoundingClientRect().toJSON()`);
  await click(input);await c.send('Input.insertText',{text:'Google'});await pause(1000);
  await save('01-google-search.png');
  const title='Software Engineering Intern, 2027 (English)';
  const find=`[...document.querySelectorAll('button')].find(b=>b.innerText===${JSON.stringify(title)}&&b.getBoundingClientRect().width>0)`;
  const row=await c.evaluate(`(()=>{const e=${find};if(!e)throw Error('Missing Google internship');e.scrollIntoView({block:'center'});return true})()`);await pause(250);
  const crop=await c.evaluate(`(()=>{const r=(${find}).parentElement.getBoundingClientRect();return {x:r.x,y:r.y+scrollY,width:r.width,height:r.height}})()`);
  await save('02-google-role-crop.png',crop);
  const btn=await c.evaluate(`(${find}).getBoundingClientRect().toJSON()`);await click(btn);await pause(800);
  await save('03-google-details.png');
  record.details=await c.evaluate(`({links:[...document.querySelectorAll('a')].map(a=>({text:a.innerText,url:a.href})),buttons:[...document.querySelectorAll('button')].filter(b=>b.getBoundingClientRect().width>0).map(b=>({text:b.innerText,aria:b.getAttribute('aria-label')}))})`);
  console.log(JSON.stringify({states:record.states.map(s=>({file:s.file,text:s.text})),details:record.details}));
  await fs.writeFile(new URL('capture-record.json',out),JSON.stringify(record,null,2)+'\n');
}finally{c.close()}
