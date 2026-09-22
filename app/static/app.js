function cookieValue(name){
 const prefix=name+'=';
 return document.cookie.split(';').map(x=>x.trim()).find(x=>x.startsWith(prefix))?.slice(prefix.length)||'';
}
async function api(path,options={}){
 const method=(options.method||'GET').toUpperCase();
 const headers={'Content-Type':'application/json',...(options.headers||{})};
 if(!['GET','HEAD','OPTIONS'].includes(method)){
   const csrf=cookieValue('csrf_access_token');
   if(csrf) headers['X-CSRF-TOKEN']=decodeURIComponent(csrf);
 }
 const controller=new AbortController();
 const timeout=options.timeout||15000;
 const timer=setTimeout(()=>controller.abort(),timeout);
 let r,d={};
 try{
   r=await fetch(path,{credentials:'include',...options,headers,signal:options.signal||controller.signal});
   try{d=await r.json()}catch{}
 }catch(error){
   if(error.name==='AbortError') throw new Error('The request took too long. Please try again.');
   throw error;
 }finally{clearTimeout(timer)}
 if(!r.ok)throw new Error(d?.error?.message||d?.message||'Request failed');
 return d;
}
const qs=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
function icons(){if(window.lucide)lucide.createIcons()}
function toast(title,message,type='success'){const el=document.createElement('div');el.className='toast';el.innerHTML='<strong>'+esc(title)+'</strong><div>'+esc(message)+'</div>';qs('#toastStack')?.appendChild(el);setTimeout(()=>el.remove(),4500)}
function closeNotifications(){qs('#notificationPanel')?.classList.remove('open')}
async function openNotifications(filter='all'){
 const p=qs('#notificationPanel');p?.classList.add('open');
 try{const r=await api('/api/notifications');const items=r.data||[];renderNotifications(items,filter)}catch(e){const list=qs('#notificationList');if(list)list.innerHTML='<p class="muted">'+esc(e.message)+'</p>'}
}
function renderNotifications(items,filter='all'){
 const list=qs('#notificationList');if(!list)return;const filtered=filter==='unread'?items.filter(n=>!n.is_read):items;
 list.innerHTML=filtered.length?filtered.map(n=>'<div class="notification-item '+(!n.is_read?'unread':'')+'"><strong>'+esc(n.title)+'</strong><p>'+esc(n.message)+'</p><small>'+esc(n.channel)+' · '+new Date(n.created_at).toLocaleString()+'</small></div>').join(''):'<div class="empty-state compact"><div class="empty-icon">✓</div><strong>All clear</strong><span>No notifications in this view.</span></div>';
 const count=items.filter(n=>!n.is_read).length,c=qs('#notificationCount');if(c){c.textContent=count||'';c.style.display=count?'grid':'none'}icons()
}
function modal(title,html,onSubmit){
 const wrap=document.createElement('div');
 wrap.className='modal-backdrop open';
 wrap.innerHTML='<div class="modal" role="dialog" aria-modal="true" aria-label="'+esc(title)+'"><div class="section-head"><div><span class="eyebrow">QUICK ACTION</span><h2>'+esc(title)+'</h2></div><button class="icon-btn close" type="button" aria-label="Close"><i data-lucide="x"></i></button></div>'+html+'</div>';
 document.body.appendChild(wrap);icons();
 const close=()=>{wrap.remove();if(!document.querySelector('.modal-backdrop'))document.body.classList.remove('modal-open')};
 wrap.querySelector('.close').onclick=close;
 wrap.addEventListener('click',e=>{if(e.target===wrap)close()});
 document.body.classList.add('modal-open');
 const form=wrap.querySelector('form');
 if(form)form.onsubmit=async e=>{
   e.preventDefault();
   const submit=form.querySelector('button[type="submit"],button.btn');
   if(submit){submit.disabled=true;submit.dataset.old=submit.innerHTML;submit.innerHTML='<i data-lucide="loader-circle"></i> Saving...';icons()}
   try{await onSubmit(new FormData(form));close();}
   catch(x){if(submit){submit.disabled=false;submit.innerHTML=submit.dataset.old||'Save';icons()}toast('Could not save',x.message,'error')}
 };
 wrap.querySelectorAll('input,select,textarea').forEach((el,i)=>{if(i===0)setTimeout(()=>el.focus(),50)});
 wrap.addEventListener('keydown',e=>{if(e.key==='Escape')close()});
 return wrap
}
function openPetPhotoModal(pid,petName){
 const html='<form enctype="multipart/form-data"><div class="photo-drop"><div class="photo-preview" id="petPhotoPreview"><i data-lucide="image-plus"></i></div><div class="photo-copy"><strong>Upload '+esc(petName||'pet')+' photo</strong><span>JPG, PNG or WebP · max 5 MB</span></div><input id="petPhotoInput" name="photo" type="file" accept="image/jpeg,image/png,image/webp" required><label for="petPhotoInput" class="btn btn-secondary"><i data-lucide="upload"></i>Choose image</label></div><p class="muted">Optional. The image will appear on the pet profile and dashboard.</p><button class="btn btn-primary" type="submit"><i data-lucide="image-up"></i>Save pet photo</button></form>';
 const wrap=modal('Pet profile photo',html,async formData=>{
   const token=cookieValue('csrf_access_token');
   const headers=token?{'X-CSRF-TOKEN':decodeURIComponent(token)}:{};
   const response=await fetch('/api/pets/'+pid+'/photo',{method:'POST',credentials:'include',headers,body:formData});
   let data={};try{data=await response.json()}catch{}
   if(!response.ok)throw new Error(data?.error?.message||data?.message||'Could not upload image');
   toast('Photo updated',(petName||'Pet')+' profile photo has been saved.');
   setTimeout(()=>location.reload(),350);
 });
 const input=wrap.querySelector('#petPhotoInput'),preview=wrap.querySelector('#petPhotoPreview');
 input?.addEventListener('change',()=>{
   const file=input.files?.[0];if(!file)return;
   if(file.size>5*1024*1024){toast('Image too large','Choose an image smaller than 5 MB.','error');input.value='';return}
   const url=URL.createObjectURL(file);
   preview.innerHTML='<img src="'+url+'" alt="Pet photo preview">';
 });
 return wrap;
}
function openOwnerPhoneModal(){modal('Owner mobile number','<form><div class="phone-help">Use 10 digits or international format. Example <strong>+919876543210</strong>.</div><label>Mobile number<input name="phone" type="tel" inputmode="tel" autocomplete="tel" value="'+esc(document.querySelector('.phone-status')?.textContent.replace('✓ ','')||'')+'" placeholder="9876543210" required></label><p class="muted">This number is stored with the owner account and receives scheduled care SMS when messaging is configured.</p><button class="btn btn-primary" type="submit">Save mobile number</button></form>',async d=>{await api('/api/profile',{method:'PATCH',body:JSON.stringify(d)});toast('Mobile number saved','Scheduled owner alerts will use this number.');setTimeout(()=>location.reload(),500)})}
function openPetModal(){modal('Create a pet profile','<form><div class="modal-grid"><label>Pet name<input name="name" required></label><label>Species<input name="species" placeholder="Dog, Cat..." required></label></div><label>Owner mobile number<input name="owner_phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="9876543210" required></label><p class="phone-help">Enter 10 digits or international format. This number receives 2-day, 1-day and event-day SMS reminders.</p><div class="modal-grid"><label>Breed<input name="breed"></label><label>Weight<input name="weight" type="number" step="0.1"></label></div><div class="modal-grid"><label>Gender<input name="gender"></label><label>Color<input name="color"></label></div><div class="modal-grid"><label>Date of birth<input name="date_of_birth" type="date"></label><label>Microchip ID<input name="microchip_id"></label></div><label>Allergies<textarea name="allergies" rows="2"></textarea></label><label>Existing conditions<textarea name="conditions" rows="2"></textarea></label><button class="btn btn-primary" type="submit">Create profile <i data-lucide="arrow-right"></i></button></form>',async d=>{const r=await api('/api/pets',{method:'POST',body:JSON.stringify(d)});toast('Pet added','Owner number saved as '+(r.data?.owner_phone||d.owner_phone)+'.');setTimeout(()=>location.href='/pets/'+r.data.id,500)})}
async function openReminderModal(pid){if(!pid){const ps=await api('/api/pets');pid=ps.data[0]?.id}if(!pid)return toast('Add a pet first','Create a pet profile before adding reminders.','error');modal('Create a care reminder','<form><label>Title<input name="title" required placeholder="Checkup, grooming..."></label><div class="modal-grid"><label>Due date<input name="due_date" type="date" required></label><label>Time<input name="due_time" type="time"></label></div><label>Type<select name="reminder_type"><option>custom</option><option>checkup</option><option>vaccination</option><option>medication</option><option>appointment</option><option>deworming</option><option>grooming</option><option>preventive</option></select></label><label>Notes<textarea name="notes" rows="2"></textarea></label><button class="btn btn-primary" type="submit">Create reminder <i data-lucide="bell-plus"></i></button></form>',async d=>{await api('/api/pets/'+pid+'/reminders',{method:'POST',body:JSON.stringify(d)});toast('Reminder created','It will appear in the care queue.');setTimeout(()=>location.reload(),600)})}
async function addVaccination(pid){modal('Add vaccination','<form><label>Vaccine name<input name="vaccine_name" required></label><div class="modal-grid"><label>Given date<input name="given_date" type="date"></label><label>Next due date<input name="next_due_date" type="date"></label></div><div class="modal-grid"><label>Vaccine type<input name="vaccine_type"></label><label>Batch number<input name="batch_number"></label></div><div class="modal-grid"><label>Veterinarian<input name="veterinarian"></label><label>Clinic<input name="clinic"></label></div><label>Notes<textarea name="notes" rows="2"></textarea></label><button class="btn btn-primary" type="submit">Save vaccination <i data-lucide="syringe"></i></button></form>',async d=>{await api('/api/pets/'+pid+'/vaccinations',{method:'POST',body:JSON.stringify(d)});toast('Vaccination saved','The health passport is updated.');setTimeout(()=>location.reload(),600)})}
async function addMedication(pid){modal('Add medication','<form><div class="modal-grid"><label>Name<input name="name" required></label><label>Dosage<input name="dosage"></label></div><div class="modal-grid"><label>Frequency<input name="frequency"></label><label>Start date<input name="start_date" type="date"></label></div><label>End date<input name="end_date" type="date"></label><label>Instructions<textarea name="administration_instructions" rows="2"></textarea></label><button class="btn btn-primary" type="submit">Save medication <i data-lucide="pill"></i></button></form>',async d=>{await api('/api/pets/'+pid+'/medications',{method:'POST',body:JSON.stringify(d)});toast('Medication saved','The care plan is updated.');setTimeout(()=>location.reload(),600)})}
async function addAppointment(pid){modal('Schedule appointment','<form><div class="modal-grid"><label>Date<input name="appointment_date" type="date" required></label><label>Time<input name="appointment_time" type="time"></label></div><div class="modal-grid"><label>Clinic<input name="clinic"></label><label>Veterinarian<input name="vet_name"></label></div><label>Reason<input name="reason" placeholder="General checkup, follow-up..."></label><label>Notes<textarea name="notes" rows="2"></textarea></label><button class="btn btn-primary" type="submit">Schedule appointment <i data-lucide="calendar-plus"></i></button></form>',async d=>{await api('/api/pets/'+pid+'/appointments',{method:'POST',body:JSON.stringify(d)});toast('Appointment scheduled','A reminder has been added automatically.');setTimeout(()=>location.reload(),600)})}
async function addMedicalRecord(pid){modal('Add health record','<form><div class="modal-grid"><label>Date<input name="record_date" type="date"></label><label>Reason<input name="reason"></label></div><div class="modal-grid"><label>Veterinarian<input name="veterinarian"></label><label>Clinic<input name="clinic"></label></div><div class="modal-grid"><label>Diagnosis<input name="diagnosis"></label><label>Treatment<input name="treatment"></label></div><label>Symptoms<textarea name="symptoms" rows="2"></textarea></label><label>Notes<textarea name="notes" rows="2"></textarea></label><button class="btn btn-primary" type="submit">Save record <i data-lucide="file-plus-2"></i></button></form>',async d=>{await api('/api/pets/'+pid+'/medical-records',{method:'POST',body:JSON.stringify(d)});toast('Health record saved','The care timeline is up to date.');setTimeout(()=>location.reload(),600)})}
async function completeReminder(id){try{await api('/api/reminders/'+id+'/complete',{method:'POST'});toast('Reminder completed','The care queue is updated.');setTimeout(()=>location.reload(),500)}catch(e){toast('Could not complete',e.message,'error')}}
async function sendTestSms(){try{const r=await api('/api/notifications/test-sms',{method:'POST'});toast('Test SMS sent','Check '+(r.data?.phone||'the saved number')+' for the PAWCARE 360 test message.')}catch(e){toast('SMS test failed',e.message,'error')}}
function initTheme(){const root=document.documentElement;const saved=localStorage.getItem('pawcare-theme')||'system';const system=matchMedia('(prefers-color-scheme:dark)').matches;root.dataset.theme=saved==='system'?(system?'dark':'light'):saved;const b=qs('#themeToggle');b?.addEventListener('click',()=>{const saved=localStorage.getItem('pawcare-theme')||'system';const next=saved==='light'?'dark':saved==='dark'?'system':'light';const system=matchMedia('(prefers-color-scheme:dark)').matches;root.dataset.theme=next==='system'?(system?'dark':'light'):next;localStorage.setItem('pawcare-theme',next);toast('Theme changed',next==='system'?'Following system theme.':next==='dark'?'Dark theme enabled.':'Light theme enabled.');});matchMedia('(prefers-color-scheme:dark)').addEventListener('change',e=>{if((localStorage.getItem('pawcare-theme')||'system')==='system')root.dataset.theme=e.matches?'dark':'light'})}
function initSidebar(){const side=qs('#sidebar'),scrim=qs('#sidebarScrim');const open=()=>{side?.classList.add('open');scrim?.classList.add('open')},close=()=>{side?.classList.remove('open');scrim?.classList.remove('open')};qs('#mobileMenu')?.addEventListener('click',open);qs('#sidebarClose')?.addEventListener('click',close);scrim?.addEventListener('click',close);document.querySelectorAll('.side-link').forEach(a=>a.addEventListener('click',()=>{if(innerWidth<901)close()}));const path=location.pathname+location.hash;document.querySelectorAll('.side-link').forEach(a=>{if(a.getAttribute('href')===path||((path==='/dashboard'||path.startsWith('/dashboard#'))&&a.getAttribute('href')==='/dashboard'))a.classList.add('active')})}
function initProfileMenu(){const t=qs('#profileTrigger'),d=qs('#profileDropdown');t?.addEventListener('click',e=>{e.stopPropagation();d?.classList.toggle('open')});document.addEventListener('click',()=>d?.classList.remove('open'));qs('#profileLogout')?.addEventListener('click',async()=>{await logout()})}
async function logout(){try{await api('/api/auth/logout',{method:'POST'})}finally{location.href='/'}}
function animateCounters(){document.querySelectorAll('[data-counter]').forEach(el=>{const target=Number(el.dataset.counter||0);const start=performance.now(),duration=650;function tick(now){const p=Math.min(1,(now-start)/duration),ease=1-Math.pow(1-p,3);el.textContent=Math.round(target*ease);if(p<1)requestAnimationFrame(tick)}requestAnimationFrame(tick)})}
function initSearch(){const input=qs('#globalSearch');if(!input)return;let timer;const box=document.createElement('div');box.className='search-results';input.parentElement.appendChild(box);const search=async()=>{const q=input.value.trim();if(!q){box.classList.remove('open');return}try{const r=await api('/api/search?q='+encodeURIComponent(q));const items=r.data||[];box.innerHTML=items.length?items.map(x=>'<a href="'+esc(x.url)+'"><strong>'+esc(x.title)+'</strong><span>'+esc(x.subtitle)+'</span></a>').join(''):'<div class="search-empty">No matching records</div>';box.classList.add('open')}catch(e){box.innerHTML='<div class="search-empty">'+esc(e.message)+'</div>';box.classList.add('open')}};input.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(search,220)});input.addEventListener('keydown',e=>{if(e.key==='Escape'){input.value='';box.classList.remove('open')}if(e.key==='Enter'&&box.querySelector('a'))location.href=box.querySelector('a').href});document.addEventListener('click',e=>{if(!input.parentElement.contains(e.target))box.classList.remove('open')});document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();input.focus()}})}
async function syncNav(){
 if(!qs('#sidebar'))return;
 try{
   const r=await api('/api/profile',{timeout:8000});
   const name=r.data?.full_name||'Pet owner';
   const initial=name.charAt(0).toUpperCase();
   document.querySelectorAll('#sidebarName,#topProfileName').forEach(e=>e.textContent=name);
   document.querySelectorAll('.profile-avatar').forEach(e=>e.textContent=initial);
   document.querySelectorAll('.admin-link').forEach(e=>e.style.display=r.data?.role==='admin'?'flex':'none');
   qs('#logoutBtn')?.style.setProperty('display','flex');
 }catch(e){document.querySelectorAll('.admin-link').forEach(e=>e.style.display='none')}
}
function friendlyAuthNavigation(){
 document.querySelectorAll('a[href^="/dashboard"],a[href^="/pets/"],a[href="/admin"]').forEach(a=>{
   a.addEventListener('click',()=>{
     if(a.target==='_blank'||a.hasAttribute('download')||a.getAttribute('href')?.startsWith('#'))return;
     showPageLoader();
   });
 });
}
function showPageLoader(){
 let loader=qs('#pageLoader');
 if(!loader){
   loader=document.createElement('div');loader.id='pageLoader';loader.className='page-loader';
   loader.innerHTML='<span></span><span></span><span></span>';
   document.body.appendChild(loader);
 }
 requestAnimationFrame(()=>loader.classList.add('active'));
}
function hidePageLoader(){qs('#pageLoader')?.classList.remove('active')}
function initCalendarView(){const buttons=document.querySelectorAll('[data-calendar-view]'),days=document.querySelectorAll('.calendar-day');if(!buttons.length)return;const today=new Date();const iso=d=>d.toISOString().slice(0,10);buttons.forEach(b=>b.addEventListener('click',()=>{buttons.forEach(x=>x.classList.remove('active'));b.classList.add('active');const mode=b.dataset.calendarView;days.forEach(cell=>{const d=new Date(cell.dataset.day+'T00:00:00');let show=true;if(mode==='day')show=iso(d)===iso(today);if(mode==='week'){const monday=new Date(today);const offset=(today.getDay()+6)%7;monday.setDate(today.getDate()-offset);const sunday=new Date(monday);sunday.setDate(monday.getDate()+6);show=d>=monday&&d<=sunday}cell.style.display=show?'block':'none'})}))}
function initAuthForms(){
 const login=qs('#loginForm');
 if(login) login.addEventListener('submit',async e=>{
   e.preventDefault();
   const btn=login.querySelector('button[type="submit"]');
   const message=login.querySelector('#formMessage');
   const data=Object.fromEntries(new FormData(login));
   const redirect=data.login_redirect||new URLSearchParams(location.search).get('next')||'/dashboard';
   if(btn){btn.disabled=true;btn.dataset.old=btn.innerHTML;btn.innerHTML='<i data-lucide="loader-circle"></i> Signing in...';icons()}
   if(message){message.textContent='';message.className='message'}
   try{
     const r=await api('/api/auth/login',{method:'POST',body:JSON.stringify({email:data.email,password:data.password})});
     if(message){message.textContent='Login successful. Redirecting...';message.className='message success'}
     toast('Welcome back',r.data?.user?.name||'Signed in successfully.');
     window.location.assign(redirect.startsWith('/')?redirect:'/dashboard');
   }catch(err){
     if(message){message.textContent=err.message;message.className='message error'}
     toast('Sign in failed',err.message,'error');
     if(btn){btn.disabled=false;btn.innerHTML=btn.dataset.old||'Sign in';icons()}
   }
 });
 const register=qs('#registerForm');
 if(register) register.addEventListener('submit',async e=>{
   e.preventDefault();
   const btn=register.querySelector('button[type="submit"],button.btn');
   const message=register.querySelector('#formMessage');
   const data=Object.fromEntries(new FormData(register));
   if(btn){btn.disabled=true;btn.dataset.old=btn.innerHTML;btn.innerHTML='<i data-lucide="loader-circle"></i> Creating account...';icons()}
   if(message){message.textContent='';message.className='message'}
   try{
     await api('/api/auth/register',{method:'POST',body:JSON.stringify({full_name:data.full_name,email:data.email,phone:data.phone,password:data.password})});
     const r=await api('/api/auth/login',{method:'POST',body:JSON.stringify({email:data.email,password:data.password})});
     if(message){message.textContent='Account created. Redirecting...';message.className='message success'}
     toast('Account created','Welcome to PAWCARE 360.');
     window.location.assign('/dashboard');
   }catch(err){
     if(message){message.textContent=err.message;message.className='message error'}
     toast('Could not create account',err.message,'error');
     if(btn){btn.disabled=false;btn.innerHTML=btn.dataset.old||'Create account';icons()}
   }
 });
}
function initNotificationFilters(){document.querySelectorAll('[data-notification-filter]').forEach(b=>b.addEventListener('click',async()=>{document.querySelectorAll('[data-notification-filter]').forEach(x=>x.classList.remove('active'));b.classList.add('active');const r=await api('/api/notifications');renderNotifications(r.data||[],b.dataset.notificationFilter)}))}
document.addEventListener('DOMContentLoaded',()=>{
 document.body.classList.add('app-ready');
 icons();initAuthForms();initTheme();initSidebar();initProfileMenu();initSearch();animateCounters();initNotificationFilters();initCalendarView();syncNav();friendlyAuthNavigation(); document.body.addEventListener('click',e=>{if(e.target.closest('#notificationBtn'))openNotifications()});
 qs('#logoutBtn')?.addEventListener('click',logout);
  document.addEventListener('click',e=>{
   const link=e.target.closest('a[href]');
   if(!link||e.defaultPrevented)return;
   const href=link.getAttribute('href')||'';
   if(link.target==='_blank'||link.hasAttribute('download')||href.startsWith('#')||href.startsWith('mailto:')||href.startsWith('tel:')||href.startsWith('javascript:'))return;
   if(href===location.pathname+location.search){e.preventDefault();return}
   showPageLoader();
 });
 window.addEventListener('pageshow',hidePageLoader);
 window.addEventListener('load',()=>setTimeout(hidePageLoader,120));
 window.addEventListener('error',()=>hidePageLoader());
});


