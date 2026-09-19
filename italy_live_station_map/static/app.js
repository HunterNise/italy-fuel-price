const START={lat:43.9303,lon:10.9079};
const PALETTE=['#0072B2','#56B4E9','#F0E442','#E69F00','#D55E00'];

const I18N={
 en:{
  title:'MIMIT station prices',subtitle:'official daily data, joined locally',searchPlaceholder:'Search a place in Italy…',
  fuel:'Fuel',petrol:'Petrol',diesel:'Diesel',methane:'Methane',mode:'Mode',self:'Self-service',served:'Served',
  radius:'Radius',fill:'Fill',freshness:'Freshness',all:'all',refresh:'Refresh map',syncCurrent:'Sync current snapshot',myLocation:'Use my location',
  ready:'Ready.',bestNearby:'Best prices nearby',rankSubtitle:'Price ranking ignores brands/ratings. Distance is straight-line from the selected point.',
  sort:'Sort',price:'Price',distance:'Distance',savings:'Savings vs median',show:'Show',distribution:'Current price distribution',
  relativePrice:'Relative price',helpTitle:'Map guide',helpIntro:'Click the map to move the selected search point. The dashed circle is the active radius.',
  shortcuts:'Keyboard shortcuts',panNorth:'Pan north',panWest:'Pan west',panSouth:'Pan south',panEast:'Pan east',zoom:'Zoom in / out',recenter:'Recenter',
  focusSearch:'Focus search',close:'Close popup/menu',
  guideIntroTitle:'Using the map',
  guideIntro:'Search for a place, click the map, or use your browser location to choose the centre point. The dashed circle is the active search radius.',
  guideDataTitle:'Prices and ranking',
  guideData:'Choose fuel, service mode and freshness. The map and ranking use the same filtered station set. “Show” changes only how many ranking rows are displayed; the histogram always describes all filtered stations.',
  guideReadTitle:'Reading a station',
  guideRead:'Each station shows the current reported price, straight-line distance, price age and savings versus the local median for your selected fill size. Click a ranked row or map marker to open its details.',
  historyTitle:'History',
  historyHelp:'The 7/30/90-day views read only dates already stored in the local SQLite database. Sync adds the newest official snapshot only. The current nationwide snapshot is not retained day-by-day; history is kept only for stations in areas you view, so disk use stays small.',
  stations:'stations',hiddenStale:'hidden as stale',min:'min',median:'median',max:'max',snapshot:'snapshot',registry:'registry',
  localHistory:'local history',snapshotDays:'snapshot days',tracked:'tracked stations',syncing:'Downloading the official current MIMIT snapshot…',
  syncDone:'Current snapshot synchronized',searchNoResults:'No places found.',searching:'Searching…',searchError:'Location search failed',
  loading:'Loading locally joined MIMIT snapshot…',syncFailed:'Sync failed',freshnessUnknown:'freshness unknown',less1:'<1 day old',
  oneDay:'1 day old',daysOld:'{n} days old',stale:'stale',belowMedian:'{c}¢/L below median',aboveMedian:'{c}¢/L above median',
  medianPrice:'median price',cheaperThan:'cheaper than {p}% of visible stations',lowest:'lowest price in current set',highest:'highest price in current set',
  saveFill:'save {v} / {l} L',aboveFill:'{v} above median / {l} L',atMedian:'at local median',
  savingFooter:'Savings are relative to the current area median for a {l} L fill. Driving/detour cost is not included.',
  spread:'spread {c}¢/L',histAllFiltered:'all {n} filtered stations; “Show” affects only the ranked list',
  historyFast:'History',daysAvailable:'{a}/{r} days available · {m} missing · no interpolation',
  localCoverage:'local station coverage: {n} snapshot days ({a} → {b})',noHistory:'No local history indexed for this period.',
  station:'Station ID',communicated:'communicated',distanceKm:'{n} km',locationDenied:'Location not used',browserGeoUnavailable:'Browser geolocation unavailable.'
 },
 it:{
  title:'Prezzi carburanti MIMIT',subtitle:'dati ufficiali giornalieri, uniti in locale',searchPlaceholder:'Cerca una località in Italia…',
  fuel:'Carburante',petrol:'Benzina',diesel:'Gasolio',methane:'Metano',mode:'Servizio',self:'Self-service',served:'Servito',
  radius:'Raggio',fill:'Rifornimento',freshness:'Freschezza',all:'tutti',refresh:'Aggiorna mappa',syncCurrent:'Sincronizza snapshot attuale',myLocation:'La mia posizione',
  ready:'Pronto.',bestNearby:'Migliori prezzi nei dintorni',rankSubtitle:'La classifica ignora marchi/recensioni. La distanza è in linea d’aria dal punto selezionato.',
  sort:'Ordina',price:'Prezzo',distance:'Distanza',savings:'Risparmio vs mediana',show:'Mostra',distribution:'Distribuzione prezzi attuale',
  relativePrice:'Prezzo relativo',helpTitle:'Guida mappa',helpIntro:'Clicca sulla mappa per spostare il punto di ricerca. Il cerchio tratteggiato indica il raggio attivo.',
  shortcuts:'Scorciatoie da tastiera',panNorth:'Sposta a nord',panWest:'Sposta a ovest',panSouth:'Sposta a sud',panEast:'Sposta a est',zoom:'Zoom avanti / indietro',recenter:'Ricentra',
  focusSearch:'Vai alla ricerca',close:'Chiudi popup/menu',
  guideIntroTitle:'Come usare la mappa',
  guideIntro:'Cerca una località, clicca sulla mappa oppure usa la posizione del browser per scegliere il punto centrale. Il cerchio tratteggiato è il raggio di ricerca attivo.',
  guideDataTitle:'Prezzi e classifica',
  guideData:'Scegli carburante, modalità di servizio e freschezza. Mappa e classifica usano lo stesso insieme di stazioni filtrate. “Mostra” cambia solo il numero di righe della classifica; l’istogramma descrive sempre tutte le stazioni filtrate.',
  guideReadTitle:'Come leggere una stazione',
  guideRead:'Ogni stazione mostra prezzo corrente comunicato, distanza in linea d’aria, età del prezzo e risparmio rispetto alla mediana locale per la quantità di rifornimento scelta. Clicca una riga o un marker per aprire i dettagli.',
  historyTitle:'Storico',
  historyHelp:'Le viste 7/30/90 giorni leggono solo le date già presenti nel database SQLite locale. La sincronizzazione aggiunge soltanto lo snapshot ufficiale più recente. Lo snapshot nazionale corrente non viene conservato giorno per giorno: lo storico viene mantenuto solo per gli impianti nelle aree che consulti, così lo spazio occupato resta ridotto.',
  stations:'stazioni',hiddenStale:'nascoste perché vecchie',min:'min',median:'mediana',max:'max',snapshot:'snapshot',registry:'anagrafica',
  localHistory:'storico locale',snapshotDays:'giorni snapshot',tracked:'impianti tracciati',syncing:'Scarico lo snapshot MIMIT attuale…',
  syncDone:'Snapshot attuale sincronizzato',searchNoResults:'Nessuna località trovata.',searching:'Ricerca…',searchError:'Ricerca località fallita',
  loading:'Carico lo snapshot MIMIT unito in locale…',syncFailed:'Sincronizzazione fallita',freshnessUnknown:'freschezza sconosciuta',less1:'meno di 1 giorno',
  oneDay:'1 giorno fa',daysOld:'{n} giorni fa',stale:'vecchio',belowMedian:'{c}¢/L sotto la mediana',aboveMedian:'{c}¢/L sopra la mediana',
  medianPrice:'prezzo mediano',cheaperThan:'più economico del {p}% delle stazioni visibili',lowest:'prezzo più basso del gruppo',highest:'prezzo più alto del gruppo',
  saveFill:'risparmi {v} / {l} L',aboveFill:'{v} sopra mediana / {l} L',atMedian:'alla mediana locale',
  savingFooter:'Il risparmio è rispetto alla mediana dell’area per un rifornimento di {l} L. Il costo della deviazione non è incluso.',
  spread:'ampiezza {c}¢/L',histAllFiltered:'tutte le {n} stazioni filtrate; “Mostra” limita solo la lista',
  historyFast:'Storico',daysAvailable:'{a}/{r} giorni disponibili · {m} mancanti · nessuna interpolazione',
  localCoverage:'copertura locale stazione: {n} giorni snapshot ({a} → {b})',noHistory:'Nessuno storico locale disponibile per questo periodo.',
  station:'ID impianto',communicated:'comunicato',distanceKm:'{n} km',locationDenied:'Posizione non usata',browserGeoUnavailable:'Geolocalizzazione browser non disponibile.'
 }
};

