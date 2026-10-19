import fs from 'node:fs/promises';
import {connect} from '../../../scripts/cdp.mjs';
const cdp=await connect(9346),out=new URL('./',import.meta.url),wait=ms=>new Promise(r=>setTimeout(r,ms));
try{
 const before=await(await fetch('http://127.0.0.1:9346/json/list')).json();
 const bounds=await cdp.evaluate(`(()=>{const e=[...document.querySelectorAll('button')].find(e=>e.innerText==='Open application →');e.scrollIntoView({block:'center'});return e.getBoundingClientRect().toJSON()})()`);
 await cdp.send('Input.dispatchMouseEvent',{type:'mousePressed',x:bounds.x+bounds.width/2,y:bounds.y+bounds.height/2,button:'left',clickCount:1});
 await cdp.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:bounds.x+bounds.width/2,y:bounds.y+bounds.height/2,button:'left',clickCount:1});
 await wait(3500);
 const after=await(await fetch('http://127.0.0.1:9346/json/list')).json();
 const data={checked:'2026-10-17',captured_at_utc:new Date().toISOString(),action:'Actual read-only Open application click on Microsoft Research Intern; no application submission',before:before.map(({id,type,title,url})=>({id,type,title,url})),after:after.map(({id,type,title,url})=>({id,type,title,url})),samePage:await cdp.evaluate('({url:location.href,text:document.body.innerText})')};
 await fs.writeFile(new URL('source-handoff.json',out),JSON.stringify(data,null,2));console.log(JSON.stringify(data,null,2));
}finally{cdp.close()}