/* PAWCARE 360 interaction layer */
function setButtonBusy(button,busy,label){
 if(!button)return;
 if(busy){
   if(button.dataset.busy==='1')return;
   button.dataset.busy='1';button.disabled=true;button.dataset.originalHtml=button.innerHTML;
   button.innerHTML='<span class="button-spinner" aria-hidden="true"></span><span>'+esc(label||'Working...')+'</span>';
 }else{
   button.disabled=false;button.dataset.busy='0';
   if(button.dataset.originalHtml)button.innerHTML=button.dataset.originalHtml;
   icons();
 }
}
document.addEventListener('submit',e=>{
 const form=e.target;
 if(!(form instanceof HTMLFormElement)||form.dataset.noBusy==='true')return;
 const button=form.querySelector('button[type="submit"]');
 if(button&&!button.disabled&&!form.id?.match(/loginForm|registerForm/))setButtonBusy(button,true,'Saving...');
});
document.addEventListener('click',e=>{
 const button=e.target.closest('button');
 if(button?.dataset.loadingText&&!button.disabled)setButtonBusy(button,true,button.dataset.loadingText);
});
function initSectionScrollSpy(){
 const links=[...document.querySelectorAll('.profile-tabs a[href^="#"]')];
 if(!links.length||!('IntersectionObserver' in window))return;
 const sections=links.map(a=>document.querySelector(a.getAttribute('href'))).filter(Boolean);
 const observer=new IntersectionObserver(entries=>{
   entries.forEach(entry=>{
     if(!entry.isIntersecting)return;
     links.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+entry.target.id));
   });
 },{rootMargin:'-25% 0px -60% 0px',threshold:0});
 sections.forEach(s=>observer.observe(s));
}
function initSmoothAnchors(){
 document.addEventListener('click',e=>{
   const a=e.target.closest('a[href^="#"]');if(!a)return;
   const id=a.getAttribute('href');if(!id||id==='#')return;
   const target=document.querySelector(id);if(!target)return;
   e.preventDefault();
   const top=target.getBoundingClientRect().top+scrollY-(window.innerWidth<=640?78:92);
   window.scrollTo({top:Math.max(0,top),behavior:'smooth'});
   history.replaceState(null,'',id);
 });
}
function initScrollTop(){
 let btn=qs('#scrollTop');
 if(!btn){
   btn=document.createElement('button');btn.id='scrollTop';btn.className='scroll-top icon-btn';btn.setAttribute('aria-label','Back to top');
   btn.innerHTML='<i data-lucide="arrow-up"></i>';document.body.appendChild(btn);icons();
 }
 const sync=()=>btn.classList.toggle('show',scrollY>500);
 addEventListener('scroll',sync,{passive:true});sync();
 btn.addEventListener('click',()=>scrollTo({top:0,behavior:'smooth'}));
}
function initTableMotion(){
 document.querySelectorAll('.data-row,.event-row,.appointment-row,.record-row,.attention-item').forEach((el,i)=>{
   el.style.setProperty('--row-delay',Math.min(i,8)*25+'ms');
   el.classList.add('interactive-row');
 });
}
initSectionScrollSpy();initSmoothAnchors();initScrollTop();initTableMotion();
