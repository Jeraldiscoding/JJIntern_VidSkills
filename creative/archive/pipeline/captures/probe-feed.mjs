import fs from 'node:fs/promises';
import {connect} from '../../../scripts/cdp.mjs';
const cdp=await connect(9346),out=new URL('./',import.meta.url);
const wait=ms=>new Promise(r=>setTimeout(r,ms));
try{
 await cdp.send('Page.enable');
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:4,mobile:true});
 await cdp.send('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:'dark'}]});
 await cdp.send('Page.navigate',{url:'https://jjintern.com/feed'});
 await wait(6000);
 await cdp.evaluate('document.fonts.ready.then(()=>true)');
 const data=await cdp.evaluate(`({url:location.href,title:document.title,text:document.body.innerText,inputs:[...document.querySelectorAll('input')].map(e=>({type:e.type,placeholder:e.placeholder,value:e.value,bounds:e.getBoundingClientRect().toJSON()})),links:[...document.querySelectorAll('a[href]')].map(e=>({text:e.innerText,url:e.href,bounds:e.getBoundingClientRect().toJSON()})),tables:[...document.querySelectorAll('table')].map(e=>({text:e.innerText,html:e.outerHTML.slice(0,20000)})),articles:[...document.querySelectorAll('article')].map(e=>({text:e.innerText,html:e.outerHTML.slice(0,5000)}))})`);
 await fs.writeFile(new URL('probe.json',out),JSON.stringify(data,null,2));
 const s=await cdp.send('Page.captureScreenshot',{format:'png'});await fs.writeFile(new URL('feed-probe.png',out),Buffer.from(s.data,'base64'));
 console.log(JSON.stringify(data));
}finally{cdp.close()}
