/* Original rectangle revision. Analytic geometry and studio lighting, no reused
 * film frames, third-party rendering code, generated bitmap, or video assets.
 * Static approval studies only; this is not the eventual animation renderer. */
window.createRectangleStudio = function () {
  const canvas = document.createElement('canvas');
  const gl = canvas.getContext('webgl', {alpha:false, antialias:false, preserveDrawingBuffer:true});
  if (!gl) throw Error('WebGL unavailable');
  const vert = 'attribute vec2 position; void main(){gl_Position=vec4(position,0.,1.);}';
  const frag = `precision highp float;
  uniform vec2 resolution;
  uniform sampler2D page;
  uniform float shot;
  uniform vec2 halfSize;
  float sdBox(vec3 p, vec3 b, float r) {vec3 q=abs(p)-b+r;return length(max(q,0.))+min(max(q.x,max(q.y,q.z)),0.)-r;}
  mat3 rx(float a){float c=cos(a),s=sin(a);return mat3(1.,0.,0.,0.,c,s,0.,-s,c);}
  mat3 ry(float a){float c=cos(a),s=sin(a);return mat3(c,0.,-s,0.,1.,0.,s,0.,c);}
  mat3 rz(float a){float c=cos(a),s=sin(a);return mat3(c,s,0.,-s,c,0.,0.,0.,1.);}
  vec3 local(vec3 p){
    if(shot>1.5&&shot<2.5)return rx(-.30)*ry(.28)*rz(-.065)*(p-vec3(.06,.0,0.));
    return ry(shot<1.5?.075:-.025)*rx(-.035)*rz(shot<1.5?-.012:.006)*p;
  }
  float object(vec3 p){
    vec3 q=local(p);
    if(shot>1.5&&shot<2.5) {
      float shell=sdBox(q,vec3(1.64,.94,.145),.045);
      // A continuous inset seam, cut into a solid rectangular volume.
      float seam=abs(q.z+.017)-.009;
      float inset=sdBox(q,vec3(1.625,.925,.155),.032);
      return max(shell,-max(-inset,seam));
    }
    return sdBox(q,vec3(halfSize,.049),.032);
  }
  vec3 normal(vec3 p){vec2 e=vec2(.00065,0.);return normalize(vec3(object(p+e.xyy)-object(p-e.xyy),object(p+e.yxy)-object(p-e.yxy),object(p+e.yyx)-object(p-e.yyx)));}
  vec3 env(vec3 r){
    vec3 c=vec3(.055,.057,.061);
    // Wide overhead white softbox, restrained side strip and warm fill.
    float broad=exp(-pow((r.x+.33)*1.65,6.)-pow((r.y-.66)*2.2,6.))*smoothstep(-.3,.25,r.z);
    float edge=exp(-pow((r.x-.73)*9.,2.)-pow((r.y-.18)*1.25,6.));
    float low=exp(-pow((r.y+.64)*8.,2.)-pow((r.x+.20)*1.2,6.));
    c+=vec3(2.4,2.38,2.32)*broad;
    c+=vec3(1.32,1.40,1.51)*edge;
    c+=vec3(.32,.34,.37)*low;
    return c;
  }
  vec3 softReflection(vec3 r,vec3 n,float rough){
    vec3 tangent=normalize(cross(n,vec3(.01,1.,.02))),bitan=cross(n,tangent);
    return env(r)*.40+(env(normalize(r+tangent*rough))+env(normalize(r-tangent*rough))+env(normalize(r+bitan*rough))+env(normalize(r-bitan*rough)))*.15;
  }
  vec3 nearSoftbox(vec3 p,vec3 reflected){
    // Finite studio cards. Unlike an infinitely distant environment, these
    // create broad moving reflection boundaries across the planar face.
    vec3 at=p+reflected*max((3.7-p.z)/max(reflected.z,.15),0.);
    float upper=exp(-pow((at.x+1.0)/3.9,6.)-pow((at.y-2.7)/2.3,6.));
    float strip=exp(-pow((at.x-3.1)/.65,2.)-pow((at.y+.6)/4.0,6.));
    float lower=exp(-pow((at.x+.7)/4.5,6.)-pow((at.y+3.3)/.8,2.));
    return vec3(1.32,1.30,1.25)*upper+vec3(.55,.61,.69)*strip+vec3(.12,.13,.15)*lower;
  }
  float hash(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
  vec3 tone(vec3 c){c=(c*(2.51*c+.03))/(c*(2.43*c+.59)+.14);return pow(clamp(c,0.,1.),vec3(1./2.2));}
  void main(){
    vec2 uv=(gl_FragCoord.xy-resolution*.5)/resolution.y;
    bool flight=shot>1.5&&shot<2.5;
    vec3 eye=flight?vec3(.15,.42,8.25):vec3(.04,.12,8.7);
    vec3 target=vec3(0.);vec3 f=normalize(target-eye),r=normalize(cross(f,vec3(0.,1.,0.))),up=cross(r,f);
    vec3 rd=normalize(f*1.12+r*uv.x+up*uv.y);
    // Neutral graphite cyclorama; local light gathers around the object.
    float pool=exp(-pow((uv.x+.08)*2.1,2.)-pow((uv.y-.02)*1.5,2.));
    vec3 col=vec3(.0065,.0070,.0082)+vec3(.019,.0196,.021)*pool;
    float floorGlow=exp(-pow((uv.y+.315)*26.,2.)-pow(uv.x*3.,2.));
    col+=vec3(.0045)*floorGlow;
    float foot=exp(-pow((uv.y+.335)*58.,2.)-pow(uv.x*5.,2.));
    col*=1.-foot*.60;
    // Airflow in camera space. All trails are left of the leading right edge.
    if(flight){
      float stream=0.;
      for(int i=0;i<15;i++){
        float fi=float(i),y=-.115+hash(vec2(fi,17.))*.25;
        float longness=.22+.23*hash(vec2(fi,2.));
        float endX=-.025+.035*sin(fi*2.13);
        float startX=endX-longness;
        float ramp=smoothstep(startX,startX+.12,uv.x)*(1.-smoothstep(endX-.02,endX,uv.x));
        float curve=.006*sin(uv.x*5.+fi*.75);
        float width=.00022+.00042*hash(vec2(fi,9.));
        float line=exp(-pow((uv.y-y-curve)/width,2.));
        stream+=line*ramp*(.025+.060*hash(vec2(fi,5.)));
      }
      col+=vec3(.42,.48,.56)*stream;
      // Sparse air sliding around the silhouette; shallow pressure at right.
      float bend=.246-.038*pow((uv.y+.005)/.13,4.);
      float ends=exp(-pow((uv.y+.005)/.125,12.));
      float contour=exp(-pow((uv.x-bend)/.0006,2.))*ends;
      float contour2=exp(-pow((uv.x-bend-.006)/.0004,2.))*ends;
      col+=vec3(.16,.19,.23)*(contour*.22+contour2*.06);
    }
    float dist=0.;bool hit=false;
    for(int i=0;i<150;i++){float d=object(eye+rd*dist);if(d<.00045){hit=true;break;}dist+=max(d*.78,.00025);if(dist>14.)break;}
    if(hit){
      vec3 p=eye+rd*dist,q=local(p),n=normal(p),ref=reflect(rd,n);
      float nv=max(dot(n,-rd),0.);
      vec3 ln=normalize(vec3(-2.,4.,5.));
      float light=max(dot(n,ln),0.);
      if(flight){
        vec3 refl=softReflection(ref,n,.19);
        vec3 area=nearSoftbox(p,ref);
        vec3 pearl=vec3(.22,.22,.218)*(.30+.70*light)+refl*.035+area*.55;
        vec3 polished=(softReflection(ref,n,.028)+area*.7)*(.70+.30*pow(1.-nv,5.));
        float broadFace=smoothstep(.80,.975,abs((rx(-.30)*ry(.28)*rz(-.065)*n).z));
        col=mix(polished,pearl,broadFace);
        float seam=1.-smoothstep(.007,.017,abs(q.z+.017));
        col=mix(col,vec3(.0035,.012,.026),seam*.95);
        // Blue information channel flows from face to the leading right edge.
        float line=1.-smoothstep(.006,.012,abs(q.y+.48));
        float ends=smoothstep(-1.35,-1.30,q.x)*(1.-smoothstep(1.56,1.63,q.x));
        float front=smoothstep(.120,.138,q.z);
        col=mix(col,vec3(.003,.023,.065),line*ends*front*.94);
        col+=vec3(.001,.030,.105)*line*ends*front;
        // The captured information remains in the face, with no invented role.
        vec2 tc=vec2((q.x+1.64)/3.28,1.-(q.y+.94)/1.88);
        vec4 content=texture2D(page,tc);
        col*=1.-content.a*front*.39;
        float hair=(hash(q.xy*1800.)-.5)*.0012;
        col+=hair*broadFace;
      }else{
        vec2 tc=vec2((q.x+halfSize.x)/(halfSize.x*2.),1.-(q.y+halfSize.y)/(halfSize.y*2.));
        vec3 tex=texture2D(page,tc).rgb;
        float face=smoothstep(.026,.044,q.z);
        vec3 rim=softReflection(ref,n,.04)*.65+vec3(.02);
        // Screenshot front stays colour-faithful; reflections live at the rim.
        col=mix(rim,pow(tex,vec3(2.2)),face);
        float edge=min(halfSize.x-abs(q.x),halfSize.y-abs(q.y));
        col+=vec3(.12)*exp(-pow(edge/.008,2.))*face;
      }
    }
    vec3 outColor=hit&&!flight&&local(eye+rd*dist).z>.044?pow(max(col,0.),vec3(1./2.2)):tone(col);
    outColor+=(hash(gl_FragCoord.xy)-.5)/850.;
    gl_FragColor=vec4(outColor,1.);
  }`;
  function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}
  const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vert));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,frag));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
  gl.useProgram(program);const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
  const loc=gl.getAttribLocation(program,'position');gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);
  const tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tex);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
  const u={};for(const key of ['resolution','page','shot','halfSize'])u[key]=gl.getUniformLocation(program,key);
  return {render(shot,texture,halfSize,w=2160,h=3840){canvas.width=w;canvas.height=h;gl.viewport(0,0,w,h);gl.useProgram(program);gl.bindTexture(gl.TEXTURE_2D,tex);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,texture);gl.uniform1i(u.page,0);gl.uniform1f(u.shot,shot);gl.uniform2f(u.halfSize,...halfSize);gl.uniform2f(u.resolution,w,h);gl.drawArrays(gl.TRIANGLES,0,6);return canvas;}};
};
