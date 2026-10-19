import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {connect} from '../../../scripts/cdp.mjs';
const out=new URL('./',import.meta.url);
const record=JSON.parse(await fs.readFile(new URL('capture-record.json',out),'utf8'));
const handoff=JSON.parse(await fs.readFile(new URL('source-handoff.json',out),'utf8'));
handoff.action='Actual Open application click on Microsoft Research Intern opened the generic employer portal; isolated JJIntern UI subsequently displayed Applied. No application or form was submitted.';
handoff.before=handoff.before.filter(p=>p.type==='page');handoff.after=handoff.after.filter(p=>p.type==='page');
handoff.limit='Generic employer destination does not confirm a role-specific current vacancy. Clean feed/search screenshots predate the Applied UI side effect.';
await fs.writeFile(new URL('source-handoff.json',out),JSON.stringify(handoff,null,2));
const crops={checked:'2026-10-17',source_png_dimensions:[1560,3376],device_scale_factor:4,crops:[{file:'feed-microsoft-focus.png',source:'feed-microsoft.png',rect:{x:32,y:600,width:1496,height:1020},scope:'Actual query, controls and first role row; historical date visible; aggregate header counts excluded.'},{file:'feed-microsoft-role.png',source:'feed-microsoft.png',rect:{x:32,y:1140,width:1000,height:300},scope:'Actual company logo/name and Research Intern title; editorial detail, requires Example posting context.'}],transform:'Lossless rectangular crop of genuine source pixels; no reconstructed interface or retyped product content.'};
await fs.writeFile(new URL('crop-manifest.json',out),JSON.stringify(crops,null,2));
const files=[];for(const name of (await fs.readdir(out)).sort()){if(name==='manifest.json')continue;const b=await fs.readFile(new URL(name,out));files.push({path:name,sha256:createHash('sha256').update(b).digest('hex'),bytes:b.length});}
await fs.writeFile(new URL('manifest.json',out),JSON.stringify({checked:'2026-10-17',captured_at_utc:record.captured_at_utc,timezone:'Europe/Stockholm',source:record.source,viewport:record.viewport,session:record.session,verified:'Loaded public feed and actual Microsoft query returning a Microsoft Research Intern row, plus Synapxe role with Microsoft in its title.',limit:'Microsoft display date 1 Sept; generic employer portal; no verified current vacancy, scrape interval or ingest latency. See capture-note.txt for isolated UI Applied side effect.',files},null,2));
console.log(JSON.stringify({status:'ready',files:files.length,source:'feed-microsoft.png',role:'Microsoft — Research Intern',date:'1 Sept',sourceURL:'https://apply.careers.microsoft.com/careers'}));
const cdp=await connect(9346);try{await cdp.send('Browser.close')}catch(e){console.log('Browser close connection ended:',e.message)}finally{cdp.close()}
