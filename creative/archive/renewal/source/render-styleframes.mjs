import fs from 'node:fs/promises';
import {connect} from '../../../scripts/cdp.mjs';
const cdp=await connect(process.argv[2]||'9350');
const base=new URL('../',import.meta.url);
let html=await fs.readFile(new URL('styleframes.html',import.meta.url),'utf8');
html=html.replace('/* STUDIO */',await fs.readFile(new URL('studio.js',import.meta.url),'utf8'));
for(const [key,path] of [['FEED_IMAGE','../../pipeline/captures/feed-loaded.png'],['LOGO_IMAGE','../../../assets/evidence/product/logo-mark.png']]){
 const data=await fs.readFile(new URL(path,import.meta.url));html=html.replace(key,`data:image/png;base64,${data.toString('base64')}`);
}
try{
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:1080,height:1920,deviceScaleFactor:1,mobile:false});
 await cdp.send('Page.navigate',{url:`data:text/html;base64,${Buffer.from(html).toString('base64')}`});
 let started=false;for(let i=0;i<60;i++){if(await cdp.evaluate('typeof window.ready!=="undefined"')){started=true;break;}await new Promise(r=>setTimeout(r,100));}
 if(!started)throw Error('Scene did not initialise');
 console.log(await cdp.evaluate('window.ready'));
 for(let i=1;i<=3;i++){const data=await cdp.evaluate(`drawFrame(${i})`);await fs.writeFile(new URL(`styleframes/0${i}-${['posting','packet','feed'][i-1]}.png`,base),Buffer.from(data,'base64'));console.log('Exported frame '+i);}
 const sheet=await cdp.evaluate(`(()=>{const out=document.createElement('canvas');out.width=1620;out.height=960;const x=out.getContext('2d');for(let i=1;i<=3;i++){drawFrame(i);x.drawImage(canvas,(i-1)*540,0,540,960);}return out.toDataURL().split(',')[1];})()`);
 await fs.writeFile(new URL('styleframes/approval-board.png',base),Buffer.from(sheet,'base64'));
 console.log(await cdp.send('Browser.getVersion'));
}finally{cdp.close();}
