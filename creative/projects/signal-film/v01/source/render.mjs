import fs from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {once} from 'node:events';
import {promisify} from 'node:util';
import {createHash} from 'node:crypto';
import {connect} from '../../../../scripts/cdp.mjs';
const run=promisify(execFile),root=new URL('../',import.meta.url),project=new URL('../../',import.meta.url);
const [port='9372',mode='stills',format='wide']=process.argv.slice(2),vertical=format==='vertical';
const assets={logo:new URL('../../../../assets/evidence/product/logo-mark.png',import.meta.url)};
for(const name of ['portrait-feed-finance','portrait-feed-tech','portrait-directory-empty','portrait-directory-microsoft',...Array.from({length:9},(_,i)=>`portrait-directory-${String(i+1).padStart(2,'0')}`)])assets[name]=new URL(`captures/${name}.png`,project);
const data={},hashes={};for(const [name,url]of Object.entries(assets)){const b=await fs.readFile(url);data[name]='data:image/png;base64,'+b.toString('base64');hashes[name]={path:url.pathname,sha256:createHash('sha256').update(b).digest('hex')}}
const source=await fs.readFile(new URL('motion.html',import.meta.url),'utf8'),html=source.replace('ASSET_DATA',JSON.stringify(data));
const preview=new URL('preview.html',import.meta.url);await fs.writeFile(preview,html);
const cdp=await connect(port);let enc;
try{
await cdp.send('Page.navigate',{url:preview.href});
for(let i=0;i<100;i++){if(await cdp.evaluate('typeof window.ready!=="undefined"'))break;await new Promise(r=>setTimeout(r,100))}
const meta=await cdp.evaluate('window.ready');const size=await cdp.evaluate(`setFormat(${JSON.stringify(format)})`);console.log(JSON.stringify({meta,size}));
const frame=async(t,w,kind='png')=>Buffer.from(await cdp.evaluate(`frameData(${t},${w},${JSON.stringify(kind)})`),'base64');
if(mode==='stills'){
 const times=[.8,2.4,3.7,4.3,5.7,7.6,8.75,10.6,12.6,13.35,15.8,17.8,18.7,20.5,21.75,22.5,24.6,27.1,28.5,30.6];
 for(const t of times)await fs.writeFile(new URL(`stills/${format}-${t.toFixed(2)}.png`,root),await frame(t,vertical?1080:1920));
 for(let p=0;p<4;p++){const ts=times.slice(p*5,p*5+5);const cw=vertical?270:480,ch=vertical?480:270;const b=await cdp.evaluate(`(()=>{const s=document.createElement('canvas');s.width=${cw*5};s.height=${ch+36};const c=s.getContext('2d');c.fillStyle='#203145';c.fillRect(0,0,s.width,s.height);${JSON.stringify(ts)}.forEach((t,i)=>{drawScene(t);c.drawImage(canvas,i*${cw},0,${cw},${ch});c.fillStyle='#fff';c.font='18px -apple-system';c.fillText(t.toFixed(2)+'s',i*${cw}+12,${ch+26})});return s.toDataURL().split(',')[1]})()`);await fs.writeFile(new URL(`review/${format}-board-${p+1}.png`,root),Buffer.from(b,'base64'))}
}else{
 const rough=mode==='rough',fps=rough?30:60,width=rough?(vertical?540:960):(vertical?1080:1920),count=32*fps;
 const target=new URL(`JJIntern-Find-your-focus-${format}${rough?'-rough':''}.mp4`,root),score=new URL('audio/jjintern-find-your-focus-original-score.wav',root);
 const args=['-hide_banner','-loglevel','error','-y','-f','image2pipe','-framerate',String(fps),'-vcodec','mjpeg','-i','pipe:0','-i',score.pathname,'-map','0:v:0','-map','1:a:0','-vf','scale=in_range=full:out_range=limited:out_color_matrix=bt709,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709,setsar=1','-c:v','libx264','-preset',rough?'veryfast':'medium','-crf',rough?'19':'16','-pix_fmt','yuv420p','-r',String(fps),'-fps_mode','cfr','-profile:v','high','-level:v','4.2','-c:a','aac','-b:a','320k','-ar','48000','-movflags','+faststart','-t','32',target.pathname];
 enc=spawn('ffmpeg',args,{stdio:['pipe','inherit','inherit']});let error;enc.on('error',e=>error=e);enc.stdin.on('error',e=>error=e);const done=once(enc,'close'),started=Date.now();
 for(let i=0;i<count;i++){if(error)throw error;const b=await frame(i/fps,width,'jpeg');if(!enc.stdin.write(b))await once(enc.stdin,'drain');if(i%120===0)console.log(`${format} ${i}/${count} frames, ${((Date.now()-started)/1000).toFixed(1)}s`)}enc.stdin.end();const [code]=await done;if(code)throw Error('FFmpeg exit '+code);
 const b=await fs.readFile(target),media=JSON.parse((await run('ffprobe',['-v','error','-show_streams','-show_format','-of','json',target.pathname])).stdout);
 await fs.writeFile(new URL(`review/${format}${rough?'-rough':''}-manifest.json`,root),JSON.stringify({format,mode,duration:32,fps,frames:count,width,height:width*size.height/size.width,sourceSha256:createHash('sha256').update(source).digest('hex'),assets:hashes,output:{path:target.pathname,bytes:b.length,sha256:createHash('sha256').update(b).digest('hex')},media,browser:await cdp.send('Browser.getVersion'),renderSeconds:(Date.now()-started)/1000,command:args},null,2));console.log('Complete '+target.pathname)
}
}finally{cdp.close()}
