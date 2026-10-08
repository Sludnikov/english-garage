const CACHE='english-garage-v17';
const CORE=['./','index.html','styles.css','app.js','cards.json','manifest.webmanifest','vendor/ts-fsrs.umd.js','assets/locations/lab.png','assets/locations/mansion.png','assets/locations/garage.png','assets/hero.png','assets/gentlemen.png','assets/dark.png','assets/potter.png','assets/app-icon.png','progress-worker.js'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('english-garage-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET'||new URL(e.request.url).origin!==location.origin)return;
  const path=new URL(e.request.url).pathname;
  const fresh=e.request.mode==='navigate'||path.endsWith('/index.html')||path.endsWith('/app.js')||path.endsWith('/cards.json');
  if(fresh){
    e.respondWith(fetch(e.request).then(async response=>{
      if(response.ok)try{const cache=await caches.open(CACHE);await cache.put(e.request,response.clone());}catch(_){}
      return response;
    }).catch(()=>caches.match(e.request,{ignoreSearch:true})));
    return;
  }
  e.respondWith(caches.match(e.request).then(cached=>cached||fetch(e.request)));
});
