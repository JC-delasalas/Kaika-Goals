// Server-to-server adapter for the synthetic Kaika workshop only.
// The expiring capability is kept by the loopback Python gateway, never by the browser.
const BASE=Deno.env.get('SUPABASE_URL')!;
const key=JSON.parse(Deno.env.get('SUPABASE_SECRET_KEYS')||'{}').default||Deno.env.get('SUPABASE_SECRET_KEY')||Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const admin:Record<string,string>={apikey:key};if(key?.startsWith('eyJ'))admin.Authorization='Bearer '+key;
const bucket='kaika-deliverable-evidence',MAX=20*1024*1024;
const hash=async(b:Uint8Array)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new Uint8Array(b).buffer)),x=>x.toString(16).padStart(2,'0')).join('');
class Failure extends Error{constructor(message:string,public status=400){super(message)}}
const json=(data:unknown,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
async function rpc(token:string,action:string,data:unknown={}){const r=await fetch(BASE+'/rest/v1/rpc/kaika_workshop_store',{method:'POST',headers:{...admin,'Content-Type':'application/json'},body:JSON.stringify({p_hash:token,p_action:action,p_data:data})});const body=await r.json();if(!r.ok)throw new Failure(body.message||'Database request failed',r.status);return body}
async function bytes(req:Request,limit:number){if(Number(req.headers.get('content-length'))>limit)throw new Failure('Request too large',413);const reader=req.body?.getReader();if(!reader)throw new Failure('Empty request');let size=0;const chunks=[];while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>limit){await reader.cancel();throw new Failure('Request too large',413)}chunks.push(value)}const out=new Uint8Array(size);let offset=0;for(const part of chunks){out.set(part,offset);offset+=part.length}return out}
function validFile(b:Uint8Array,mime:string){
 const types=['application/pdf','image/png','image/jpeg','text/plain','text/csv','application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/vnd.openxmlformats-officedocument.presentationml.presentation'];
 if(!b.length||!types.includes(mime))throw new Failure('Unsupported or empty file');
 const ascii=new TextDecoder().decode(b.slice(0,8));
 if(mime==='application/pdf'&&!ascii.startsWith('%PDF-'))throw new Failure('Invalid PDF contents');
 if(mime==='image/png'&&Array.from(b.slice(0,8)).join(',')!=='137,80,78,71,13,10,26,10')throw new Failure('Invalid PNG contents');
 if(mime==='image/jpeg'&&!(b[0]===255&&b[1]===216&&b[2]===255))throw new Failure('Invalid JPEG contents');
 if(mime.includes('openxmlformats')&&!(b[0]===80&&b[1]===75&&b[2]===3&&b[3]===4))throw new Failure('Invalid Office container');
 if(mime.startsWith('text/')){try{new TextDecoder('utf-8',{fatal:true}).decode(b)}catch{throw new Failure('Text must use UTF-8')}if(b.includes(0))throw new Failure('Binary data in text file')}
}
export async function handler(req:Request){try{
 if(req.method!=='POST')return json({error:'POST required'},405);
 const token=req.headers.get('X-Kaika-Capability')||'';if(!/^[A-Za-z0-9_-]{43}$/.test(token))return json({error:'Private workshop connection required'},401);
 const digest=await hash(new TextEncoder().encode(token)),params=new URL(req.url).searchParams,action=params.get('action')||'load';
 if(action==='upload'){
  const did=params.get('deliverable_id'),eid=params.get('evidence_id'),leader=params.get('leader'),cid=params.get('checkpoint_id');
  if(!eid||!/^[a-f0-9-]{36}$/.test(eid))throw new Failure('Invalid file identifier');
  const context=await rpc(digest,'upload_context',{deliverable_id:did});
  if(!context||context.goal.active_version_id!==context.version.id||![context.deliverable.owner_id,context.version.owner_id].includes(leader))throw new Failure('Only the owner can upload to an approved deliverable',403);
  if(cid&&!context.checkpoints.some((c:{id:string})=>c.id===cid))throw new Failure('Checkpoint does not belong to deliverable');
  const b=await bytes(req,MAX),mime=(req.headers.get('Content-Type')||'').split(';')[0];validFile(b,mime);const sha=await hash(b),path='workshop/'+context.workspace_id+'/'+eid;
  const r=await fetch(BASE+'/storage/v1/object/'+bucket+'/'+path,{method:'POST',headers:{...admin,'Content-Type':mime,'x-upsert':'false'},body:b});
  if(!r.ok){const previous=await fetch(BASE+'/storage/v1/object/authenticated/'+bucket+'/'+path,{headers:admin});if(!previous.ok||await hash(new Uint8Array(await previous.arrayBuffer()))!==sha)throw new Failure('Upload failed or file identifier conflict',409)}
  return json({object_path:path,sha256:sha,byte_size:b.length});
 }
 const input=JSON.parse(new TextDecoder().decode(await bytes(req,4*1024*1024)));
 if(action==='download'){
  const file=await rpc(digest,'file',input);if(!file||file.upload_state!=='complete')throw new Failure('File not found',404);
  // The trusted local domain service has checked persona access before requesting this file.
  const r=await fetch(BASE+'/storage/v1/object/authenticated/'+bucket+'/'+file.object_path,{headers:admin});if(!r.ok)throw new Failure('Private evidence unavailable',404);
  return new Response(r.body,{headers:{'Content-Type':file.mime_type,'Content-Disposition':"attachment; filename*=UTF-8''"+encodeURIComponent(file.original_name),'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
 }
 if(!['load','commit','lookup'].includes(action))throw new Failure('Unsupported operation');
 return json(await rpc(digest,action,input));
}catch(e){return json({error:e instanceof Failure?e.message:'Request failed validation'},e instanceof Failure?e.status:400)}}
if(import.meta.main)Deno.serve(handler);
