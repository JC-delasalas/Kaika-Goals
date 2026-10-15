/** Typed network boundary shared by the incremental legacy UI migration. */
export interface Transport { send(url: string, options: RequestInit): Promise<Response> }
declare global { interface Window { KaikaTransport: Transport } }
window.KaikaTransport = {
 async send(url, options) {
  const controller=new AbortController();
  const upload=url.startsWith('/api/upload') || url.startsWith('/api/download');
  const slow=window.setTimeout(()=>{
   const status=document.getElementById('toast');
   if(status){status.textContent='The connection is taking longer than expected. Waiting for confirmation…';status.classList.add('show');}
  },3500);
  // Never auto-retry writes or report failure as success. App retains mutation IDs.
  const deadline=window.setTimeout(()=>controller.abort(),upload?45000:12000);
  const started=performance.now();
  try {
   const response=await fetch(url,{...options,signal:controller.signal});
   document.documentElement.dataset.lastRequestMs=String(Math.round(performance.now()-started));
   return response;
  } catch(error) {
   if(controller.signal.aborted)throw new Error('Connection timed out. Your save may still finish. Retry the same action to confirm it safely.');
   throw error;
  } finally {clearTimeout(slow);clearTimeout(deadline);}
 }
};
