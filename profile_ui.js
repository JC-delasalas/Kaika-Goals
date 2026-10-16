// Images are fetched only for rendered people, in bounded, leader-scoped batches.
let profileCache=new Map(),profilePending=new Set(),profileCacheLeader='',profileEditor=null;
function profileKey(p){return p.id+':'+(p.profile_revision||0)}
function profilePhoto(p){return p?.photo_data_url||profileCache.get(profileKey(p||{}))||null}
async function loadProfilePhotos(){
 if(!data||loading)return;
 if(profileCacheLeader!==leader){profileCache.clear();profilePending.clear();profileCacheLeader=leader}
 const selected=leader,epochAtStart=epoch;
 const ids=[...new Set([...document.querySelectorAll('[data-profile-person]')].map(el=>el.dataset.profilePerson))];
 const needed=ids.map(person).filter(p=>p?.has_photo&&!profileCache.has(profileKey(p))&&!profilePending.has(profileKey(p))).slice(0,24);
 if(!needed.length)return;needed.forEach(p=>profilePending.add(profileKey(p)));
 try{const result=await request('profile_photos',{person_ids:needed.map(p=>p.id)});if(selected!==leader||epochAtStart!==epoch)return;
 for(const p of needed){const image=result.profiles.find(x=>x.person_id===p.id&&x.revision===p.profile_revision)?.photo_data_url;profileCache.set(profileKey(p),image||null)}
 document.querySelectorAll('[data-profile-person]').forEach(el=>{const p=person(el.dataset.profilePerson),image=profilePhoto(p);if(image){el.querySelector('img').src=image;el.setAttribute('aria-label',p.name+' · profile photo')}});
 }catch{ /* Keep the local avatar and let the editor offer an explicit retry. */ }
 finally{if(selected===leader){needed.forEach(p=>profilePending.delete(profileKey(p)));if(needed.every(p=>profileCache.has(profileKey(p))))setTimeout(loadProfilePhotos,0);}}
}
let profileSchedule;
new MutationObserver(()=>{clearTimeout(profileSchedule);profileSchedule=setTimeout(loadProfilePhotos,60)}).observe(document.body,{childList:true,subtree:true});
function profileEditorMarkup(){const p=person(leader),s=profileEditor;return '<form id="profile-form"><div class="profile-preview"><img id="profile-preview-image" src="'+(s.photo||defaultAvatarImage(leader,s.style))+'" alt="Profile preview" width="80" height="80"><div><b>'+esc(p.name)+'</b><p>'+esc(p.title||p.team)+'</p><small>Used wherever you own or contribute to work.</small></div></div><fieldset class="avatar-options"><legend>Choose an avatar</legend>'+Array.from({length:6},(_,i)=>'<label><input type="radio" name="avatar_style" value="'+i+'" '+(!s.photo&&s.style===i?'checked':'')+'><img src="'+defaultAvatarImage(leader,i)+'" alt="Avatar '+(i+1)+'" width="48" height="48"></label>').join('')+'</fieldset><label class="profile-upload">Or upload a photo<input type="file" id="profile-file" accept="image/jpeg,image/png,image/webp" aria-describedby="profile-file-help"></label><p id="profile-file-help">JPEG, PNG or WebP, up to 5 MB. Center-cropped to a square. Only a small thumbnail is saved; the original and its metadata are discarded.</p><div class="profile-form-actions"><button type="button" class="btn" id="profile-reset">Use default avatar</button><button class="btn primary" id="profile-save">Save profile</button></div><p role="alert" id="profile-error"></p></form>'}
const profileActBefore=act;act=async function(action,id){if(action!=='profile-edit')return profileActBefore(action,id);const p=person(leader);if(!p)return;profileEditor={person:leader,revision:p.profile_revision||0,style:p.avatar_style??null,photo:profilePhoto(p)};
 if(p.has_photo&&!profileEditor.photo){try{const r=await request('profile_photos',{person_ids:[leader]});profileEditor.photo=r.profiles[0]?.photo_data_url||null}catch(e){toast('Could not load your saved photo. Retry before editing.');return}}
 openDialog('Your profile',profileEditorMarkup());};
function updateProfilePreview(){document.getElementById('profile-preview-image').src=profileEditor.photo||defaultAvatarImage(leader,profileEditor.style);document.getElementById('profile-error').textContent=''}
document.addEventListener('change',async e=>{
 if(e.target.matches('#profile-form [name="avatar_style"]')){profileEditor.style=Number(e.target.value);profileEditor.photo=null;updateProfilePreview()}
 if(e.target.id!=='profile-file')return;
 const file=e.target.files?.[0],s=profileEditor,save=document.getElementById('profile-save');if(!file)return;save.disabled=true;
 try{if(!['image/jpeg','image/png','image/webp'].includes(file.type)||file.size>5*1024*1024)throw Error('Choose a JPEG, PNG or WebP file up to 5 MB.');
 const image=await createImageBitmap(file);try{if(image.width*image.height>16000000)throw Error('Choose an image under 16 megapixels.');const canvas=document.createElement('canvas');canvas.width=canvas.height=160;const size=Math.min(image.width,image.height);const c=canvas.getContext('2d');c.fillStyle='#fff';c.fillRect(0,0,160,160);c.drawImage(image,(image.width-size)/2,(image.height-size)/2,size,size,0,0,160,160);if(profileEditor!==s)return;s.photo=canvas.toDataURL('image/jpeg',.85)}finally{image.close()}
 document.querySelectorAll('#profile-form [name="avatar_style"]').forEach(r=>r.checked=false);updateProfilePreview();
 }catch(err){document.getElementById('profile-error').textContent=errorText(err)}finally{save.disabled=false;e.target.value=''}
});
document.addEventListener('click',e=>{if(e.target.id==='profile-reset'){profileEditor.style=null;profileEditor.photo=null;document.querySelectorAll('#profile-form [name="avatar_style"]').forEach(r=>r.checked=false);updateProfilePreview()}});
document.addEventListener('submit',async e=>{if(e.target.id!=='profile-form')return;e.preventDefault();if(busy||profileEditor.person!==leader)return;const f=e.target,s=profileEditor,b=f.querySelector('#profile-save');b.disabled=true;
 try{await command('profile_save',{person_id:leader,expected_revision:s.revision,avatar_style:s.style??avatarDefaultStyle(leader),photo_data_url:s.photo});profileCache.clear();$('dialog').close();render();}
 catch(err){f.querySelector('[role="alert"]').textContent=errorText(err)}finally{b.disabled=false}});
