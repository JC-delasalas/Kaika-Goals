"""Local FastAPI boundary. Persona switching is a trusted preview, not authentication."""
import base64,hashlib,json,re,secrets,time
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse,Response
from starlette.concurrency import run_in_threadpool
from starlette.middleware.gzip import GZipMiddleware
MAX=20*1024*1024

def create_app(root:Path,port=8787,fixtures=False):
 config_path=root/'.workshop-config.json'
 config=json.loads(config_path.read_text()) if config_path.exists() and not fixtures else {}
 if fixtures:
  from fixture_server import Fixture
  repository=Fixture(root/'.demo-state.json',default_scenario='strategy')
 else:
  from supabase_repository import SupabaseRepository
  repository=SupabaseRepository(config) if config.get('capability') else None
 nonce=secrets.token_urlsafe(32)
 @asynccontextmanager
 async def lifespan(app):
  yield
  if repository and hasattr(repository,'cloud'):
   repository.executor.shutdown(wait=True);repository.cloud.close()
 app=FastAPI(title='Kaika local API',docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)
 app.add_middleware(GZipMiddleware,minimum_size=1000,compresslevel=4)
 @app.middleware('http')
 async def boundary(request,call_next):
  start=time.perf_counter();hosts={'127.0.0.1:'+str(port),'localhost:'+str(port)}
  valid=request.headers.get('host') in hosts and request.headers.get('sec-fetch-site')!='cross-site'
  origin=request.headers.get('origin')
  valid=valid and (not origin or origin in {'http://'+h for h in hosts})
  if request.method=='POST':valid=valid and secrets.compare_digest(request.headers.get('x-kaika-nonce',''),nonce)
  if not valid:return JSONResponse({'error':'Local request validation failed'},status_code=403)
  response=await call_next(request)
  response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Server-Timing':'api;dur='+str(round((time.perf_counter()-start)*1000,1))})
  return response
 @app.get('/api/bootstrap')
 def bootstrap():return {'nonce':nonce,'mode':'fixture' if fixtures else 'supabase-demo','configured':bool(repository)}
 @app.get('/')
 @app.get('/Kaika-Connected-Preview.html')
 def home():
  html=root/'dist/Kaika-Connected-Preview.html'
  if not html.exists():html=root.parents[1]/'outputs/Kaika-Connected-Preview.html'
  content=html.read_bytes();script=re.search(rb'<script>([\s\S]*?)</script>',content)
  digest=base64.b64encode(hashlib.sha256(script.group(1)).digest()).decode()
  return Response(content,media_type='text/html',headers={'Content-Security-Policy':"default-src 'none'; script-src 'sha256-"+digest+"'; style-src 'unsafe-inline'; connect-src 'self'; img-src data:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"})
 @app.post('/api/{action}')
 async def command(action:str,request:Request):
  if action not in ('command','upload','download'):return JSONResponse({'error':'Not found'},status_code=404)
  if not repository:return JSONResponse({'error':'Private connection is not configured. Set up the local capability file.'},status_code=503)
  limit=MAX if action=='upload' else 1024*1024;chunks=[];size=0
  async for chunk in request.stream():
   size+=len(chunk)
   if size>limit:return JSONResponse({'error':'Request exceeds size limit'},status_code=413)
   chunks.append(chunk)
  if not size:return JSONResponse({'error':'Empty request'},status_code=400)
  try:status,body,headers=await run_in_threadpool(repository.handle,'/api/'+action,request.url.query,b''.join(chunks),request.headers)
  except Exception:return JSONResponse({'error':'Request could not be completed. Retry the same action to confirm its saved state.'},status_code=500)
  if isinstance(body,bytes):return Response(body,status_code=status,headers=headers)
  return JSONResponse(body,status_code=status,headers=headers)
 return app
