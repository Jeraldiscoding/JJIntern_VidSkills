/* Original JJIntern approval-stage material study. No earlier campaign scene used.
 * Continuous folded sheet, analytic studio reflections, per-pixel occlusion.
 * Scene time remains a parameter for the eventual native 120 fps renderer.
 */
window.makeStudio = function () {
 const c=document.createElement('canvas');
 const gl=c.getContext('webgl',{alpha:false,antialias:false,preserveDrawingBuffer:true});
 const vs=`attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}`;
 const fs=`precision highp float;
 uniform vec2 size;uniform float clock;uniform float mode;uniform sampler2D page;
 float box(vec3 p,vec3 b,float r){vec3 q=abs(p)-b+r;return length(max(q,0.))+min(max(q.x,max(q.y,q.z)),0.)-r;}
 mat3 ry(float a){float s=sin(a),c=cos(a);return mat3(c,0.,s,0.,1.,0.,-s,0.,c);}
 mat3 rz(float a){float s=sin(a),c=cos(a);return mat3(c,s,0.,-s,c,0.,0.,0.,1.);}
 vec3 local(vec3 p){return ry(-.10)*p;}
 float folded(vec3 p){
   p=local(p);float d=100.;
   float wave=.14*sin(p.x*1.20+.30)+.045*sin(p.z*1.9);
   float opening=.37*pow(smoothstep(-1.6,1.6,p.x),2.);
   for(int i=0;i<3;i++){
    float h=(float(i)-1.)*.19+(i==2?opening:0.);
    vec3 q=p-vec3(0.,h+wave,0.);
    d=min(d,box(q,vec3(1.67,.013,.86),.011));
    if(i<2){
     float side=mod(float(i),2.)<.5?1.:-1.;
     float next=(float(i))*.19+(i==1?opening:0.);
     float radius=(next-h)*.5;
     vec2 yz=p.yz-vec2(h+radius+wave,side*.86);
     float ring=abs(length(yz)-radius)-.012;
     float halfRing=max(ring,-side*yz.y);
     float end=max(halfRing,abs(p.x)-1.655);
     d=min(d,end);
    }
   }
   return d;
 }
 vec3 pageLocal(vec3 p){return rz(.075)*ry(-.16)*p;}
 float paper(vec3 p){
  vec3 q=pageLocal(p);float lift=.68*pow(max((q.x+.2)/1.75,0.),3.)*pow(max((-q.y+.2)/2.4,0.),3.);
  q.z-=lift;return box(q,vec3(1.40,1.92,.016),.016);
 }
 float object(vec3 p){return mode<.5?paper(p):folded(p);}
 float scene(vec3 p){return min(object(p),p.y+.70);}
 vec3 normal(vec3 p){vec2 e=vec2(.0012,0.);return normalize(vec3(object(p+e.xyy)-object(p-e.xyy),object(p+e.yxy)-object(p-e.yxy),object(p+e.yyx)-object(p-e.yyx)));}
 vec3 environment(vec3 r){
  vec3 v=vec3(.032,.035,.043)+vec3(.030,.032,.036)*max(r.y,0.);
  float panel=exp(-pow((r.z-.25)*2.4,8.))*exp(-pow((r.x+.43)*3.6,8.))*smoothstep(.25,.45,r.y);
  v+=vec3(2.7,2.72,2.78)*panel;
  float strip=exp(-pow((r.y-.53)*17.,2.))*exp(-pow((r.x-.25)*1.4,8.));
  v+=vec3(2.5,2.57,2.68)*strip;
  float kick=exp(-pow((r.x-.84)*17.,2.))*exp(-pow((r.z-.1)*2.,4.));
  v+=vec3(.7,.8,.95)*kick;
  float low=exp(-pow((r.y+.20)*8.,2.))*exp(-pow((r.x+.75)*4.,4.));
  v+=vec3(.12,.17,.25)*low;
  return v;
 }
 float shadow(vec3 p,vec3 l){float shade=1.,t=.025;for(int i=0;i<28;i++){float h=object(p+l*t);shade=min(shade,9.*h/t);t+=clamp(h,.025,.18);if(t>4.)break;}return clamp(shade,.0,1.);}
 float ao(vec3 p,vec3 n){float sum=0.,gain=1.;for(int i=1;i<6;i++){float r=.028*float(i);sum+=(r-object(p+n*r))*gain;gain*=.72;}return clamp(1.-sum*3.3,.1,1.);}
 vec3 film(vec3 c){c=(c*(2.51*c+.03))/(c*(2.43*c+.59)+.14);return pow(clamp(c,0.,1.),vec3(1./2.2));}
 void main(){
  vec2 uv=(gl_FragCoord.xy-size*.5)/size.y;
  vec3 ro=mode<.5?vec3(.3,.32,7.6):vec3(3.6,2.85,6.2);
  vec3 target=mode<.5?vec3(0.,0.,0.):vec3(0.,-.04,0.);
  vec3 fw=normalize(target-ro),rt=normalize(cross(fw,vec3(0.,1.,0.))),up=cross(rt,fw);
  float lens=mode<.5?1.10:.91;
  vec3 rd=normalize(fw*lens+rt*uv.x+up*uv.y);
  float t=0.,d=100.;bool hit=false;
  for(int i=0;i<200;i++){vec3 p=ro+rd*t;d=mode<.5?object(p):scene(p);if(d<.0006){hit=true;break;}t+=max(d*.53,.00025);if(t>24.)break;}
  vec3 bg=vec3(.0065,.007,.0085);bg+=vec3(.012)*exp(-dot(uv*vec2(1.2,.85),uv*vec2(1.2,.85))*2.2);
  vec3 col=bg;
  if(hit){
   vec3 p=ro+rd*t;
   if(mode>.5&&p.y< -.698){
    vec3 l=normalize(vec3(-2.,5.,3.));float sh=shadow(p+vec3(0.,.01,0.),l);
    float halo=exp(-pow(p.x/4.,2.)-pow(p.z/4.,2.));
    col=bg+vec3(.006,.0065,.007)*halo*(.2+.8*sh);
   }else{
    vec3 n=normal(p),v=-rd,r=reflect(rd,n);float occ=ao(p,n);
    if(mode<.5){
     vec3 q=pageLocal(p);vec2 tc=vec2((q.x+1.4)/2.8,1.-(q.y+1.92)/3.84);
     vec3 ink=texture2D(page,tc).rgb;
     float lit=.63+.35*max(dot(n,normalize(vec3(-1.,2.,4.))),0.);
     col=pow(ink,vec3(2.2))*lit;
     float edge=1.-smoothstep(.0,.028,min(1.40-abs(q.x),1.92-abs(q.y)));
     col=mix(col,environment(r)*.55,edge*.85);
    }else{
     vec3 q=local(p);float nv=max(dot(n,v),0.);
     float fres=.72+.28*pow(1.-nv,5.);
     vec3 reflectance=(environment(r)*.5+environment(normalize(r+vec3(.027,.008,.012)))*.25+environment(normalize(r-vec3(.027,.008,.012)))*.25);
     vec3 pearl=vec3(.39,.386,.375)*(.40+.56*max(dot(n,normalize(vec3(-.7,2.,1.7))),0.))*occ+reflectance*.18*occ;
     vec3 metal=reflectance*fres*occ+vec3(.065,.067,.070)*max(n.y,0.)*occ;
     col=mix(metal,pearl,smoothstep(.50,.87,n.y));
     float brushed=.987+.013*sin(q.x*790.+sin(q.z*18.));col*=brushed;
     // Etched data strokes live on the top silver fold; blue is a narrow inset.
     float top=smoothstep(.14,.19,q.y-.14*sin(q.x*1.20+.30)-.045*sin(q.z*1.9)-.37*pow(smoothstep(-1.6,1.6,q.x),2.))*smoothstep(.65,.95,n.y);
     float line=1.-smoothstep(.008,.014,abs(q.z+.22));
     float finite=1.-smoothstep(1.10,1.14,abs(q.x+.06));
     col=mix(col,vec3(.002,.020,.070),line*finite*top*.9);
     float trace=(1.-smoothstep(.006,.012,abs(q.z+.22)))*(1.-smoothstep(.94,1.02,abs(q.x+.10)))*top;
     col+=vec3(.001,.075,.36)*trace*1.0;
     float rows=0.;for(int k=0;k<4;k++){float z=.02+float(k)*.105;float len=1.-float(k)*.18;rows=max(rows,(1.-smoothstep(.003,.007,abs(q.z-z)))*(1.-smoothstep(len,len+.04,abs(q.x+.16))));}
     col*=1.-rows*top*.30;
     float rim=pow(1.-nv,4.);col+=vec3(.04,.045,.055)*rim;
    }
   }
  }
  gl_FragColor=vec4(film(col),1.);
 }`;
 function shader(type,src){const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}
 const p=gl.createProgram();gl.attachShader(p,shader(gl.VERTEX_SHADER,vs));gl.attachShader(p,shader(gl.FRAGMENT_SHADER,fs));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));gl.useProgram(p);
 const b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);const a=gl.getAttribLocation(p,'a');gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,2,gl.FLOAT,false,0,0);
 const u={};for(const k of ['size','clock','mode','page'])u[k]=gl.getUniformLocation(p,k);
 const tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tex);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
 return {canvas:c,render(mode,page,w,h,t=0){c.width=w;c.height=h;gl.viewport(0,0,w,h);gl.useProgram(p);gl.bindTexture(gl.TEXTURE_2D,tex);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,page);gl.uniform1i(u.page,0);gl.uniform2f(u.size,w,h);gl.uniform1f(u.mode,mode);gl.uniform1f(u.clock,t);gl.drawArrays(gl.TRIANGLES,0,6);return c;}};
};
