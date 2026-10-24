import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {connect} from '../../../scripts/cdp.mjs';
const root=new URL('../',import.meta.url), images=new URL('images/',root),review=new URL('review/',root);
const hash=b=>createHash('sha256').update(b).digest('hex');
const assets={logo:new URL('../../../assets/evidence/product/logo-mark.png',import.meta.url),role:new URL('evidence/02-google-role-crop.png',root)};
const data={},provenance=[];
for(const [name,url]of Object.entries(assets)){const b=await fs.readFile(url);data[name]='data:image/png;base64,'+b.toString('base64');provenance.push({name,path:url.pathname,sha256:hash(b)})}
const html=await fs.readFile(new URL('carousel.html',import.meta.url),'utf8');
const preview=new URL('preview.html',import.meta.url);await fs.writeFile(preview,html.replace('ASSET_DATA',JSON.stringify(data)));
await fs.mkdir(images,{recursive:true});await fs.mkdir(review,{recursive:true});
const names=['01-cover.png','02-application-window.png','03-fit-check.png','04-visit-jjintern.png'];
const c=await connect(process.argv[2]||9384),manifest={checked:'2026-10-24',dimensions:[1080,1350],format:'PNG; sRGB Chrome rendering; manual-swipe carousel',source_sha256:hash(Buffer.from(html)),assets:provenance,outputs:[],review:{checks:[],pending:['physical phone','actual platform upload preview']}};
try{
 await c.send('Page.enable');await c.send('Emulation.setDeviceMetricsOverride',{width:1080,height:1350,deviceScaleFactor:1,mobile:false});
 await c.send('Page.navigate',{url:preview.href});
 for(let i=0;i<30;i++){if(await c.evaluate('typeof window.ready!=="undefined"'))break;await new Promise(r=>setTimeout(r,100))}
 await c.evaluate('window.ready');
 for(let i=0;i<names.length;i++){
  await c.evaluate(`showSlide(${i})`);
  const content=await c.evaluate(`(()=>{const s=document.querySelector('.slide.active');return {text:s.innerText,overflow:[...s.querySelectorAll('*')].filter(e=>{const r=e.getBoundingClientRect();return r.right>1080.5||r.bottom>1350.5||r.left<-.5||r.top<-.5}).map(e=>({tag:e.tagName,text:e.innerText,rect:e.getBoundingClientRect().toJSON()})),font:getComputedStyle(s).fontFamily}})()`);
  if(content.overflow.length)throw Error(JSON.stringify(content.overflow));
  const shot=await c.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:1080,height:1350,scale:1}});
  const b=Buffer.from(shot.data,'base64');await fs.writeFile(new URL(names[i],images),b);
  manifest.outputs.push({file:names[i],sha256:hash(b),bytes:b.length,...content});
 }
 const imageData=await Promise.all(names.map(async n=>'data:image/png;base64,'+(await fs.readFile(new URL(n,images))).toString('base64')));
 const contact=await c.evaluate(`(async()=>{const a=${JSON.stringify(imageData)};const can=document.createElement('canvas');can.width=720;can.height=900;const ctx=can.getContext('2d');for(let i=0;i<a.length;i++){const im=new Image;im.src=a[i];await im.decode();ctx.drawImage(im,(i%2)*360,Math.floor(i/2)*450,360,450)}return can.toDataURL('image/png').split(',')[1]})()`);
 await fs.writeFile(new URL('contact-sheet.png',review),Buffer.from(contact,'base64'));
 manifest.browser=await c.send('Browser.getVersion');manifest.review.checks.push('All authored element bounds remain within 1080×1350 canvas; fonts and images loaded before capture','Four PNG files rendered and hashed; 360px-per-panel contact sheet created');
 await fs.writeFile(new URL('render-manifest.json',review),JSON.stringify(manifest,null,2)+'\n');console.log(JSON.stringify({outputs:manifest.outputs.map(o=>({file:o.file,bytes:o.bytes})),contactSheet:new URL('contact-sheet.png',review).pathname}));
}finally{c.close()}
