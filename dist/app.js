/* English Garage — offline-first client, FSRS schedules, versioned OPFS progress. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const DECKS = {gentlemen: {name:'Джентльмены · сезон 2', subtitle:'Поместье, сделки и отношения'}, dark:{name:'Тьма',subtitle:'Тайны, время и семья'}, potter:{name:'Гарри Поттер',subtitle:'Школа, дружба и приключения'}};
  const LOCATIONS = {lab:{name:'Лаборатория',image:'assets/locations/lab.png'},mansion:{name:'Особняк',image:'assets/locations/mansion.png'},garage:{name:'Гараж',image:'assets/locations/garage.png'}};
  const SHOP = [
    {id:'cash',name:'Пачки денег',asset:'assets/items/cash.png',price:100,description:'Пачки фунтов в коллекции',x:'77%',y:'71%',w:'18%'},
    {id:'watch',name:'Швейцарские часы',asset:'assets/items/watch.png',price:180,description:'Аксессуар героя',x:'83%',y:'82%',w:'11%'},
    {id:'ring',name:'Перстень',asset:'assets/items/ring.png',price:220,description:'Родовой перстень',x:'63%',y:'79%',w:'11%'},
    {id:'cigars',name:'Шкатулка с сигарами',asset:'assets/items/cigars.png',price:280,description:'Коллекционный предмет',x:'4%',y:'70%',w:'18%'},
    {id:'car',name:'Спортивное авто',asset:'assets/items/car.png',price:350,description:'Автомобиль в локации',x:'2%',y:'68%',w:'39%'},
    {id:'art',name:'Картина',asset:'assets/items/art.png',price:480,description:'Искусство в коллекции',x:'79%',y:'10%',w:'15%'},
    {id:'guncase',name:'Охотничий кейс',asset:'assets/items/guncase.png',price:550,description:'Коллекционный кейс',x:'5%',y:'79%',w:'22%'},
    {id:'trophy',name:'Кубок',asset:'assets/items/trophy.png',price:700,description:'Трофей коллекции',x:'68%',y:'19%',w:'13%'},
    {id:'estate',name:'Загородный дом',asset:'assets/items/estate.png',price:800,description:'Ключ и документ на поместье',x:'3%',y:'43%',w:'16%'},
    {id:'bag',name:'Дорожная сумка',asset:'assets/items/bag.png',price:900,description:'Аксессуар для поездок',x:'25%',y:'78%',w:'18%'},
    {id:'club',name:'Частный клуб',asset:'assets/items/club.png',price:1000,description:'+10% будущих монет',bonus:.1,x:'71%',y:'53%',w:'15%'},
    {id:'company',name:'Ключи от империи',asset:'assets/items/keys.png',price:1700,description:'+15% будущих монет',bonus:.15,x:'4%',y:'14%',w:'15%'},
    {id:'hotel',name:'Городской особняк',asset:'assets/items/townhouse.png',price:2600,description:'+25% будущих монет',bonus:.25,x:'80%',y:'34%',w:'16%'},
    {id:'cufflinks',name:'Запонки',asset:'assets/items/cufflinks.png',price:320,description:'Набор в футляре',x:'54%',y:'79%',w:'12%'},
    {id:'poker-case',name:'Покерный набор',asset:'assets/items/poker-case.png',price:420,description:'Коллекционный кейс',x:'47%',y:'68%',w:'17%'},
    {id:'champagne',name:'Шампанское',asset:'assets/items/champagne.png',price:560,description:'Праздничный набор',x:'62%',y:'54%',w:'14%'},
    {id:'suit',name:'Костюм на манекене',asset:'assets/items/suit.png',price:600,description:'Экспонат гардероба',x:'58%',y:'16%',w:'17%'},
    {id:'binoculars',name:'Бинокль',asset:'assets/items/binoculars.png',price:650,description:'Аксессуар коллекции',x:'20%',y:'48%',w:'15%'},
    {id:'burgundy-car',name:'Бордовый ретроавтомобиль',asset:'assets/items/burgundy-car.png',price:750,description:'Редкий автомобиль',x:'5%',y:'70%',w:'32%'},
    {id:'suv',name:'Чёрный внедорожник',asset:'assets/items/suv.png',price:1200,description:'Большой автомобиль',x:'25%',y:'64%',w:'38%'},
    {id:'silver-car',name:'Серебристое купе',asset:'assets/items/silver-car.png',price:1300,description:'Современный автомобиль',x:'56%',y:'68%',w:'37%'},
    {id:'safe',name:'Сейф с золотом',asset:'assets/items/safe.png',price:1500,description:'Золото и коллекция',x:'78%',y:'57%',w:'18%'}
  ];
  const fsrs = FSRS.fsrs(FSRS.generatorParameters({request_retention:.9,learning_steps:[],relearning_steps:[],enable_short_term:false}));
  const worker = new Worker('progress-worker.js');
  let requestId = 0, pending = new Map(), saveQueue = Promise.resolve(), cards = [], byId = new Map(), current = null, flipped = false, deck = 'gentlemen';
  let state = {version:1,createdAt:new Date().toISOString(),updatedAt:null,settings:{retention:.9},balance:0,owned:[],location:'lab',schedule:{},history:[],rewarded:{},newStarted:{}};
  worker.onmessage = e => {const {id,ok,data,error}=e.data;const item=pending.get(id);if(!item)return;pending.delete(id);ok?item.resolve(data):item.reject(new Error(error));};
  function storage(type,payload){return new Promise((resolve,reject)=>{const id=++requestId;pending.set(id,{resolve,reject});worker.postMessage({id,type,payload});});}
  function setStatus(message,error=false){$('storage-status').textContent=message;$('storage-status').style.color=error?'#a45d51':'#749179';}
  function save(){state.updatedAt=new Date().toISOString();const snapshot=JSON.parse(JSON.stringify(state));saveQueue=saveQueue.then(()=>storage('write',snapshot)).then(()=>setStatus('Сохранено автоматически · progress.json')).catch(e=>setStatus('Ошибка сохранения: '+e.message,true));return saveQueue;}
  function dayKey(date=new Date()){return [date.getFullYear(),String(date.getMonth()+1).padStart(2,'0'),String(date.getDate()).padStart(2,'0')].join('-');}
  function startedToday(){return state.newStarted[dayKey()]||0;}
  function revived(card){return {...card,due:new Date(card.due),last_review:card.last_review?new Date(card.last_review):undefined};}
  function isDueToday(c,now,today){const scheduled=state.schedule[c.id];if(!scheduled||!(new Date(scheduled.due).getTime()<=now))return false;return !scheduled.last_review||dayKey(new Date(scheduled.last_review))!==today;}
  function dueCards(d){const now=Date.now(),today=dayKey();return cards.filter(c=>c.deck===d&&isDueToday(c,now,today)).sort((a,b)=>new Date(state.schedule[a.id].due)-new Date(state.schedule[b.id].due));}
  function nextCard(d){const due=dueCards(d);if(due.length)return due[0];return cards.find(c=>c.deck===d&&!state.schedule[c.id])||null;}
  function bonus(){return Math.min(.5,SHOP.filter(i=>state.owned.includes(i.id)).reduce((n,i)=>n+(i.bonus||0),0));}
  function renderStats(){const today=dayKey(),now=Date.now();$('balance').textContent=state.balance.toLocaleString('ru-RU');$('today-count').textContent=Object.keys(state.rewarded).filter(k=>k.endsWith(':'+today)).length;$('due-count').textContent=cards.filter(c=>isDueToday(c,now,today)).length;$('new-count').textContent=startedToday();}
  function renderCard(){
    renderStats();current=nextCard(deck);flipped=false;
    $('card-translation').classList.add('hidden');$('rating-area').classList.add('hidden');
    $('flip-button').classList.toggle('hidden',!current);$('flashcard').classList.toggle('hidden',!current);$('study-empty').classList.toggle('hidden',!!current);
    if(!current)return;
    $('card-image').src=current.image;
    $('card-image').alt=current.imageContext||('Кадр из '+(current.deck==='potter'?'фильма «Гарри Поттер»':current.deck==='dark'?'сериала «Тьма»':'сериала «Джентльмены»'));
    $('card-theme').textContent=DECKS[deck].name;
    $('card-word').textContent=current.word;
    $('card-level').textContent=current.level+' · '+current.pos;
    $('card-position').textContent=state.schedule[current.id]?'ПОВТОРЕНИЕ':'НОВОЕ СЛОВО';
    $('card-translation').textContent=current.ru;
    const audioSource=$('audio-source');
    if(current.audioType==='speech-synthesis'){
      audioSource.removeAttribute('href');
      audioSource.textContent='Произношение: голос устройства · en-US';
    }else{
      audioSource.href=current.audioAttribution;
      audioSource.textContent='Аудио: '+(current.audioCredit||'Wikimedia')+' · '+(current.audioLicense||'Commons')+' ↗';
    }
    $('card-audio-error').classList.add('hidden');
    $('image-context').textContent=current.imageContext||'';
    $('image-context').classList.add('hidden');
    const hasImageSource=/^https?:\/\//.test(current.imageSource||'');
    const imageSource=$('image-source');imageSource.classList.toggle('hidden',!hasImageSource);
    $('image-theme-label').classList.toggle('hidden',hasImageSource);
    if(hasImageSource){imageSource.href=current.imageSource;imageSource.textContent=['series-photo','themed-prop-photo'].includes(current.imageType)?'Источник фото ↗':'Источник кадра ↗';}
  }
  function renderDecks(){const holder=$('deck-cards');holder.replaceChildren();$('library-total').textContent=cards.length.toLocaleString('ru-RU');for(const [key,meta] of Object.entries(DECKS)){const total=cards.filter(c=>c.deck===key).length,count=cards.filter(c=>c.deck===key&&state.schedule[c.id]).length;const el=document.createElement('article');el.className='deck-card';const img=document.createElement('img');img.src='assets/'+key+'.png';img.alt='';const text=document.createElement('div');const h=document.createElement('h2');h.textContent=meta.name;const p=document.createElement('p');p.textContent=meta.subtitle;const strong=document.createElement('strong');strong.textContent=count+' / '+total+' начато';text.append(h,p,strong);el.append(img,text);el.addEventListener('click',()=>{deck=key;document.querySelector('[data-deck="'+key+'"]').click();showView('study');});holder.append(el);}}
  function renderGarage(){
    const items=$('scene-items'), gallery=$('owned-gallery');
    items.replaceChildren(); gallery.replaceChildren();
    for(const item of SHOP.filter(i=>state.owned.includes(i.id))){
      const marker=document.createElement(item.asset?'img':'div');
      marker.className=item.asset?'scene-prop':'scene-item';
      marker.style.left=item.x; marker.style.top=item.y;
      if(item.asset){marker.src=item.asset;marker.alt=item.name;marker.style.width=item.w;marker.title=item.name;}
      else {marker.setAttribute('aria-label',item.name+' в локации');const symbol=document.createElement('span');symbol.className='scene-object';symbol.textContent=item.icon;const name=document.createElement('span');name.className='scene-object-name';name.textContent=item.name;marker.append(symbol,name);}
      items.append(marker);
      const tile=document.createElement('div'); tile.className='owned-tile';
      const tileIcon=document.createElement(item.asset?'img':'span');if(item.asset){tileIcon.src=item.asset;tileIcon.alt='';}else tileIcon.textContent=item.icon;
      const tileName=document.createElement('strong'); tileName.textContent=item.name;
      tile.append(tileIcon,tileName); gallery.append(tile);
    }
    if(!state.owned.length){const empty=document.createElement('p');empty.className='owned-empty';empty.textContent='Пока нет покупок. Первый предмет появится здесь и в локации.';gallery.append(empty);}
    const n=state.owned.length;
    $('owned-count').textContent=n+' '+(n%10===1&&n%100!==11?'предмет':n%10>=2&&n%10<=4&&(n%100<12||n%100>14)?'предмета':'предметов');
    if(!LOCATIONS[state.location])state.location='lab';
    $('location-background').src=LOCATIONS[state.location].image;
    $('location-background').alt=LOCATIONS[state.location].name;
    for(const b of document.querySelectorAll('[data-location]'))b.classList.toggle('selected',b.dataset.location===state.location);
    const list=$('shop-list');list.replaceChildren();
    for(const item of SHOP){
      const owned=state.owned.includes(item.id),el=document.createElement('article');el.className='shop-item';
      el.innerHTML='<div class="shop-art"></div><h3></h3><p></p><button></button>';
      const art=el.querySelector('.shop-art');if(item.asset){const img=document.createElement('img');img.src=item.asset;img.alt='';art.append(img);}else art.textContent=item.icon;
      el.querySelector('h3').textContent=item.name;el.querySelector('p').textContent=item.description;
      const btn=el.querySelector('button');if(owned)btn.textContent='Куплено';else {const coin=document.createElement('img');coin.src='assets/coin.png';coin.alt='';coin.className='coin-icon';btn.append(String(item.price)+' ',coin);btn.setAttribute('aria-label','Купить '+item.name+' за '+item.price+' монет');}btn.disabled=owned||state.balance<item.price;btn.addEventListener('click',()=>buy(item.id));list.append(el);
    }
  }
  function showView(view){document.querySelectorAll('.view').forEach(e=>e.classList.toggle('active',e.id===view));document.querySelectorAll('.bottom-nav button').forEach(e=>e.classList.toggle('active',e.dataset.view===view));if(view==='garage')renderGarage();if(view==='library')renderDecks();window.scrollTo(0,0);}
  function buy(id){const item=SHOP.find(i=>i.id===id);if(!item||state.owned.includes(id)||state.balance<item.price)return;state.balance-=item.price;state.owned.push(id);save();renderStats();renderGarage();$('scene-message').textContent=item.name+' добавлен в локацию';document.querySelector('.garage-scene').scrollIntoView({behavior:'smooth',block:'center'});}
  function rate(value){if(!current||!flipped)return;const now=new Date(),id=current.id,isNew=!state.schedule[id];const prior=isNew?FSRS.createEmptyCard(now):revived(state.schedule[id]);const result=fsrs.repeat(prior,now)[value];if(!result)return;state.schedule[id]=result.card;state.history.push({cardId:id,at:now.toISOString(),rating:value,due:result.card.due});if(isNew){const key=dayKey(now);state.newStarted[key]=(state.newStarted[key]||0)+1;}const rewardKey=id+':'+dayKey(now);if(!state.rewarded[rewardKey]){state.rewarded[rewardKey]=true;state.balance+=Math.round(10*(1+bonus()));}save();renderCard();}
  async function play(){if(!current)return;if(current.audioType==='speech-synthesis'){if(!('speechSynthesis'in window)){$('card-audio-error').classList.remove('hidden');return;}const utterance=new SpeechSynthesisUtterance(current.word);utterance.lang='en-US';utterance.rate=.9;const voice=speechSynthesis.getVoices().find(v=>v.lang.toLowerCase()==='en-us');if(voice)utterance.voice=voice;utterance.onerror=()=>$('card-audio-error').classList.remove('hidden');speechSynthesis.cancel();speechSynthesis.speak(utterance);return;}const audio=new Audio(current.audio);try{await audio.play();}catch(e){$('card-audio-error').classList.remove('hidden');}}
  async function exportProgress(){await saveQueue;const content=JSON.stringify(state,null,2),name='english-garage-progress-'+dayKey()+'.json',file=new File([content],name,{type:'application/json'});if(navigator.share&&navigator.canShare?.({files:[file]})){try{await navigator.share({files:[file],title:'English Garage — прогресс'});return;}catch(e){if(e.name==='AbortError')return;}}const url=URL.createObjectURL(file),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);}
  async function importProgress(file){try{const parsed=JSON.parse(await file.text());if(parsed.version!==1||!parsed.schedule||!Array.isArray(parsed.owned)||!Array.isArray(parsed.history)||!parsed.rewarded||typeof parsed.balance!=='number'||parsed.balance<0)throw new Error('Неверный формат progress.json');for(const id of Object.keys(parsed.schedule))if(!byId.has(id))throw new Error('Файл содержит неизвестные карточки');state={...state,...parsed};state.settings={retention:.9,...state.settings};delete state.settings.dailyNewLimit;await save();renderCard();renderGarage();renderDecks();setStatus('Прогресс восстановлен и сохранён');}catch(e){setStatus('Не удалось импортировать: '+e.message,true);}}
  async function start(){try{cards=await (await fetch('cards.json?v=17',{cache:'no-store'})).json();if(!Array.isArray(cards)||!cards.length)throw new Error('Карточки не загрузились');byId=new Map(cards.map(c=>[c.id,c]));if(byId.size!==cards.length)throw new Error('Найдены повторяющиеся ID карточек');const saved=await storage('read');if(saved){if(saved.version!==1)throw new Error('Неподдерживаемая версия progress.json');state={...state,...saved};state.settings={retention:.9,...state.settings};delete state.settings.dailyNewLimit;}setStatus('Прогресс хранится в OPFS · progress.json');renderCard();renderGarage();renderDecks();}catch(e){setStatus('Не удалось открыть данные: '+e.message,true);$('study-empty').classList.remove('hidden');$('flashcard').classList.add('hidden');$('flip-button').classList.add('hidden');}}
  document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.view)));
  document.querySelectorAll('[data-deck]').forEach(b=>b.addEventListener('click',()=>{deck=b.dataset.deck;document.querySelectorAll('[data-deck]').forEach(x=>x.classList.toggle('selected',x===b));renderCard();}));
  document.querySelectorAll('[data-rating]').forEach(b=>b.addEventListener('click',()=>rate(Number(b.dataset.rating))));
  document.querySelectorAll('[data-location]').forEach(b=>b.addEventListener('click',()=>{if(b.disabled)return;state.location=b.dataset.location;save();renderGarage();}));
  $('flip-button').addEventListener('click',()=>{flipped=true;$('card-translation').classList.remove('hidden');$('image-context').classList.toggle('hidden',!current.imageContext);$('rating-area').classList.remove('hidden');$('flip-button').classList.add('hidden');});
  $('play-audio').addEventListener('click',play);$('export-button').addEventListener('click',exportProgress);$('import-input').addEventListener('change',e=>{if(e.target.files[0])importProgress(e.target.files[0]);e.target.value='';});
  if('serviceWorker'in navigator){navigator.serviceWorker.addEventListener('controllerchange',()=>location.reload());navigator.serviceWorker.register('sw.js',{updateViaCache:'none'}).then(reg=>reg.update()).catch(()=>{});}
  start();
})();
