/* Silver laminae -> one thin data envelope. No text or fabricated UI.
 * CompactObject.render(t,{morph,angleX,angleY,angleZ,width,height}) -> transparent canvas.
 * morph 0: three curved sheets; morph 1: one slim envelope. Rotation radians.
 */
(function(){
 'use strict';
 const canvas=document.createElement('canvas');
 const gl=canvas.getContext('webgl',{alpha:true,premultipliedAlpha:false,preserveDrawingBuffer:true,antialias:false});
 if(!gl)throw Error('CompactObject requires WebGL');
 const vs='attribute vec2 position;void main(){gl_Position=vec4(position,0.,1.);}';
 const fs=`precision highp float;
 uniform vec2 resolution;uniform vec3 rotation;uniform float morph;
 uniform sampler2D postingTexture;uniform float hasTexture;
 mat3 orientation;
 mat3 rx(float a){float c=cos(a),s=sin(a);return mat3(1.,0.,0.,0.,c,s,0.,-s,c);}
 mat3 ry(float a){float c=cos(a),s=sin(a);return mat3(c,0.,-s,0.,1.,0.,s,0.,c);}
 mat3 rz(float a){float c=cos(a),s=sin(a);return mat3(c,s,0.,-s,c,0.,0.,0.,1.);}
 float sheet(vec3 p,vec2 b,float h){
  vec2 q=abs(p.xy)-b+vec2(.09);
  float d=length(max(q,0.))+min(max(q.x,q.y),0.)-.09;
  vec2 w=vec2(d,abs(p.z)-h);
  return min(max(w.x,w.y),0.)+length(max(w,0.))-.009;
 }
 float shape(vec3 world){
  vec3 p=orientation*world;float d=100.;
  for(int i=0;i<3;i++){
   float layer=float(i)-1.;vec3 q=p;
   q.x-=layer*.19*(1.-morph);q.y-=layer*.10*(1.-morph);
   q.z-=layer*.19*(1.-morph);
   q.z-=(1.-morph)*.13*sin(q.x*1.20+layer*.65)*cos(q.y*.50);
   d=min(d,sheet(q,vec2(1.57,mix(.942,.58,morph)),mix(.013,.036,morph)));
  }
  return d;
 }
 vec3 normalAt(vec3 p){vec2 e=vec2(.001,0.);return normalize(vec3(
  shape(p+e.xyy)-shape(p-e.xyy),shape(p+e.yxy)-shape(p-e.yxy),shape(p+e.yyx)-shape(p-e.yyx)));}
 vec3 env(vec3 r){
  vec3 c=vec3(.045,.055,.07);
  c+=vec3(.8,.84,.9)*pow(max(r.y*.5+.5,0.),2.);
  float window=exp(-pow((r.x+.42)/.48,4.))*exp(-pow((r.y-.38)/.55,4.));
  c+=vec3(1.55,1.60,1.65)*window;
  float strip=exp(-pow((r.y-.68)*22.,2.));c+=vec3(1.3)*strip;
  float blackFlag=exp(-pow((r.x-.30)/.23,4.));c*=1.-blackFlag*.76;
  return c;
 }
 void main(){
  orientation=rx(-rotation.x)*ry(-rotation.y)*rz(-rotation.z);
  vec2 uv=(gl_FragCoord.xy-resolution*.5)/resolution.y;
  vec3 ro=vec3(0.,0.,5.8),rd=normalize(vec3(uv*3.6,-5.8));
  float z=0.;bool hit=false;
  for(int i=0;i<110;i++){float d=shape(ro+rd*z);if(d<.00055){hit=true;break;}z+=d*.73;if(z>10.)break;}
  if(!hit){gl_FragColor=vec4(0.);return;}
  vec3 p=ro+rd*z,q=orientation*p,n=normalAt(p),v=normalize(ro-p);
  vec3 localN=orientation*n;
  float face=smoothstep(.40,.96,abs(localN.z));
  vec3 bent=vec3(q.x*.008,q.y*.014,0.);
  n=normalize(n+vec3(dot(orientation[0],bent),dot(orientation[1],bent),dot(orientation[2],bent))*face);
  vec3 r=reflect(-v,n);float nv=max(dot(n,v),0.);
  float key=max(dot(n,normalize(vec3(-.5,1.2,2.))),0.);
  float rim=pow(1.-nv,3.);
  vec3 base=mix(vec3(.12,.14,.17),vec3(.72,.74,.77),face);
  vec3 col=base*(.19+.49*key);
  col+=env(r)*mix(.47,.21,face);
  col+=vec3(.8,.86,.95)*rim*.34;
  // Silver is defined by the studio's bright window and dark flag, rather
  // than a flat grey diffuse fill. The reflected window follows the view.
  vec3 lv=orientation*v;
  float sweep=q.x*.77+q.y*.42+lv.x*.27-lv.y*.20;
  float softWindow=exp(-pow((sweep+.54)/.50,4.));
  float darkFlag=exp(-pow((sweep-.65)/.53,4.));
  vec3 reflectedStudio=vec3(.16,.18,.21)+vec3(.95,.98,1.)*softWindow-vec3(.12)*darkFlag;
  col=mix(col,reflectedStudio,face*mix(.24,.88,morph));
  // The blue lives only on one fine perimeter seam, not on the solid body.
  float edge=min(1.57-abs(q.x),mix(.942,.58,morph)-abs(q.y));
  float seam=exp(-pow((edge-.035)/.014,2.));
  col=mix(col,vec3(.004,.20,.62),seam*morph*.72*face);
  // Soft directional reflection across the satin clear coat.
  float band=exp(-pow((q.y+.22*q.x+.10)/.27,2.));
  col+=vec3(.16,.17,.18)*band*face;
  col=col/(col+vec3(.65));col=pow(clamp(col,0.,1.),vec3(1./2.2));
  vec2 faceXY=q.xy-vec2(.19,.10)*(1.-morph);
  vec2 texUV=faceXY/vec2(3.14,1.884)+.5;
  float inside=step(0.,texUV.x)*step(texUV.x,1.)*step(0.,texUV.y)*step(texUV.y,1.);
  float exposed=(1.-smoothstep(.12,.73,morph))*smoothstep(.60,.97,localN.z)*inside*hasTexture;
  vec3 tex=texture2D(postingTexture,clamp(texUV,0.,1.)).rgb;
  col=mix(col,tex*(.83+.13*key)+vec3(.018)*band,exposed);
  gl_FragColor=vec4(col,1.);
 }`;
 function shader(type,src){const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}
 const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vs));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fs));gl.linkProgram(program);
 if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
 gl.useProgram(program);const b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
 const a=gl.getAttribLocation(program,'position');gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,2,gl.FLOAT,false,0,0);
 const u={};for(const k of ['resolution','rotation','morph','hasTexture','postingTexture'])u[k]=gl.getUniformLocation(program,k);
 const texture=gl.createTexture();gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,texture);
 gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
 gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
 gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array([255,255,255,255]));let textured=false;
 window.CompactObject={canvas,setTexture(source){gl.bindTexture(gl.TEXTURE_2D,texture);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,source);textured=true;},render(t,o={}){
  const w=o.width||1080,h=o.height||800;if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
  gl.viewport(0,0,w,h);gl.useProgram(program);gl.uniform2f(u.resolution,w,h);gl.uniform3f(u.rotation,o.angleX??.38,o.angleY??-.28,o.angleZ??-.055);gl.uniform1f(u.morph,Math.max(0,Math.min(1,o.fold??o.morph??0)));gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,texture);gl.uniform1i(u.postingTexture,0);gl.uniform1f(u.hasTexture,textured?1:0);
  gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.drawArrays(gl.TRIANGLES,0,6);return canvas;
 }};
})();