let lang=localStorage.getItem('fuelMapLang')||(navigator.language&&navigator.language.toLowerCase().startsWith('it')?'it':'en');
function T(key,vars={}){
 let s=(I18N[lang]&&I18N[lang][key])||I18N.en[key]||key;
 for(const [k,v] of Object.entries(vars))s=s.replaceAll(`{${k}}`,String(v));
 return s
}
function flagSVG(code){
 if(code==='it')return`<svg class="flag-svg" viewBox="0 0 30 20" aria-hidden="true"><rect width="10" height="20" fill="#009246"/><rect x="10" width="10" height="20" fill="#fff"/><rect x="20" width="10" height="20" fill="#ce2b37"/></svg>`;
 return`<svg class="flag-svg" viewBox="0 0 60 40" aria-hidden="true"><rect width="60" height="40" fill="#012169"/><path d="M0 0L60 40M60 0L0 40" stroke="#fff" stroke-width="9"/><path d="M0 0L60 40M60 0L0 40" stroke="#C8102E" stroke-width="4"/><path d="M30 0V40M0 20H60" stroke="#fff" stroke-width="13"/><path d="M30 0V40M0 20H60" stroke="#C8102E" stroke-width="7"/></svg>`
}
function applyLanguage(){
 document.documentElement.lang=lang;
 document.querySelectorAll('[data-i18n]').forEach(el=>el.textContent=T(el.dataset.i18n));
 document.querySelectorAll('[data-i18n-placeholder]').forEach(el=>el.placeholder=T(el.dataset.i18nPlaceholder));
 $('langToggle').innerHTML=flagSVG(lang)+`<span>${lang.toUpperCase()}</span>`;
 localStorage.setItem('fuelMapLang',lang);render()
}

