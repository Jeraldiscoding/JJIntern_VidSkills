import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {connect} from '../../../scripts/cdp.mjs';
const cdp=await connect(9346),out=new URL('./',import.meta.url),states=[];
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const inspect=`(()=>{const rect=e=>e.getBoundingClientRect().toJSON();return{url:location.href,title:document.title,text:document.body.innerText,query:document.querySelector('input[placeholder="Search company or role"]')?.value,inputs:[...document.querySelectorAll('input')].map(e=>({type:e.type,placeholder:e.placeholder,value:e.value,bounds:rect(e)})),buttons:[...document.querySelectorAll('button')].map(e=>({text:e.innerText,aria:e.getAttribute('aria-label'),bounds:rect(e),html:e.outerHTML.slice(0,6000)})),links:[...document.querySelectorAll('a[href]')].map(e=>({text:e.innerText,url:e.href,bounds:rect(e)})),style:{background:getComputedStyle(document.body).backgroundColor,font:getComputedStyle(document.body).fontFamily,stylesheets:[...document.styleSheets].map(s=>s.href)}}})()`;
async function capture(file){
 const state=await cdp.evaluate(inspect),shot=await cdp.send('Page.captureScreenshot',{format:'png'});
 await fs.writeFile(new URL(file,out),Buffer.from(shot.data,'base64'));states.push({file,...state});return state;
}
try{
 await cdp.send('Page.enable');
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:4,mobile:true});
 if(!(await cdp.evaluate('location.href === "https://jjintern.com/feed"')))throw Error('Expected isolated public feed already navigated by probe.');
 for(let i=0;i<60;i++){
  const text=await cdp.evaluate('document.body.innerText');
  if(text.includes('ByteDance')&&text.includes('Set status'))break;
  if(i%15===0)console.log('Waiting for loaded public role rows',i);
  await wait(1000);
 }
 if(!(await cdp.evaluate('document.body.innerText.includes("ByteDance")')))throw Error('No loaded role rows; capture cannot demonstrate populated feed.');
 await capture('feed-loaded.png');
 const rect=await cdp.evaluate(`document.querySelector('input[placeholder="Search company or role"]').getBoundingClientRect().toJSON()`);
 await cdp.send('Input.dispatchMouseEvent',{type:'mousePressed',x:rect.x+70,y:rect.y+18,button:'left',clickCount:1});
 await cdp.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:rect.x+70,y:rect.y+18,button:'left',clickCount:1});
 let query='';
 for(const [i,letter] of [...'Microsoft'].entries()){
  await cdp.send('Input.insertText',{text:letter});query+=letter;await wait(350);
  const state=await capture(`feed-search-${String(i+1).padStart(2,'0')}.png`);
  if(state.query!==query)throw Error('Captured query differs from actual expected input.');
 }
 await wait(1500);
 const final=await capture('feed-microsoft.png');
 await fs.writeFile(new URL('filtered-dom.html',out),await cdp.evaluate('document.documentElement.outerHTML'));
 const record={checked:'2026-10-17',captured_at_utc:new Date().toISOString(),timezone:'Europe/Stockholm',source:'https://jjintern.com/feed',viewport:{css_width:390,css_height:844,device_scale_factor:4,png_width:1560,png_height:3376},session:{logged_in:false,isolated_profile:true,cdp_port:9346},context:'Genuine public feed captures and actual Input.insertText events. Edited timing is not product latency. Site displays are not employer-confirmed vacancy evidence.',states};
 await fs.writeFile(new URL('capture-record.json',out),JSON.stringify(record,null,2));
 const files=[];for(const name of ['capture-record.json','filtered-dom.html',...states.map(s=>s.file)]){const b=await fs.readFile(new URL(name,out));files.push({path:name,sha256:createHash('sha256').update(b).digest('hex'),bytes:b.length});}
 await fs.writeFile(new URL('manifest.json',out),JSON.stringify({...record,states:undefined,files},null,2));
 console.log(JSON.stringify({status:'captured',query:final.query,text:final.text,buttons:final.buttons,links:final.links},null,2));
}finally{cdp.close()}
