import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {connect} from '../../../scripts/cdp.mjs';
const port=process.argv[2]||'9354';
const base=new URL('../',import.meta.url);
let html=await fs.readFile(new URL('styleframes.html',import.meta.url),'utf8');
html=html.replace('/* STUDIO */',await fs.readFile(new URL('studio.js',import.meta.url),'utf8'));
const inputs={MICROSOFT_IMAGE:'../captures/microsoft-internship-programmes-540.png',FEED_IMAGE:'../../pipeline/captures/feed-loaded.png'};
const manifest={stage:'styleframes awaiting approval',date:'2026-10-17',size:[1080,1920],actual_deliverable:'three still approval frames; no video or audio',supersampling:[2160,3840],crops:{microsoft:[0,110,1620,1490],feed:[0,0,1560,2268]},review_notes:'review/final-stills-qa.md',direction:'direction.md',flight:{start:4.5,end:6.5,seconds:2,confirmed_by_user:true,native_frames:[540,779],arrival_frame:780},inputs:{},outputs:[]};
for(const [key,path] of Object.entries(inputs)){const b=await fs.readFile(new URL(path,import.meta.url));html=html.replace(key,`data:image/png;base64,${b.toString('base64')}`);manifest.inputs[key]={path,sha256:crypto.createHash('sha256').update(b).digest('hex')};}
const cdp=await connect(port);
try{
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:1080,height:1920,deviceScaleFactor:1,mobile:false});
 const preview=new URL('preview-bundled.html',import.meta.url);await fs.writeFile(preview,html);
 const navigation=await cdp.send('Page.navigate',{url:preview.href});if(navigation.errorText)throw Error(navigation.errorText);
 let initialized=false;for(let i=0;i<100;i++){if(await cdp.evaluate('typeof window.ready!=="undefined"')){initialized=true;break;}await new Promise(r=>setTimeout(r,100));}if(!initialized)throw Error('Scene did not initialize');
 manifest.scene=await cdp.evaluate('window.ready');console.log(manifest.scene);
 for(const [i,name] of ['01-browser','02-speed','03-feed'].entries()){const result=await cdp.evaluate(`drawFrame(${i+1})`);const b=Buffer.from(result,'base64'),path=`styleframes/${name}.png`;await fs.writeFile(new URL(path,base),b);manifest.outputs.push({path,sha256:crypto.createHash('sha256').update(b).digest('hex')});console.log('Saved '+path);}
 await fs.writeFile(new URL('styleframes/approval-board.png',base),Buffer.from(await cdp.evaluate('makeBoard()'),'base64'));
 manifest.browser=await cdp.send('Browser.getVersion');await fs.writeFile(new URL('styleframe-manifest.json',base),JSON.stringify(manifest,null,2)+'\n');
}finally{cdp.close();}