const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const quantile=(a,p)=>{if(!a.length)return NaN;const x=(a.length-1)*p,l=Math.floor(x),h=Math.ceil(x);return l===h?a[l]:a[l]*(h-x)+a[h]*(x-l)};
const fmt=x=>Number.isFinite(x)?`€${x.toFixed(3)}`:'n/a';

const map=L.map('map',{zoomControl:false}).setView([START.lat,START.lon],13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
L.control.scale({imperial:false}).addTo(map);

const layer=L.layerGroup().addTo(map);
let center=null,radiusCircle=null,current={...START},stations=[],requestSeq=0,markerById=new Map(),lastServerState={};

function markerColor(price,lo,hi){
 if(!Number.isFinite(price)||!Number.isFinite(lo)||!Number.isFinite(hi)||hi<=lo)return PALETTE[2];
 const t=Math.max(0,Math.min(.999999,(price-lo)/(hi-lo)));return PALETTE[Math.min(4,Math.floor(t*5))]
}
function setSearchGeometry(lat,lon){
 if(center)center.remove();
 center=L.marker([lat,lon],{icon:L.divIcon({className:'',html:'<div class="center-dot"></div>',iconSize:[14,14],iconAnchor:[7,7]}),interactive:false}).addTo(map);
 if(radiusCircle)radiusCircle.remove();
 radiusCircle=L.circle([lat,lon],{radius:+$('radius').value*1000,color:'#4c5962',weight:1.2,opacity:.42,dashArray:'5 6',fillColor:'#7c8a93',fillOpacity:.06,interactive:false}).addTo(map)
}
function updateRadiusCircle(){if(radiusCircle)radiusCircle.setRadius(+$('radius').value*1000)}
function parseMimitDate(s){
 if(!s)return null;const x=String(s).trim();const m=x.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?/);
 if(m){const [,d,mo,y,h='0',mi='0',sec='0']=m;return new Date(+y,+mo-1,+d,+h,+mi,+sec)}const d=new Date(x);return Number.isNaN(+d)?null:d
}
function stationAgeDays(s){const d=parseMimitDate(s.updated)||parseMimitDate(s.observed_date);return d?Math.max(0,(Date.now()-d.getTime())/86400000):null}
function ageText(days){if(days==null||!Number.isFinite(days))return T('freshnessUnknown');if(days<1)return T('less1');if(days<2)return T('oneDay');return T('daysOld',{n:Math.floor(days)})}
function ageClass(days){if(days==null)return'mid';if(days<=1)return'good';if(days<=3)return'mid';return'old'}
function activeStations(){const raw=$('maxAgeDays').value;if(raw==='all')return stations;const max=+raw;return stations.filter(s=>{const a=stationAgeDays(s);return a!=null&&a<=max})}
function cheaperThanPct(price,visible){return visible.length?100*visible.filter(s=>Number.isFinite(s.price)&&s.price>price).length/visible.length:null}
function percentileText(price,visible){const p=cheaperThanPct(price,visible);if(p==null)return'';if(p<.5)return T('highest');if(p>99.5)return T('lowest');return T('cheaperThan',{p:Math.round(p)})}
function centsValue(x){return(x*100).toFixed(1)}
function toggleLabels(){const show=map.getZoom()>=12;layer.eachLayer(l=>{if(!l.getTooltip||!l.getTooltip())return;if(show)l.openTooltip();else l.closeTooltip()})}

