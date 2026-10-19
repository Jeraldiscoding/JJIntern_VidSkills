import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {connect} from '../../../scripts/cdp.mjs';
const cdp=await connect(9346),out=new URL('./',import.meta.url);
const wait=ms=>new Promise(r=>setTimeout(r,ms));
try{
 const bounds=await cdp.evaluate(`(()=>{const e=[...document.querySelectorAll('button[aria-label="View details"]')].find(e=>e.getBoundingClientRect().width>0);return e.getBoundingClientRect().toJSON()})()`);
 await cdp.send('Input.dispatchMouseEvent',{type:'mousePressed',x:bounds.x+bounds.width/2,y:bounds.y+bounds.height/2,button:'left',clickCount:1});
 await cdp.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:bounds.x+bounds.width/2,y:bounds.y+bounds.height/2,button:'left',clickCount:1});
 await wait(1300);
 const data=await cdp.evaluate(`(()=>{const rect=e=>e.getBoundingClientRect().toJSON();const e=[...document.querySelectorAll('button[title="Research Intern"]')].find(e=>rect(e).width>0);let p=e;const ancestors=[];for(let i=0;p&&i<5;i++,p=p.parentElement)ancestors.push({tag:p.tagName,cls:p.className,bounds:rect(p),text:p.innerText,html:p.outerHTML.slice(0,18000)});return{url:location.href,text:document.body.innerText,links:[...document.querySelectorAll('a[href]')].map(e=>({text:e.innerText,url:e.href,bounds:rect(e)})),ancestors}})()`);
 const s=await cdp.send('Page.captureScreenshot',{format:'png'});await fs.writeFile(new URL('feed-microsoft-details.png',out),Buffer.from(s.data,'base64'));
 await fs.writeFile(new URL('details-record.json',out),JSON.stringify({checked:'2026-10-17',captured_at_utc:new Date().toISOString(),source:'https://jjintern.com/feed',action:'Actual read-only click on first visible View details control for Microsoft Research Intern',...data},null,2));
 await fs.writeFile(new URL('details-dom.html',out),await cdp.evaluate('document.documentElement.outerHTML'));
 const manifest=JSON.parse(await fs.readFile(new URL('manifest.json',out),'utf8'));
 for(const name of ['feed-microsoft-details.png','details-record.json','details-dom.html']){const b=await fs.readFile(new URL(name,out));manifest.files.push({path:name,sha256:createHash('sha256').update(b).digest('hex'),bytes:b.length});}
 await fs.writeFile(new URL('manifest.json',out),JSON.stringify(manifest,null,2));
 console.log(JSON.stringify({text:data.text,links:data.links,ancestors:data.ancestors.map(({html,...a})=>a)},null,2));
}finally{cdp.close()}
