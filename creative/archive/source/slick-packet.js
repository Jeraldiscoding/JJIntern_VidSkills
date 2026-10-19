/* Standalone deterministic WebGL studio object. Rotations are radians.
 * PacketRenderer.render(t, {angleX,angleY,angleZ,morph,width,height}) -> canvas.
 * morph 0 is a thin posting; morph 1 is a thick data carrier. No dependencies.
 */
(function () {
  'use strict';
  const canvas = document.createElement('canvas');
  const gl = canvas.getContext('webgl', {
    alpha: true, antialias: false, premultipliedAlpha: false,
    preserveDrawingBuffer: true, powerPreference: 'high-performance'
  });
  if (!gl) throw new Error('PacketRenderer requires WebGL (SwiftShader supported).');
  const vertex = `attribute vec2 position;
    void main(){gl_Position=vec4(position,0.,1.);}`;
  const fragment = `precision highp float;
    uniform vec2 resolution;
    uniform vec3 rotation;
    uniform float morph;
    uniform float time;
    mat3 orientation;
    vec3 halfSize;
    float bevel;
    float roundBox(vec3 p,vec3 b,float r){
      vec3 q=abs(p)-b;
      return length(max(q,0.))+min(max(q.x,max(q.y,q.z)),0.)-r;
    }
    float shapeLocal(vec3 p){
      float body=roundBox(p,halfSize-vec3(bevel),bevel);
      // Three actual shallow, rounded recesses, cut into the front face.
      float grooves=100.;
      for(int i=0;i<3;i++){
        float row=(float(i)-1.)*.275;
        float len=1.05-float(i)*.16;
        vec3 q=p-vec3(-.15,row,halfSize.z+.018);
        float cut=roundBox(q,vec3(len,.035,.045),.032);
        grooves=min(grooves,cut);
      }
      return max(body,-grooves);
    }
    float scene(vec3 p){return shapeLocal(orientation*p);}
    vec3 normalAt(vec3 p){
      vec2 e=vec2(.0012,0.);
      return normalize(vec3(scene(p+e.xyy)-scene(p-e.xyy),
        scene(p+e.yxy)-scene(p-e.yxy),scene(p+e.yyx)-scene(p-e.yyx)));
    }
    float softbox(vec3 r,vec3 axis,float sharp){
      return pow(max(dot(r,normalize(axis)),0.),sharp);
    }
    vec3 environment(vec3 r){
      vec3 col=vec3(.004,.008,.022);
      col+=vec3(.015,.045,.12)*pow(max(r.y*.5+.5,0.),2.);
      // Large neutral studio windows and a narrow blue kicker.
      col+=vec3(2.5,2.65,2.9)*softbox(r,vec3(-.7,1.15,1.9),38.);
      col+=vec3(1.4,1.50,1.70)*softbox(r,vec3(.90,.48,1.1),110.);
      col+=vec3(.025,.16,.64)*softbox(r,vec3(-1.,-.3,.5),28.);
      float strip=exp(-pow((r.y-.62)*22.,2.))*exp(-pow(r.x*1.1,4.));
      col+=vec3(.9,1.02,1.14)*strip;
      return col;
    }
    float distribution(float ndh,float rough){
      float a=rough*rough;float a2=a*a;
      float d=ndh*ndh*(a2-1.)+1.;
      return a2/(3.14159265*d*d+.00001);
    }
    vec3 fresnel(float vdh,vec3 f0){return f0+(1.-f0)*pow(1.-vdh,5.);}
    vec3 lamp(vec3 n,vec3 v,vec3 l,vec3 base,vec3 energy,float rough){
      vec3 h=normalize(v+l);float nl=max(dot(n,l),0.);
      float nv=max(dot(n,v),.001);float nh=max(dot(n,h),0.);
      float vh=max(dot(v,h),0.);float k=pow(rough+1.,2.)*.125;
      float gv=nv/(nv*(1.-k)+k);float gl=nl/(nl*(1.-k)+k);
      vec3 f=fresnel(vh,mix(vec3(.055),base,.42));
      vec3 spec=distribution(nh,rough)*gv*gl*f/max(4.*nl*nv,.002);
      return ((1.-f)*base*.34/3.14159265+spec)*energy*nl;
    }
    mat3 turnX(float a){float c=cos(a),s=sin(a);return mat3(1.,0.,0.,0.,c,s,0.,-s,c);}
    mat3 turnY(float a){float c=cos(a),s=sin(a);return mat3(c,0.,-s,0.,1.,0.,s,0.,c);}
    mat3 turnZ(float a){float c=cos(a),s=sin(a);return mat3(c,s,0.,-s,c,0.,0.,0.,1.);}
    void main(){
      vec2 uv=(gl_FragCoord.xy-.5*resolution)/resolution.y;
      orientation=turnX(-rotation.x)*turnY(-rotation.y)*turnZ(-rotation.z);
      halfSize=vec3(1.68,mix(.91,.75,morph),mix(.065,.31,morph));
      bevel=mix(.055,.15,morph);
      vec3 ro=vec3(0.,0.,5.8);
      vec3 rd=normalize(vec3(uv*3.3,-5.8));
      float travel=0.;float d=1.;bool hit=false;
      for(int i=0;i<82;i++){
        vec3 p=ro+rd*travel;d=scene(p);
        if(d<.0009){hit=true;break;}
        travel+=d*.85;
        if(travel>10.)break;
      }
      if(!hit){gl_FragColor=vec4(0.);return;}
      vec3 p=ro+rd*travel;vec3 q=orientation*p;
      vec3 n=normalAt(p);vec3 v=normalize(ro-p);
      float face=smoothstep(.70,.98,abs((orientation*n).z));
      // Subtle lens curvature gives the broad polished front a rolling reflection.
      vec3 bend=vec3(q.x*.028,q.y*.048,0.);
      n=normalize(n+vec3(dot(orientation[0],bend),dot(orientation[1],bend),dot(orientation[2],bend))*face);
      float front=smoothstep(halfSize.z-.14,halfSize.z+.008,q.z);
      float edge=1.-smoothstep(.045,.16,min(halfSize.x-abs(q.x),halfSize.y-abs(q.y)));
      vec3 base=mix(vec3(.001,.008,.035),vec3(.002,.025,.17),front);
      base=mix(base,vec3(.004,.052,.28),edge*.40);
      vec3 refl=reflect(-v,n);
      vec3 f=fresnel(max(dot(v,n),0.),vec3(.13,.17,.24));
      vec3 col=base*vec3(.13,.22,.50);
      col+=lamp(n,v,normalize(vec3(-.75,1.25,2.4)),base,vec3(2.7,2.74,2.8),.19);
      col+=lamp(n,v,normalize(vec3(1.9,.35,.4)),base,vec3(.25,.49,1.20),.24);
      col+=lamp(n,v,normalize(vec3(-1.6,-.4,.8)),base,vec3(.10,.20,.55),.22);
      col+=environment(refl)*(f+.08)*1.05;
      // A large diffused rectangular studio window reflected in the clear coat.
      // Its angle follows the view; it rolls across the lens instead of glowing.
      vec3 localView=orientation*v;
      float windowLine=q.y+.34*q.x-.12+localView.x*.30-localView.y*.22;
      float windowBand=exp(-pow(windowLine/.31,2.));
      float windowEdge=exp(-pow((windowLine+.14)/.070,2.));
      float windowFalloff=1.-smoothstep(.60,1.65,q.x);
      col+=vec3(.10,.17,.29)*windowBand*windowFalloff*face*front;
      col+=vec3(.13,.23,.40)*windowEdge*windowFalloff*face*front*.48;
      // Fine physical rim and face windows; slots sit beneath the surface.
      float facing=max(dot(n,v),0.);
      col+=vec3(.08,.24,.65)*pow(1.-facing,3.)*.34;
      col+=vec3(.14,.24,.36)*edge*pow(max(dot(n,normalize(vec3(-.8,1.2,1.6))),0.),8.)*.45;
      float slot=0.;
      for(int i=0;i<3;i++){
        float row=(float(i)-1.)*.275;float len=1.05-float(i)*.16;
        vec2 s=abs(q.xy-vec2(-.15,row))-vec2(len,.028);
        float dst=length(max(s,0.))+min(max(s.x,s.y),0.)-.025;
        slot=max(slot,1.-smoothstep(-.012,.025,dst));
      }
      float slotFront=smoothstep(halfSize.z-.11,halfSize.z-.008,q.z);
      col=mix(col,col*.18+vec3(.001,.014,.065),slot*slotFront*.88);
      col+=vec3(.01,.11,.36)*slot*slotFront*.12;
      // ACES-style display transform, then correct linear-to-sRGB conversion.
      col=(col*(2.51*col+.03))/(col*(2.43*col+.59)+.14);
      col=pow(clamp(col,0.,1.),vec3(1./2.2));
      gl_FragColor=vec4(col,1.);
    }`;
  function compile(type, source) {
    const shader = gl.createShader(type); gl.shaderSource(shader, source); gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader));
    return shader;
  }
  const program = gl.createProgram();
  gl.attachShader(program, compile(gl.VERTEX_SHADER, vertex));
  gl.attachShader(program, compile(gl.FRAGMENT_SHADER, fragment));
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
  gl.useProgram(program);
  const buffer = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]), gl.STATIC_DRAW);
  const attr = gl.getAttribLocation(program, 'position');
  gl.enableVertexAttribArray(attr); gl.vertexAttribPointer(attr, 2, gl.FLOAT, false, 0, 0);
  const uniforms = {};
  for (const key of ['resolution','rotation','morph','time']) uniforms[key] = gl.getUniformLocation(program, key);
  gl.disable(gl.DEPTH_TEST); gl.disable(gl.BLEND);
  window.PacketRenderer = {
    canvas,
    render(t, options = {}) {
      const width = Math.max(64, Math.round(options.width || 1080));
      const height = Math.max(64, Math.round(options.height || 800));
      if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
      gl.viewport(0, 0, width, height); gl.useProgram(program);
      gl.uniform2f(uniforms.resolution, width, height);
      gl.uniform3f(uniforms.rotation, options.angleX ?? -.18, options.angleY ?? -.35, options.angleZ ?? -.08);
      gl.uniform1f(uniforms.morph, Math.max(0, Math.min(1, options.morph ?? 1)));
      gl.uniform1f(uniforms.time, Number(t) || 0);
      gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
      return canvas;
    },
    info: 'Raymarched rounded solid, physically recessed slots, GGX studio lights; transparent WebGL output.'
  };
})();