function renderDistribution(visible,median){
 const box=$('distChart'),spread=$('distSpread');$('distNote').textContent=T('histAllFiltered',{n:visible.length});
 const vals=visible.map(s=>s.price).filter(Number.isFinite).sort((a,b)=>a-b);
 if(!vals.length){box.innerHTML='';spread.textContent='';return}
 const min=vals[0],max=vals.at(-1),range=Math.max(.001,max-min);
 const bins=Math.min(12,Math.max(5,Math.ceil(Math.sqrt(vals.length)))),counts=Array(bins).fill(0);
 vals.forEach(v=>{let i=Math.floor((v-min)/range*bins);if(i>=bins)i=bins-1;counts[i]++});
 const W=340,H=63,PL=5,PR=5,PT=5,PB=16,UW=W-PL-PR,UH=H-PT-PB,mxCount=Math.max(...counts,1),bw=UW/bins;
 const bars=counts.map((c,i)=>{const h=UH*c/mxCount,x=PL+i*bw+1,y=PT+UH-h;return`<rect x="${x}" y="${y}" width="${Math.max(1,bw-2)}" height="${h}" fill="#858b90" opacity=".72"><title>${c}</title></rect>`}).join('');
 const mx=PL+(median-min)/range*UW;
 box.innerHTML=`<svg width="100%" height="${H}" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${bars}<line x1="${mx}" y1="${PT}" x2="${mx}" y2="${PT+UH}" stroke="#222" stroke-width="1.2" stroke-dasharray="3 2"/><text x="${PL}" y="${H-3}" class="dist-axis">${fmt(min)}</text><text x="${W-PR}" y="${H-3}" text-anchor="end" class="dist-axis">${fmt(max)}</text></svg>`;
 spread.textContent=T('spread',{c:centsValue(max-min)})
}

function spark(points){
 if(!points.length)return`<div class="spark-empty">${T('noHistory')}</div>`;
 const W=280,H=76,P=9,vals=points.map(x=>+x.price),min=Math.min(...vals),max=Math.max(...vals),span=Math.max(.001,max-min);
 const start=new Date(points[0].date+'T00:00:00'),end=new Date(points.at(-1).date+'T00:00:00'),dspan=Math.max(1,(end-start)/86400000);
 const xy=points.map(x=>{const d=new Date(x.date+'T00:00:00');return{x:P+((d-start)/86400000)/dspan*(W-2*P),y:H-P-(+x.price-min)/span*(H-2*P),...x}});
 let segments=[],seg=[];xy.forEach((p,i)=>{if(i&&(new Date(p.date)-new Date(xy[i-1].date))/86400000>1){if(seg.length)segments.push(seg);seg=[]}seg.push(p)});if(seg.length)segments.push(seg);
 const lines=segments.map(s=>`<polyline fill="none" stroke="#222" stroke-width="1.6" points="${s.map(p=>`${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')}"/>`).join('');
 const dots=xy.map(p=>`<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="2" fill="#0072B2"><title>${p.date}: ${fmt(+p.price)}</title></circle>`).join('');
 return`<svg width="100%" height="${H}" viewBox="0 0 ${W} ${H}"><line x1="${P}" y1="${H-P}" x2="${W-P}" y2="${H-P}" stroke="#bbb" stroke-dasharray="2 3"/>${lines}${dots}<text x="${P+2}" y="11" font-size="9">${fmt(max)}</text><text x="${P+2}" y="${H-11}" font-size="9">${fmt(min)}</text></svg>`
}
async function loadHistory(box,id,fuel,self,days){
 box.innerHTML='<div class="spark-empty">…</div>';
 try{
  const r=await fetch(`/api/history?id=${encodeURIComponent(id)}&fuel=${encodeURIComponent(fuel)}&self=${self?1:0}&days=${days}`,{cache:'no-store'}),d=await r.json();
  if(!d.ok)throw Error(d.error||'history error');
  box.innerHTML=spark(d.points)+`<div class="spark-meta">${T('daysAvailable',{a:d.observed_days,r:d.requested_days,m:d.missing_days})}</div>`+(d.available_total_days?`<div class="spark-meta">${T('localCoverage',{n:d.available_total_days,a:d.available_start,b:d.available_end})}</div>`:'')
 }catch(e){box.innerHTML=`<div class="spark-empty">${esc(e.message)}</div>`}
}

function popupHtml(s){
 const key=`hist-${String(s.id).replace(/[^a-zA-Z0-9_-]/g,'')}-${Math.random().toString(36).slice(2,6)}`;
 return`<div class="popup-price">${fmt(s.price)}</div><div><b>${esc(s.fuel)}</b> · ${s.isSelf?T('self'):T('served')} · ${T('distanceKm',{n:s.distance_km.toFixed(1)})}</div>
 <div class="popup-meta">${T('station')} ${esc(s.id)}<br/>${esc(s.address)}<br/>${T('snapshot')}: ${esc(s.observed_date)}${s.updated?`<br/>${T('communicated')}: ${esc(s.updated)}`:''}<br/><span class="fresh ${ageClass(stationAgeDays(s))}">${ageText(stationAgeDays(s))}</span></div>
 <div class="history-head"><b>${T('historyFast')}</b><span class="history-btns"><button data-days="7">7d</button><button data-days="30">30d</button><button data-days="90">90d</button></span></div>
 <div id="${key}" data-history-id="${esc(s.id)}" data-fuel="${esc(s.fuel)}" data-self="${s.isSelf?1:0}"></div>`
}
function openStation(id){const marker=markerById.get(String(id));if(!marker)return;map.panTo(marker.getLatLng(),{animate:true});marker.openPopup()}

function renderRanking(visible,median){
 const fill=+$('fillLitres').value,mode=$('rankSort').value,limitRaw=$('rankLimit').value;
 const enriched=visible.map(s=>({...s,delta:s.price-median,saving:(median-s.price)*fill,ageDays:stationAgeDays(s),percentileLabel:percentileText(s.price,visible)}));
 enriched.sort((a,b)=>mode==='distance'?a.distance_km-b.distance_km||a.price-b.price:mode==='saving'?b.saving-a.saving||a.distance_km-b.distance_km:a.price-b.price||a.distance_km-b.distance_km);
 renderDistribution(visible,median);$('rankCount').textContent=`${enriched.length} ${T('stations')}`;$('rankFooter').textContent=T('savingFooter',{l:fill});
 const shown=limitRaw==='all'?enriched:enriched.slice(0,+limitRaw);
 if(!shown.length){$('rankList').innerHTML=`<div class="rank-empty">0 ${T('stations')}</div>`;return}
 $('rankList').innerHTML=shown.map((s,i)=>{
  const delta=Math.abs(s.delta)<.0005?T('medianPrice'):s.delta<0?T('belowMedian',{c:centsValue(Math.abs(s.delta))}):T('aboveMedian',{c:centsValue(s.delta)});
  const saving=s.saving>.005?T('saveFill',{v:fmt(s.saving),l:fill}):s.saving<-.005?T('aboveFill',{v:fmt(Math.abs(s.saving)),l:fill}):T('atMedian');
  return`<div class="rank-item" data-id="${esc(s.id)}"><div class="rank-num">${i+1}</div><div><div class="rank-price">${fmt(s.price)}</div><div class="rank-detail">${esc(s.address||`#${s.id}`)}</div><div class="rank-delta">${delta}</div><div class="rank-percentile">${esc(s.percentileLabel)}</div><div class="fresh ${ageClass(s.ageDays)}">${ageText(s.ageDays)}${s.ageDays!=null&&s.ageDays>3?`<span class="stale-badge">${T('stale')}</span>`:''}</div></div><div class="rank-right"><div class="rank-distance">${T('distanceKm',{n:s.distance_km.toFixed(1)})}</div><div class="rank-saving">${saving}</div></div></div>`
 }).join('');
 $('rankList').querySelectorAll('.rank-item').forEach(el=>el.addEventListener('click',()=>openStation(el.dataset.id)))
}

function render(){
 if(!$('rankList'))return;layer.clearLayers();markerById.clear();
 const visible=activeStations(),values=visible.map(s=>s.price).filter(Number.isFinite).sort((a,b)=>a-b),lo=quantile(values,.05),hi=quantile(values,.95),med=quantile(values,.5);
 visible.forEach(s=>{
  const marker=L.circleMarker([s.lat,s.lon],{radius:9,color:'#222',weight:.8,fillColor:markerColor(s.price,lo,hi),fillOpacity:.95}).addTo(layer);markerById.set(String(s.id),marker);
  marker.bindTooltip(`<span class="price-label">${fmt(s.price)}</span>`,{permanent:true,direction:'top',offset:[0,-7],className:'price-tip',opacity:1});
  marker.bindPopup(popupHtml(s),{maxWidth:330,autoPan:true,autoPanPaddingTopLeft:L.point(25,190),autoPanPaddingBottomRight:L.point(25,35)});
  marker.on('popupopen',e=>{const el=e.popup.getElement();if(!el)return;const box=el.querySelector('[data-history-id]');if(!box)return;const id=box.dataset.historyId,f=box.dataset.fuel,self=box.dataset.self==='1';loadHistory(box,id,f,self,7);el.querySelectorAll('[data-days]').forEach(b=>b.addEventListener('click',()=>loadHistory(box,id,f,self,+b.dataset.days)))})
 });
 $('lmin').textContent=values.length?fmt(values[0]):'—';$('lmid').textContent=values.length?fmt(med):'—';$('lmax').textContent=values.length?fmt(values.at(-1)):'—';
 const hidden=stations.length-visible.length;$('stats').innerHTML=values.length?`<span class="stat">${values.length} ${T('stations')}</span>${hidden?`<span class="stat">${hidden} ${T('hiddenStale')}</span>`:''}<span class="stat">${T('min')} ${fmt(values[0])}</span><span class="stat">${T('median')} ${fmt(med)}</span><span class="stat">${T('max')} ${fmt(values.at(-1))}</span>`:`<span class="stat">0 ${T('stations')}</span>`;
 renderRanking(visible,med);toggleLabels()
}

async function loadStations(){
 const seq=++requestSeq,fuel=$('fuel').value,self=$('mode').value,radius=$('radius').value;$('status').textContent=T('loading');
 try{
  const r=await fetch(`/api/stations?lat=${current.lat}&lon=${current.lon}&radius=${radius}&fuel=${encodeURIComponent(fuel)}&self=${self}`,{cache:'no-store'}),d=await r.json();
  if(seq!==requestSeq)return;if(!r.ok||!d.ok)throw Error(d.error||`HTTP ${r.status}`);
  stations=d.stations||[];lastServerState=d;render();
  $('status').innerHTML=`${T('snapshot')} <b>${esc(d.price_date)}</b> · ${T('registry')} ${esc(d.registry_date)} · ${T('localHistory')}: ${d.history_days||0} ${T('snapshotDays')} · ${d.tracked_station_rows||0} ${T('tracked')}`+(d.warning?`<br/><span class="warn">${esc(d.warning)}</span>`:'')
 }catch(e){if(seq!==requestSeq)return;stations=[];render();$('status').innerHTML=`<span class="warn">${esc(e.message)}</span>`}
}
async function syncNow(){
 const b=$('sync');b.disabled=true;$('status').textContent=T('syncing');
 try{
  const r=await fetch('/api/sync',{cache:'no-store'}),d=await r.json();if(!r.ok||!d.ok)throw Error(d.error||`HTTP ${r.status}`);
  $('status').textContent=`${T('syncDone')}: ${d.price_date} · ${T('localHistory')}: ${d.history_days||0} ${T('snapshotDays')}`;
  await loadStations()
 }catch(e){$('status').innerHTML=`<span class="warn">${T('syncFailed')}: ${esc(e.message)}</span>`}finally{b.disabled=false}
}
function relocate(lat,lon,zoom=13,reload=true){current={lat,lon};setSearchGeometry(lat,lon);map.setView([lat,lon],zoom);if(reload)loadStations()}
function useLocation(){if(!navigator.geolocation){$('status').textContent=T('browserGeoUnavailable');return}navigator.geolocation.getCurrentPosition(p=>relocate(p.coords.latitude,p.coords.longitude,14,true),e=>$('status').textContent=`${T('locationDenied')}: ${e.message}`)}

async function searchLocation(query){
 const results=$('searchResults');results.classList.add('show');results.innerHTML=`<div class="search-item">${T('searching')}</div>`;
 try{
  const r=await fetch(`/api/geocode?q=${encodeURIComponent(query)}&lang=${encodeURIComponent(lang)}`,{cache:'no-store'}),d=await r.json();if(!r.ok||!d.ok)throw Error(d.error||`HTTP ${r.status}`);
  if(!d.results.length){results.innerHTML=`<div class="search-item">${T('searchNoResults')}</div>`;return}
  results.innerHTML=d.results.map((x,i)=>`<div class="search-item" data-i="${i}">${esc(x.display_name)}</div>`).join('');
  results.querySelectorAll('.search-item[data-i]').forEach(el=>el.addEventListener('click',()=>{const x=d.results[+el.dataset.i];results.classList.remove('show');$('locationSearch').value=x.display_name;relocate(x.lat,x.lon,14,true)}))
 }catch(e){results.innerHTML=`<div class="search-item">${T('searchError')}: ${esc(e.message)}</div>`}
}

function pan(dir){const step=170,delta={up:[0,-step],down:[0,step],left:[-step,0],right:[step,0]}[dir];if(delta)map.panBy(delta,{animate:true})}
document.querySelectorAll('[data-pan]').forEach(b=>b.addEventListener('click',()=>pan(b.dataset.pan)));
document.querySelector('[data-zoom="in"]').addEventListener('click',()=>map.zoomIn());document.querySelector('[data-zoom="out"]').addEventListener('click',()=>map.zoomOut());document.querySelector('[data-recenter]').addEventListener('click',()=>map.setView([current.lat,current.lon],map.getZoom(),{animate:true}));

function resizeMapSoon(){map.invalidateSize({pan:false});setTimeout(()=>map.invalidateSize({pan:false}),220)}

$('radius').addEventListener('input',e=>{$('radiusValue').textContent=`${e.target.value} km`;updateRadiusCircle()});$('radius').addEventListener('change',loadStations);
$('fillLitres').addEventListener('input',e=>{$('fillLitresValue').textContent=`${e.target.value} L`;render()});
$('fuel').addEventListener('change',loadStations);$('mode').addEventListener('change',loadStations);$('maxAgeDays').addEventListener('change',render);$('refresh').addEventListener('click',loadStations);$('sync').addEventListener('click',syncNow);$('locate').addEventListener('click',useLocation);$('rankSort').addEventListener('change',render);$('rankLimit').addEventListener('change',render);
$('searchForm').addEventListener('submit',e=>{e.preventDefault();const q=$('locationSearch').value.trim();if(q)searchLocation(q)});
$('langToggle').addEventListener('click',()=>{lang=lang==='en'?'it':'en';applyLanguage()});
$('helpBtn').addEventListener('click',()=>$('helpModal').classList.add('show'));$('closeHelp').addEventListener('click',()=>$('helpModal').classList.remove('show'));$('helpModal').addEventListener('click',e=>{if(e.target===$('helpModal'))$('helpModal').classList.remove('show')});
$('collapseControls').addEventListener('click',()=>{$('controlBody').classList.toggle('collapsed');$('collapseControls').textContent=$('controlBody').classList.contains('collapsed')?'▾':'▴'});
$('hideSidebar').addEventListener('click',()=>{document.body.classList.add('sidebar-collapsed');resizeMapSoon()});
$('showSidebar').addEventListener('click',()=>{document.body.classList.remove('sidebar-collapsed');resizeMapSoon()});
map.on('click',e=>relocate(e.latlng.lat,e.latlng.lng,map.getZoom(),true));map.on('zoomend',toggleLabels);

document.addEventListener('keydown',e=>{
 const tag=(e.target&&e.target.tagName||'').toLowerCase(),typing=tag==='input'||tag==='select'||tag==='textarea';
 if(e.key==='Escape'){$('helpModal').classList.remove('show');$('searchResults').classList.remove('show');map.closePopup();return}
 if(typing)return;const k=e.key.toLowerCase();
 if(k==='/'){e.preventDefault();$('locationSearch').focus();return}if(k==='h'||e.key==='?'){$('helpModal').classList.add('show');return}if(k==='r'){loadStations();return}if(k==='l'){useLocation();return}if(e.key==='0'){map.setView([current.lat,current.lon],map.getZoom(),{animate:true});return}if(e.key==='+'||e.key==='='){map.zoomIn();return}if(e.key==='-'){map.zoomOut();return}
 const keyDir={w:'up',arrowup:'up',s:'down',arrowdown:'down',a:'left',arrowleft:'left',d:'right',arrowright:'right'}[k];if(keyDir){e.preventDefault();pan(keyDir)}
});
document.addEventListener('click',e=>{if(!e.target.closest('.search-row'))$('searchResults').classList.remove('show')});

setSearchGeometry(START.lat,START.lon);applyLanguage();loadStations();
