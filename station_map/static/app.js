const START={lat:41.9028,lon:12.4964};
const PALETTE=['#0072B2','#56B4E9','#F0E442','#E69F00','#D55E00'];
const PREF_KEY='fuelMapPrefsV4';
const LEGACY_PREF_KEYS=['fuelMapPrefsV3','fuelMapPrefsV2','fuelMapPrefsV1'];
const DATA=window.FuelMapData;
if(!DATA)throw Error('FuelMap data provider is not loaded.');
const APP_VERSION=(()=>{try{return new URL(document.currentScript.src).searchParams.get('v')||'dev'}catch{return'dev'}})();
const MOBILE_LAYOUT=window.matchMedia('(max-width: 820px)');
const isMobileLayout=()=>MOBILE_LAYOUT.matches;

const I18N={
 en:{
  title:'MIMIT station prices',subtitle:'official daily data, joined locally',subtitleStatic:'official daily data, static public snapshot',searchPlaceholder:'Search a place in Italy…',
  fuel:'Fuel',petrol:'Petrol',diesel:'Diesel',methane:'Methane',mode:'Mode',self:'Self-service',served:'Served',
  radius:'Radius',fitRadius:'Fit radius',fill:'Fill',freshness:'Freshness',all:'all',
  refresh:'Refresh map',syncCurrent:'Sync current snapshot',myLocation:'Use my location',currentLocation:'Current location',
  ready:'Ready.',bestNearby:'Best prices nearby',rankSubtitle:'Price ranking ignores brands/ratings. Distance is straight-line from the selected point.',
  sort:'Sort',price:'Price',distance:'Distance',savings:'Savings vs median',show:'Show',filters:'Filters',maxPriceLabel:'Max price',maxDistanceLabel:'Max distance',resetFilters:'Reset filters',distribution:'Current price distribution',
  relativePrice:'Relative price',helpTitle:'Help & about',guideTab:'Guide',aboutTab:'About',shortcuts:'Keyboard shortcuts',panNorth:'Pan north',panWest:'Pan west',panSouth:'Pan south',panEast:'Pan east',zoom:'Zoom in / out',recenter:'Recenter',
  focusSearch:'Focus search',close:'Close popup/menu',backToResults:'Back to results',hidePanel:'Hide panel',showResults:'Show results',stationDetails:'Station details',
  guideIntroTitle:'Using the map',guideIntro:'Search for a place, click the map, or use your browser location to choose the centre point. The dashed circle is the active search radius.',
  guideDataTitle:'Prices and ranking',guideData:'Choose fuel, service mode and freshness. Filters can limit maximum price and/or straight-line distance. Sort and Show affect the final visible subset used consistently by the map, ranking and price distribution.',
  guideReadTitle:'Station details',guideRead:'Select a marker or ranking row to focus the same station. Desktop opens a map popup; narrow screens switch the lower sheet from results to station details. History always belongs to the selected fuel and service mode.',
  touchTitle:'Touch controls',touchHelp:'Drag and pinch the map normally. The lower sheet holds either results or station details: use Back to return to results, Hide to maximize the map, and the bottom-right reopen control to restore results. The price-distribution row expands on tap.',
  freshnessHelpTitle:'Freshness and history',historyTitle:'History',historyHelp:'Freshness filters each station by its communicated price age. Local history contains only snapshots actually stored for viewed stations; missing days are never interpolated.',historyHelpStatic:'Freshness filters each station by its communicated price age. The public map exposes the generated rolling 7-day history; missing source days remain missing and are never interpolated. Public snapshot health is shown separately in the top status line.',
  aboutVersionLabel:'Version',aboutModeLabel:'Data mode',aboutSnapshotLabel:'Price snapshot',aboutRegistryLabel:'Station registry',aboutGeneratedLabel:'Generated',aboutRefreshLabel:'Refresh',
  aboutModeStatic:'Public static snapshot',aboutModeLocal:'Local Python runtime',aboutRefreshStatic:'Scheduled 09:15 Europe/Rome (GitHub Actions; best-effort)',aboutRefreshLocal:'Synchronization is controlled by the local Python server',
  aboutProjectTitle:'Project',aboutProjectText:'Independent interface built around official Italian public fuel-price data. It is not an official MIMIT service and does not imply endorsement by the source institutions.',
  repositoryLink:'GitHub repository',sourcesLicencesLink:'Sources & licences',aboutSourcesTitle:'Primary sources',aboutLicenceNote:'MIMIT data: IODL 2.0. ISTAT geographic material: CC BY 4.0. Map tiles/data attribution remains with OpenStreetMap contributors. See Sources & licences for details.',
  stations:'stations',hiddenStale:'hidden as stale',min:'min',median:'median',max:'max',snapshot:'snapshot',registry:'registry',
  localHistory:'local history',publicHistory:'public history',snapshotDays:'snapshot days',tracked:'tracked stations',syncing:'Downloading the official current MIMIT snapshot…',
  syncDone:'Current snapshot synchronized',searchNoResults:'No places found.',searching:'Searching…',searchError:'Location search failed',
  loading:'Loading locally joined MIMIT snapshot…',loadingStatic:'Loading generated public station data…',syncFailed:'Sync failed',freshnessUnknown:'freshness unknown',less1:'<1 day old',
  oneDay:'1 day old',daysOld:'{n} days old',stale:'stale',snapshotCurrent:'current',snapshotStale:'stale · {n} days old',belowMedian:'{c}¢/L below median',aboveMedian:'{c}¢/L above median',
  medianPrice:'median price',cheaperThan:'cheaper than {p}% of visible stations',lowest:'lowest price in current set',highest:'highest price in current set',
  saveFill:'save {v} / {l} L',aboveFill:'{v} above median / {l} L',atMedian:'at local median',
  savingFooter:'Savings use the median of all {n} freshness-filtered stations for a {l} L fill. Driving/detour cost is not included.',
  spread:'spread {c}¢/L',histShown:'{shown} shown · {total} filtered',shownOf:'{shown}/{total} shown',
  historyFast:'History',daysAvailable:'{a}/{r} days available · {m} missing · no interpolation',
  localCoverage:'local station coverage: {n} snapshot days ({a} → {b})',publicCoverage:'public history coverage: {n} snapshot days ({a} → {b})',noHistory:'No history available for this period.',
  station:'Station ID',communicated:'communicated',distanceKm:'{n} km',locationDenied:'Location not used',browserGeoUnavailable:'Browser geolocation unavailable.',staleCount:'{n} stale hidden'
 },
 it:{
  title:'Prezzi carburanti MIMIT',subtitle:'dati ufficiali giornalieri, uniti in locale',subtitleStatic:'dati ufficiali giornalieri, snapshot pubblico statico',searchPlaceholder:'Cerca una località in Italia…',
  fuel:'Carburante',petrol:'Benzina',diesel:'Gasolio',methane:'Metano',mode:'Servizio',self:'Self-service',served:'Servito',
  radius:'Raggio',fitRadius:'Inquadra raggio',fill:'Rifornimento',freshness:'Freschezza',all:'tutti',
  refresh:'Aggiorna mappa',syncCurrent:'Sincronizza snapshot attuale',myLocation:'La mia posizione',currentLocation:'Posizione attuale',
  ready:'Pronto.',bestNearby:'Migliori prezzi nei dintorni',rankSubtitle:'La classifica ignora marchi/recensioni. La distanza è in linea d’aria dal punto selezionato.',
  sort:'Ordina',price:'Prezzo',distance:'Distanza',savings:'Risparmio vs mediana',show:'Mostra',filters:'Filtri',maxPriceLabel:'Prezzo max',maxDistanceLabel:'Distanza max',resetFilters:'Azzera filtri',distribution:'Distribuzione prezzi attuale',
  relativePrice:'Prezzo relativo',helpTitle:'Guida e informazioni',guideTab:'Guida',aboutTab:'Info',shortcuts:'Scorciatoie da tastiera',panNorth:'Sposta a nord',panWest:'Sposta a ovest',panSouth:'Sposta a sud',panEast:'Sposta a est',zoom:'Zoom avanti / indietro',recenter:'Ricentra',
  focusSearch:'Vai alla ricerca',close:'Chiudi popup/menu',backToResults:'Torna ai risultati',hidePanel:'Nascondi pannello',showResults:'Mostra risultati',stationDetails:'Dettagli impianto',
  guideIntroTitle:'Come usare la mappa',guideIntro:'Cerca una località, clicca sulla mappa oppure usa la posizione del browser per scegliere il punto centrale. Il cerchio tratteggiato è il raggio di ricerca attivo.',
  guideDataTitle:'Prezzi e classifica',guideData:'Scegli carburante, modalità di servizio e freschezza. I Filtri possono limitare il prezzo massimo e/o la distanza in linea d’aria. Ordina e Mostra agiscono sul sottoinsieme finale usato in modo coerente da mappa, classifica e distribuzione prezzi.',
  guideReadTitle:'Dettagli impianto',guideRead:'Seleziona un marker o una riga della classifica per mettere a fuoco lo stesso impianto. Su desktop si apre il popup della mappa; su schermi stretti il pannello inferiore passa dai risultati ai dettagli. Lo storico resta sempre associato al carburante e alla modalità di servizio selezionati.',
  touchTitle:'Comandi touch',touchHelp:'Trascina la mappa e usa il pinch-to-zoom normalmente. Il pannello inferiore mostra risultati oppure dettagli: usa Indietro per tornare ai risultati, Nascondi per massimizzare la mappa e il controllo in basso a destra per riaprire i risultati. La riga della distribuzione prezzi si espande con un tocco.',
  freshnessHelpTitle:'Freschezza e storico',historyTitle:'Storico',historyHelp:'La freschezza filtra ogni impianto in base all’età del prezzo comunicato. Lo storico locale contiene solo gli snapshot realmente salvati per gli impianti consultati; i giorni mancanti non vengono mai interpolati.',historyHelpStatic:'La freschezza filtra ogni impianto in base all’età del prezzo comunicato. La mappa pubblica espone lo storico mobile generato di 7 giorni; i giorni mancanti nella fonte restano mancanti e non vengono mai interpolati. Lo stato dello snapshot pubblico è mostrato separatamente nella riga di stato superiore.',
  aboutVersionLabel:'Versione',aboutModeLabel:'Modalità dati',aboutSnapshotLabel:'Snapshot prezzi',aboutRegistryLabel:'Anagrafica impianti',aboutGeneratedLabel:'Generato',aboutRefreshLabel:'Aggiornamento',
  aboutModeStatic:'Snapshot pubblico statico',aboutModeLocal:'Runtime Python locale',aboutRefreshStatic:'Programmato alle 09:15 Europe/Rome (GitHub Actions; best-effort)',aboutRefreshLocal:'La sincronizzazione è gestita dal server Python locale',
  aboutProjectTitle:'Progetto',aboutProjectText:'Interfaccia indipendente costruita su dati pubblici ufficiali italiani dei prezzi carburanti. Non è un servizio ufficiale MIMIT e non implica approvazione da parte degli enti fonte.',
  repositoryLink:'Repository GitHub',sourcesLicencesLink:'Fonti e licenze',aboutSourcesTitle:'Fonti principali',aboutLicenceNote:'Dati MIMIT: IODL 2.0. Materiale geografico ISTAT: CC BY 4.0. L’attribuzione di dati e tile della mappa resta agli autori di OpenStreetMap. Consulta Fonti e licenze per i dettagli.',
  stations:'stazioni',hiddenStale:'nascoste perché vecchie',min:'min',median:'mediana',max:'max',snapshot:'snapshot',registry:'anagrafica',
  localHistory:'storico locale',publicHistory:'storico pubblico',snapshotDays:'giorni snapshot',tracked:'impianti tracciati',syncing:'Scarico lo snapshot MIMIT attuale…',
  syncDone:'Snapshot attuale sincronizzato',searchNoResults:'Nessuna località trovata.',searching:'Ricerca…',searchError:'Ricerca località fallita',
  loading:'Carico lo snapshot MIMIT unito in locale…',loadingStatic:'Carico i dati pubblici generati degli impianti…',syncFailed:'Sincronizzazione fallita',freshnessUnknown:'freschezza sconosciuta',less1:'meno di 1 giorno',
  oneDay:'1 giorno fa',daysOld:'{n} giorni fa',stale:'vecchio',snapshotCurrent:'aggiornato',snapshotStale:'vecchio · {n} giorni fa',belowMedian:'{c}¢/L sotto la mediana',aboveMedian:'{c}¢/L sopra la mediana',
  medianPrice:'prezzo mediano',cheaperThan:'più economico del {p}% delle stazioni visibili',lowest:'prezzo più basso del gruppo',highest:'prezzo più alto del gruppo',
  saveFill:'risparmi {v} / {l} L',aboveFill:'{v} sopra mediana / {l} L',atMedian:'alla mediana locale',
  savingFooter:'Il risparmio usa la mediana di tutte le {n} stazioni filtrate per freschezza, per un rifornimento di {l} L. Il costo della deviazione non è incluso.',
  spread:'ampiezza {c}¢/L',histShown:'{shown} mostrate · {total} filtrate',shownOf:'{shown}/{total} mostrate',
  historyFast:'Storico',daysAvailable:'{a}/{r} giorni disponibili · {m} mancanti · nessuna interpolazione',
  localCoverage:'copertura locale stazione: {n} giorni snapshot ({a} → {b})',publicCoverage:'copertura storico pubblico: {n} giorni snapshot ({a} → {b})',noHistory:'Nessuno storico disponibile per questo periodo.',
  station:'ID impianto',communicated:'comunicato',distanceKm:'{n} km',locationDenied:'Posizione non usata',browserGeoUnavailable:'Geolocalizzazione browser non disponibile.',staleCount:'{n} vecchie nascoste'
 }
};

const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const quantile=(a,p)=>{if(!a.length)return NaN;const x=(a.length-1)*p,l=Math.floor(x),h=Math.ceil(x);return l===h?a[l]:a[l]*(h-x)+a[h]*(x-l)};
const fmt=x=>Number.isFinite(x)?`€${x.toFixed(3)}`:'n/a';

function loadPrefs(){
 const defaults={
  fuel:'Benzina',
  mode:'1',
  radius:'5',
  fillLitres:'50',
  maxAgeDays:'3',
  rankSort:'price',
  rankLimit:'all',
  filterPriceEnabled:false,
  filterDistanceEnabled:false,
  filterMaxPrice:null,
  filterMaxDistance:null,
  lat:START.lat,
  lon:START.lon,
  zoom:13,
  locationLabel:'Roma',
  controlsCollapsed:false,
  sidebarCollapsed:false
 };

 try{
  const currentRaw=localStorage.getItem(PREF_KEY);

  if(currentRaw){
   const current={...defaults,...JSON.parse(currentRaw)};

   // V4 is authoritative; old migration sources are no longer needed.
   for(const key of LEGACY_PREF_KEYS){
    localStorage.removeItem(key);
   }

   return current;
  }

  for(const key of LEGACY_PREF_KEYS){
   const raw=localStorage.getItem(key);
   if(!raw)continue;

   const legacy=JSON.parse(raw);
   const migrated={...defaults,...legacy};

   if(legacy.rankLimit==='maxPrice'){
    migrated.rankLimit='all';
    migrated.filterPriceEnabled=true;
    migrated.filterMaxPrice=legacy.showMaxPrice??null;
   }

   if(legacy.rankLimit==='maxDistance'){
    migrated.rankLimit='all';
    migrated.filterDistanceEnabled=true;
    migrated.filterMaxDistance=legacy.showMaxDistance??null;
   }

   // Complete the migration instead of leaving stale legacy state around.
   localStorage.setItem(PREF_KEY,JSON.stringify(migrated));

   for(const oldKey of LEGACY_PREF_KEYS){
    localStorage.removeItem(oldKey);
   }

   return migrated;
  }
 }catch{}

 return defaults;
}
const prefs=loadPrefs();
let lang=localStorage.getItem('fuelMapLang')||(navigator.language&&navigator.language.toLowerCase().startsWith('it')?'it':'en');
let current={lat:Number(prefs.lat)||START.lat,lon:Number(prefs.lon)||START.lon};
let currentLocationLabel=prefs.locationLabel||'Roma';
let center=null,radiusCircle=null,stations=[],shownStations=[],requestSeq=0,markerById=new Map(),lastServerState={},selectedStationId=null,selectionHalo=null,stationRequestKey=null,stationRequestPromise=null,lastHiddenStale=0;
let filterPriceEnabled=!!prefs.filterPriceEnabled,filterDistanceEnabled=!!prefs.filterDistanceEnabled;
let filterMaxPrice=Number.isFinite(Number(prefs.filterMaxPrice))?Number(prefs.filterMaxPrice):null;
let filterMaxDistance=Number.isFinite(Number(prefs.filterMaxDistance))?Number(prefs.filterMaxDistance):null;
let mobileControlsBeforeDetail=null,mobileDistributionOpen=false;

function T(key,vars={}){
 let s=(I18N[lang]&&I18N[lang][key])||I18N.en[key]||key;
 for(const [k,v] of Object.entries(vars))s=s.replaceAll(`{${k}}`,String(v));
 return s
}
function providerTextKey(key){
 const candidate=`${key}Static`;
 return DATA.mode==='static'&&((I18N[lang]&&I18N[lang][candidate])||I18N.en[candidate])?candidate:key
}
function flagSVG(code){
 if(code==='it')return`<svg class="flag-svg" viewBox="0 0 30 20" aria-hidden="true"><rect width="10" height="20" fill="#009246"/><rect x="10" width="10" height="20" fill="#fff"/><rect x="20" width="10" height="20" fill="#ce2b37"/></svg>`;
 return`<svg class="flag-svg" viewBox="0 0 60 40" aria-hidden="true"><rect width="60" height="40" fill="#012169"/><path d="M0 0L60 40M60 0L0 40" stroke="#fff" stroke-width="9"/><path d="M0 0L60 40M60 0L0 40" stroke="#C8102E" stroke-width="4"/><path d="M30 0V40M0 20H60" stroke="#fff" stroke-width="13"/><path d="M30 0V40M0 20H60" stroke="#C8102E" stroke-width="7"/></svg>`
}
function optionText(id){const el=$(id);return el&&el.selectedOptions.length?el.selectedOptions[0].textContent.trim():''}
function conciseLocation(label){
 const parts=String(label||'').split(',').map(x=>x.trim()).filter(Boolean);
 return parts.slice(0,2).join(', ')||`${current.lat.toFixed(4)}, ${current.lon.toFixed(4)}`
}
function updateCollapsedSummary(){
 if(!$('collapsedSummary'))return;
 const freshness=$('maxAgeDays').value==='all'?T('all'):`≤${$('maxAgeDays').value} d`;
 const totalFresh=activeStations().length,shown=shownStations.length||0;
 const line1=conciseLocation(currentLocationLabel);
 const line2=`${optionText('fuel')} · ${optionText('mode')} · ${$('radius').value} km · ${$('fillLitres').value} L`;
 const line3=`${freshness} · ${T('staleCount',{n:lastHiddenStale})} · ${shown}/${totalFresh}`;
 $('collapsedSummary').innerHTML=`<div class="summary-location">${esc(line1)}</div><div class="summary-settings">${esc(line2)}</div><div class="summary-secondary">${esc(line3)}</div>`
}
function persistPrefs(){
 const data={fuel:$('fuel').value,mode:$('mode').value,radius:$('radius').value,fillLitres:$('fillLitres').value,maxAgeDays:$('maxAgeDays').value,rankSort:$('rankSort').value,rankLimit:$('rankLimit').value,filterPriceEnabled,filterDistanceEnabled,filterMaxPrice,filterMaxDistance,lat:current.lat,lon:current.lon,zoom:map.getZoom(),locationLabel:currentLocationLabel,controlsCollapsed:$('controlBody').classList.contains('collapsed'),sidebarCollapsed:document.body.classList.contains('sidebar-collapsed')};
 localStorage.setItem(PREF_KEY,JSON.stringify(data));updateCollapsedSummary()
}
function setControlCollapsed(value,persist=true){
 $('controlBody').classList.toggle('collapsed',value);$('controlPanel').classList.toggle('is-collapsed',value);$('collapseControls').textContent=value?'▾':'▴';
 if(persist)persistPrefs()
}
function setSidebarCollapsed(value,persist=true){
 if(value&&isMobileLayout())closeMobileStationDetail();
 document.body.classList.toggle('sidebar-collapsed',value);resizeMapSoon();if(persist)persistPrefs()
}
function applyPrefs(){
 for(const [id,value] of [['fuel',prefs.fuel],['mode',prefs.mode],['radius',prefs.radius],['fillLitres',prefs.fillLitres],['maxAgeDays',prefs.maxAgeDays],['rankSort',prefs.rankSort],['rankLimit',prefs.rankLimit]]){
  const el=$(id);if(el&&[...el.options||[]].some(o=>o.value===String(value)))el.value=String(value);else if(el&&el.type==='range')el.value=String(value)
 }
 $('radiusValue').textContent=`${$('radius').value} km`;$('fillLitresValue').textContent=`${$('fillLitres').value} L`;$('locationSearch').value=currentLocationLabel;
 $('filterPriceEnabled').checked=filterPriceEnabled;$('filterDistanceEnabled').checked=filterDistanceEnabled;
 setControlCollapsed(Boolean(prefs.controlsCollapsed),false);setSidebarCollapsed(Boolean(prefs.sidebarCollapsed),false);updateCollapsedSummary()
}
function applyLanguage(){
 document.documentElement.lang=lang;
 document.querySelectorAll('[data-i18n]').forEach(el=>el.textContent=T(providerTextKey(el.dataset.i18n)));
 document.querySelectorAll('[data-i18n-placeholder]').forEach(el=>el.placeholder=T(el.dataset.i18nPlaceholder));
 $('langToggle').innerHTML=flagSVG(lang)+`<span>${lang.toUpperCase()}</span>`;
 if($('fitRadiusNav')){$('fitRadiusNav').title=T('fitRadius');$('fitRadiusNav').setAttribute('aria-label',T('fitRadius'))}
 $('helpBtn').title=T('helpTitle');$('helpBtn').setAttribute('aria-label',T('helpTitle'));
 $('closeHelp').title=T('close');$('closeHelp').setAttribute('aria-label',T('close'));
 updateResponsiveControls();renderAbout();
 localStorage.setItem('fuelMapLang',lang);updateCollapsedSummary();render();
 if(lastServerState&&lastServerState.price_date)renderStationStatus(lastServerState)
}

const map=L.map('map',{zoomControl:false}).setView([current.lat,current.lon],Number(prefs.zoom)||13);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
const layer=L.layerGroup().addTo(map);

function niceScaleDistance(meters){
 if(meters<=0)return 100;
 const pow=Math.pow(10,Math.floor(Math.log10(meters))),scaled=meters/pow;
 return (scaled>=5?5:scaled>=2?2:1)*pow
}
function updateCustomScale(){
 const bar=$('customScaleBar'),label=$('customScaleLabel');if(!bar||!label)return;
 const size=map.getSize(),y=Math.round(size.y*.62),x=40;
 const a=map.containerPointToLatLng([x,y]),b=map.containerPointToLatLng([x+100,y]);
 const meters=map.distance(a,b),target=niceScaleDistance(meters);
 const px=Math.max(35,Math.min(120,100*target/meters));
 bar.style.width=`${px}px`;
 label.textContent=target>=1000?`${(target/1000).toLocaleString(undefined,{maximumFractionDigits:1})} km`:`${Math.round(target)} m`
}

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
function fitRadius(){
 if(!radiusCircle)return;
 const zoom=map.getBoundsZoom(radiusCircle.getBounds(),false,L.point(28,28));
 map.setView([current.lat,current.lon],zoom,{animate:true});
 persistPrefs()
}
function parseMimitDate(s){
 if(!s)return null;const x=String(s).trim();const m=x.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?/);
 if(m){const [,d,mo,y,h='0',mi='0',sec='0']=m;return new Date(+y,+mo-1,+d,+h,+mi,+sec)}const d=new Date(x);return Number.isNaN(+d)?null:d
}
function stationAgeDays(s){const d=parseMimitDate(s.updated)||parseMimitDate(s.observed_date);return d?Math.max(0,(Date.now()-d.getTime())/86400000):null}
function romeCalendarDate(now=new Date()){
 const parts=new Intl.DateTimeFormat('en-US',{timeZone:'Europe/Rome',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);
 const values=Object.fromEntries(parts.map(part=>[part.type,part.value]));
 return `${values.year}-${values.month}-${values.day}`
}
function isoCalendarAgeDays(dateText,todayText=romeCalendarDate()){
 const source=String(dateText||'').match(/^(\d{4})-(\d{2})-(\d{2})$/);
 const today=String(todayText||'').match(/^(\d{4})-(\d{2})-(\d{2})$/);
 if(!source||!today)return null;
 const sourceMs=Date.UTC(+source[1],+source[2]-1,+source[3]);
 const todayMs=Date.UTC(+today[1],+today[2]-1,+today[3]);
 return Math.max(0,Math.round((todayMs-sourceMs)/86400000))
}
function staticSnapshotBadge(priceDate){
 if(DATA.mode!=='static')return'';
 const age=isoCalendarAgeDays(priceDate);
 if(age==null)return'';
 if(age<=1)return`<span class="snapshot-health current">${T('snapshotCurrent')}</span>`;
 return`<span class="snapshot-health stale">${T('snapshotStale',{n:age})}</span>`
}
function renderStationStatus(d){
 if(!d||!d.price_date)return;
 const compact=DATA.mode==='static'
  ?`${T('snapshot')} <b>${esc(d.price_date)}</b> ${staticSnapshotBadge(d.price_date)} · ${T('registry')} ${esc(d.registry_date)}`
  :`${T('snapshot')} <b>${esc(d.price_date)}</b> · ${T('registry')} ${esc(d.registry_date)}`+(d.warning?`<br/><span class="warn">${esc(d.warning)}</span>`:'');
 if(isMobileLayout()){$('status').innerHTML=compact;return}
 $('status').innerHTML=DATA.mode==='static'
  ?`${T('snapshot')} <b>${esc(d.price_date)}</b> ${staticSnapshotBadge(d.price_date)} · ${T('registry')} ${esc(d.registry_date)} · ${T('publicHistory')}: ${d.history_days||0} ${T('snapshotDays')}`
  :`${T('snapshot')} <b>${esc(d.price_date)}</b> · ${T('registry')} ${esc(d.registry_date)} · ${T('localHistory')}: ${d.history_days||0} ${T('snapshotDays')} · ${d.tracked_station_rows||0} ${T('tracked')}`+(d.warning?`<br/><span class="warn">${esc(d.warning)}</span>`:'')
}
function ageText(days){if(days==null||!Number.isFinite(days))return T('freshnessUnknown');if(days<1)return T('less1');if(days<2)return T('oneDay');return T('daysOld',{n:Math.floor(days)})}
function ageClass(days){if(days==null)return'mid';if(days<=1)return'good';if(days<=3)return'mid';return'old'}
function activeStations(){const raw=$('maxAgeDays').value;if(raw==='all')return stations;const max=+raw;return stations.filter(s=>{const a=stationAgeDays(s);return a!=null&&a<=max})}
function cheaperThanPct(price,visible){return visible.length?100*visible.filter(s=>Number.isFinite(s.price)&&s.price>price).length/visible.length:null}
function percentileText(price,visible){const p=cheaperThanPct(price,visible);if(p==null)return'';if(p<.5)return T('highest');if(p>99.5)return T('lowest');return T('cheaperThan',{p:Math.round(p)})}
function centsValue(x){return(x*100).toFixed(1)}

function configureAutoLabels(visible){
 const permanent=map.getZoom()>=13||visible.length<=12;
 for(const s of visible){
  const marker=markerById.get(String(s.id));if(!marker)continue;
  marker.unbindTooltip();
  marker.bindTooltip(`<span class="price-label">${fmt(s.price)}</span>`,{permanent,direction:'top',offset:[0,-7],className:'price-tip',opacity:1})
 }
}
function applySelectionStyles(scrollRank=false){
 if(selectionHalo){layer.removeLayer(selectionHalo);selectionHalo=null}
 markerById.forEach(marker=>{marker.setRadius(9);marker.setStyle({weight:.8,color:'#222'})});
 const marker=selectedStationId==null?null:markerById.get(String(selectedStationId));
 if(marker){
  selectionHalo=L.circleMarker(marker.getLatLng(),{radius:15,color:'#0072B2',weight:3,opacity:.32,fill:false,interactive:false}).addTo(layer);
  selectionHalo.bringToFront();
  marker.setRadius(10);
  marker.bringToFront()
 }
 document.querySelectorAll('.rank-item').forEach(el=>el.classList.toggle('selected',String(el.dataset.id)===String(selectedStationId)));
 if(scrollRank&&selectedStationId!=null){const row=document.querySelector(`.rank-item[data-id="${CSS.escape(String(selectedStationId))}"]`);if(row)row.scrollIntoView({block:'nearest',behavior:'smooth'})}
}
function selectStation(id,{openPopup=false,pan=false,scrollRank=true}={}){
 selectedStationId=id==null?null:String(id);applySelectionStyles(scrollRank);
 const marker=markerById.get(String(id));if(marker){if(pan)map.panTo(marker.getLatLng(),{animate:true});if(openPopup)marker.openPopup()}
}

function renderDistribution(visible,median,totalFiltered){
 const box=$('distChart'),spread=$('distSpread');$('distNote').textContent=T('histShown',{shown:visible.length,total:totalFiltered});
 const vals=visible.map(s=>s.price).filter(Number.isFinite).sort((a,b)=>a-b);if(!vals.length){box.innerHTML='';spread.textContent='';return}
 const min=vals[0],max=vals.at(-1),range=Math.max(.001,max-min),bins=Math.min(12,Math.max(5,Math.ceil(Math.sqrt(vals.length)))),counts=Array(bins).fill(0);
 vals.forEach(v=>{let i=Math.floor((v-min)/range*bins);if(i>=bins)i=bins-1;counts[i]++});
 const W=340,H=63,PL=5,PR=5,PT=5,PB=16,UW=W-PL-PR,UH=H-PT-PB,mxCount=Math.max(...counts,1),bw=UW/bins;
 const bars=counts.map((c,i)=>{const h=UH*c/mxCount,x=PL+i*bw+1,y=PT+UH-h;return`<rect x="${x}" y="${y}" width="${Math.max(1,bw-2)}" height="${h}" fill="#858b90" opacity=".72"><title>${c}</title></rect>`}).join('');
 const mx=PL+(median-min)/range*UW;box.innerHTML=`<svg width="100%" height="${H}" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${bars}<line x1="${mx}" y1="${PT}" x2="${mx}" y2="${PT+UH}" stroke="#222" stroke-width="1.2" stroke-dasharray="3 2"/><text x="${PL}" y="${H-3}" class="dist-axis">${fmt(min)}</text><text x="${W-PR}" y="${H-3}" text-anchor="end" class="dist-axis">${fmt(max)}</text></svg>`;spread.textContent=T('spread',{c:centsValue(max-min)})
}
function spark(points){
 if(!points.length)return`<div class="spark-empty">${T('noHistory')}</div>`;
 const W=280,H=76,P=9,vals=points.map(x=>+x.price),min=Math.min(...vals),max=Math.max(...vals),span=Math.max(.001,max-min),start=new Date(points[0].date+'T00:00:00'),end=new Date(points.at(-1).date+'T00:00:00'),dspan=Math.max(1,(end-start)/86400000);
 const xy=points.map(x=>{const d=new Date(x.date+'T00:00:00');return{x:P+((d-start)/86400000)/dspan*(W-2*P),y:H-P-(+x.price-min)/span*(H-2*P),...x}});let segments=[],seg=[];
 xy.forEach((p,i)=>{if(i&&(new Date(p.date)-new Date(xy[i-1].date))/86400000>1){if(seg.length)segments.push(seg);seg=[]}seg.push(p)});if(seg.length)segments.push(seg);
 const lines=segments.map(s=>`<polyline fill="none" stroke="#222" stroke-width="1.6" points="${s.map(p=>`${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')}"/>`).join(''),dots=xy.map(p=>`<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="2" fill="#0072B2"><title>${p.date}: ${fmt(+p.price)}</title></circle>`).join('');
 return`<svg width="100%" height="${H}" viewBox="0 0 ${W} ${H}"><line x1="${P}" y1="${H-P}" x2="${W-P}" y2="${H-P}" stroke="#bbb" stroke-dasharray="2 3"/>${lines}${dots}<text x="${P+2}" y="11" font-size="9">${fmt(max)}</text><text x="${P+2}" y="${H-11}" font-size="9">${fmt(min)}</text></svg>`
}
async function loadHistory(box,id,fuel,self,days){
 box.innerHTML='<div class="spark-empty">…</div>';
 try{const d=await DATA.getHistory({id,fuel,self,days});const coverageKey=DATA.mode==='static'?'publicCoverage':'localCoverage';box.innerHTML=spark(d.points)+`<div class="spark-meta">${T('daysAvailable',{a:d.observed_days,r:d.requested_days,m:d.missing_days})}</div>`+(d.available_total_days?`<div class="spark-meta">${T(coverageKey,{n:d.available_total_days,a:d.available_start,b:d.available_end})}</div>`:'')}catch(e){box.innerHTML=`<div class="spark-empty">${esc(e.message)}</div>`}
}
function activateHistory(root){
 if(!root)return;
 const box=root.querySelector('[data-history-id]');if(!box)return;
 const id=box.dataset.historyId,f=box.dataset.fuel,self=box.dataset.self==='1';
 const defaultDays=(DATA.capabilities.historyDays||[7])[0]||7;
 loadHistory(box,id,f,self,defaultDays);
 root.querySelectorAll('[data-days]').forEach(b=>b.addEventListener('click',()=>loadHistory(box,id,f,self,+b.dataset.days)))
}
function popupHtml(s){
 const key=`hist-${String(s.id).replace(/[^a-zA-Z0-9_-]/g,'')}-${Math.random().toString(36).slice(2,6)}`;
 const historyDays=DATA.capabilities.historyDays||[];
 const historyHtml=DATA.capabilities.history&&historyDays.length?`<div class="history-head"><b>${T('historyFast')}</b><span class="history-btns">${historyDays.map(days=>`<button data-days="${days}">${days}d</button>`).join('')}</span></div><div id="${key}" data-history-id="${esc(s.id)}" data-fuel="${esc(s.fuel)}" data-self="${s.isSelf?1:0}"></div>`:'';
 return`<div class="popup-price">${fmt(s.price)}</div><div><b>${esc(s.fuel)}</b> · ${s.isSelf?T('self'):T('served')} · ${T('distanceKm',{n:s.distance_km.toFixed(1)})}</div><div class="popup-meta">${T('station')} ${esc(s.id)}<br/>${esc(s.address)}<br/>${T('snapshot')}: ${esc(s.observed_date)}${s.updated?`<br/>${T('communicated')}: ${esc(s.updated)}`:''}<br/><span class="fresh ${ageClass(stationAgeDays(s))}">${ageText(stationAgeDays(s))}</span></div>${historyHtml}`
}
function closeMobileStationDetail({restoreControls=true}={}){
 const detail=$('mobileStationDetail');if(!detail)return;
 detail.hidden=true;detail.innerHTML='';
 document.body.classList.remove('mobile-detail-open');
 if(restoreControls&&mobileControlsBeforeDetail!==null){
  setControlCollapsed(mobileControlsBeforeDetail,false);
  mobileControlsBeforeDetail=null
 }
 resizeMapSoon()
}
function renderMobileStationDetail(){
 if(!isMobileLayout()||selectedStationId==null){closeMobileStationDetail();return}
 const station=shownStations.find(s=>String(s.id)===String(selectedStationId));
 if(!station){closeMobileStationDetail();return}
 const detail=$('mobileStationDetail');
 detail.hidden=false;
 document.body.classList.add('mobile-detail-open');
 detail.innerHTML=`<div class="mobile-detail-head"><button class="small-btn" id="mobileDetailBack" type="button" title="${esc(T('backToResults'))}" aria-label="${esc(T('backToResults'))}">‹</button><strong>${esc(T('stationDetails'))}</strong><button class="small-btn" id="mobileDetailHide" type="button" title="${esc(T('hidePanel'))}" aria-label="${esc(T('hidePanel'))}">⌄</button></div><div class="mobile-detail-body">${popupHtml(station)}</div>`;
 $('mobileDetailBack').addEventListener('click',closeMobileStationDetail);
 $('mobileDetailHide').addEventListener('click',()=>setSidebarCollapsed(true));
 activateHistory(detail);
 resizeMapSoon()
}
function openMobileStationDetail(id,{pan=true}={}){
 selectedStationId=id==null?null:String(id);
 setSidebarCollapsed(false,false);
 if(mobileControlsBeforeDetail===null){
  mobileControlsBeforeDetail=$('controlBody').classList.contains('collapsed');
  setControlCollapsed(true,false)
 }
 applySelectionStyles(true);
 const marker=markerById.get(String(id));
 if(marker&&pan)map.panTo(marker.getLatLng(),{animate:true});
 renderMobileStationDetail()
}
function openStation(id){
 if(isMobileLayout()){openMobileStationDetail(id,{pan:true});return}
 selectStation(id,{pan:true,openPopup:true,scrollRank:true})
}
function updateDistributionState(){
 const box=$('distBox'),toggle=$('distToggle');
 if(!box||!toggle)return;
 const expanded=!isMobileLayout()||mobileDistributionOpen;
 box.classList.toggle('is-open',isMobileLayout()&&mobileDistributionOpen);
 toggle.setAttribute('aria-expanded',String(expanded));
 const icon=toggle.querySelector('.dist-toggle-icon');
 if(icon)icon.textContent=mobileDistributionOpen?'⌃':'⌄'
}
function formatAboutTime(value){
 if(!value)return'—';
 const date=new Date(value);if(Number.isNaN(date.getTime()))return String(value);
 return new Intl.DateTimeFormat(lang==='it'?'it-IT':'en-GB',{
  dateStyle:'medium',timeStyle:'short',timeZone:'Europe/Rome'
 }).format(date)
}
function renderAbout(){
 if(!$('aboutVersion'))return;
 $('aboutVersion').textContent=APP_VERSION;
 $('aboutMode').textContent=T(DATA.mode==='static'?'aboutModeStatic':'aboutModeLocal');
 $('aboutSnapshot').textContent=lastServerState.price_date||'—';
 $('aboutRegistry').textContent=lastServerState.registry_date||'—';
 $('aboutGenerated').textContent=lastServerState.generated_at?formatAboutTime(lastServerState.generated_at):'—';
 $('aboutRefresh').textContent=T(DATA.mode==='static'?'aboutRefreshStatic':'aboutRefreshLocal')
}
function setHelpTab(tab){
 const active=tab==='about'?'about':'guide';
 const guide=active==='guide';
 $('helpGuidePanel').hidden=!guide;$('helpAboutPanel').hidden=guide;
 $('helpGuideTab').classList.toggle('selected',guide);$('helpAboutTab').classList.toggle('selected',!guide);
 $('helpGuideTab').setAttribute('aria-selected',String(guide));$('helpAboutTab').setAttribute('aria-selected',String(!guide));
 if(!guide)renderAbout()
}
function openHelp(tab='guide'){
 setHelpTab(tab);$('helpModal').classList.add('show');setTimeout(()=>$('closeHelp').focus(),0)
}
function closeHelpModal(){
 $('helpModal').classList.remove('show')
}
function updateResponsiveControls(){
 const mobile=isMobileLayout();
 $('hideSidebar').textContent=mobile?'⌄':'›';
 $('showSidebar').textContent=mobile?'⌃':'‹';
 $('hideSidebar').title=T('hidePanel');$('hideSidebar').setAttribute('aria-label',T('hidePanel'));
 $('showSidebar').title=T('showResults');$('showSidebar').setAttribute('aria-label',T('showResults'));
 updateDistributionState()
}


function updateFilterControls(base){
 const prices=base.map(s=>s.price).filter(Number.isFinite).sort((a,b)=>a-b);
 const pSlider=$('filterPriceSlider'),dSlider=$('filterDistanceSlider');
 $('filterPriceEnabled').checked=filterPriceEnabled;$('filterDistanceEnabled').checked=filterDistanceEnabled;
 if(prices.length){
  const pMin=Math.floor(prices[0]*1000)/1000,pMax=Math.ceil(prices.at(-1)*1000)/1000;
  if(filterMaxPrice==null)filterMaxPrice=pMax;
  filterMaxPrice=Math.max(pMin,Math.min(pMax,filterMaxPrice));
  pSlider.min=pMin.toFixed(3);pSlider.max=pMax.toFixed(3);pSlider.step='0.001';pSlider.value=filterMaxPrice.toFixed(3);
  $('filterPriceValue').textContent=fmt(filterMaxPrice)
 }
 const dMax=Math.max(1,+$('radius').value);
 if(filterMaxDistance==null)filterMaxDistance=dMax;
 filterMaxDistance=Math.max(.5,Math.min(dMax,filterMaxDistance));
 dSlider.min='0.5';dSlider.max=dMax.toFixed(1);dSlider.step='0.5';dSlider.value=filterMaxDistance.toFixed(1);
 $('filterDistanceValue').textContent=`${filterMaxDistance.toFixed(1)} km`;
 const count=(filterPriceEnabled?1:0)+(filterDistanceEnabled?1:0);
 $('filterCount').textContent=count?String(count):'';renderFilterChips()
}
function renderFilterChips(){
 const chips=[];
 if(filterPriceEnabled)chips.push(`<span class="filter-chip">≤ ${fmt(filterMaxPrice)}</span>`);
 if(filterDistanceEnabled)chips.push(`<span class="filter-chip">≤ ${filterMaxDistance.toFixed(1)} km</span>`);
 $('activeFilterChips').innerHTML=chips.join('')
}
function applyOptionalFilters(base){
 return base.filter(s=>(!filterPriceEnabled||s.price<=filterMaxPrice+1e-9)&&(!filterDistanceEnabled||s.distance_km<=filterMaxDistance+1e-9))
}
function sortedStations(filtered,referenceMedian){
 const mode=$('rankSort').value;
 return [...filtered].sort((a,b)=>{
  if(mode==='distance')return a.distance_km-b.distance_km||a.price-b.price;
  if(mode==='saving')return a.price-b.price||a.distance_km-b.distance_km;
  return a.price-b.price||a.distance_km-b.distance_km
 })
}
function shownStationSubset(filtered,referenceMedian){
 const ranked=sortedStations(filtered,referenceMedian),limit=$('rankLimit').value;
 return limit==='all'?ranked:ranked.slice(0,+limit)
}
function renderRanking(visible,filtered,referenceMedian){
 const fill=+$('fillLitres').value;
 renderDistribution(visible,quantile(visible.map(s=>s.price).filter(Number.isFinite).sort((a,b)=>a-b),.5),filtered.length);
 $('rankCount').textContent=visible.length===filtered.length?`${visible.length} ${T('stations')}`:T('shownOf',{shown:visible.length,total:filtered.length});
 $('rankFooter').textContent=T('savingFooter',{l:fill,n:filtered.length});
 if(!visible.length){$('rankList').innerHTML=`<div class="rank-empty">0 ${T('stations')}</div>`;return}
 $('rankList').innerHTML=visible.map((s,i)=>{
  const delta=s.price-referenceMedian;
  const saving=(referenceMedian-s.price)*fill;
  const ageDays=stationAgeDays(s);
  const percentileLabel=percentileText(s.price,filtered);
  const deltaText=Math.abs(delta)<.0005?T('medianPrice'):delta<0?T('belowMedian',{c:centsValue(Math.abs(delta))}):T('aboveMedian',{c:centsValue(delta)});
  const savingText=saving>.005?T('saveFill',{v:fmt(saving),l:fill}):saving<-.005?T('aboveFill',{v:fmt(Math.abs(saving)),l:fill}):T('atMedian');
  return`<div class="rank-item${String(s.id)===String(selectedStationId)?' selected':''}" data-id="${esc(s.id)}"><div class="rank-num">${i+1}</div><div><div class="rank-price">${fmt(s.price)}</div><div class="rank-detail">${esc(s.address||`#${s.id}`)}</div><div class="rank-delta">${deltaText}</div><div class="rank-percentile">${esc(percentileLabel)}</div><div class="fresh ${ageClass(ageDays)}">${ageText(ageDays)}${ageDays!=null&&ageDays>3?`<span class="stale-badge">${T('stale')}</span>`:''}</div></div><div class="rank-right"><div class="rank-distance">${T('distanceKm',{n:s.distance_km.toFixed(1)})}</div><div class="rank-saving">${savingText}</div></div></div>`
 }).join('');
 $('rankList').querySelectorAll('.rank-item').forEach(el=>el.addEventListener('click',()=>openStation(el.dataset.id)))
}
function render(){
 if(!$('rankList'))return;
 layer.clearLayers();markerById.clear();selectionHalo=null;
 const freshnessFiltered=activeStations();
 updateFilterControls(freshnessFiltered);
 const filtered=applyOptionalFilters(freshnessFiltered);
 const filteredValues=filtered.map(s=>s.price).filter(Number.isFinite).sort((a,b)=>a-b);
 const referenceMedian=quantile(filteredValues,.5);
 const visible=shownStationSubset(filtered,referenceMedian);
 shownStations=visible;
 const values=visible.map(s=>s.price).filter(Number.isFinite).sort((a,b)=>a-b);
 const lo=quantile(values,.05),hi=quantile(values,.95),shownMedian=quantile(values,.5);

 if(selectedStationId!=null&&!visible.some(s=>String(s.id)===String(selectedStationId))){selectedStationId=null;closeMobileStationDetail()}

 visible.forEach(s=>{
  const marker=L.circleMarker([s.lat,s.lon],{radius:9,color:'#222',weight:.8,fillColor:markerColor(s.price,lo,hi),fillOpacity:.95,bubblingMouseEvents:false}).addTo(layer);
  marker._station=s;
  markerById.set(String(s.id),marker);
  if(isMobileLayout()){
   marker.on('click',()=>openMobileStationDetail(s.id,{pan:false}))
  }else{
   marker.bindPopup(popupHtml(s),{maxWidth:330,autoPan:true,autoPanPaddingTopLeft:L.point(25,190),autoPanPaddingBottomRight:L.point(25,35)});
   marker.on('click',()=>selectStation(s.id,{scrollRank:true}));
   marker.on('popupopen',e=>{
    selectStation(s.id,{scrollRank:true});
    activateHistory(e.popup.getElement())
   })
  }
 });

 configureAutoLabels(visible);
 applySelectionStyles(false);

 $('lmin').textContent=values.length?fmt(values[0]):'—';
 $('lmid').textContent=values.length?fmt(shownMedian):'—';
 $('lmax').textContent=values.length?fmt(values.at(-1)):'—';

 lastHiddenStale=stations.length-freshnessFiltered.length;

 const shownLabel=visible.length===filtered.length
   ? `${visible.length} ${T('stations')}`
   : T('shownOf',{shown:visible.length,total:filtered.length});

 $('stats').innerHTML=values.length
   ? `<span class="stat stat-primary">${shownLabel}</span>
      ${lastHiddenStale?`<span class="stat stat-stale">${lastHiddenStale} ${T('hiddenStale')}</span>`:''}
      <span class="stat stat-price">${T('min')} ${fmt(values[0])}</span>
      <span class="stat stat-price">${T('median')} ${fmt(shownMedian)}</span>
      <span class="stat stat-price">${T('max')} ${fmt(values.at(-1))}</span>`
   : `<span class="stat stat-primary">0 ${T('stations')}</span>`;

 renderRanking(visible,filtered,referenceMedian);
 applySelectionStyles(false);
 if(document.body.classList.contains('mobile-detail-open'))renderMobileStationDetail();
 updateCollapsedSummary()
}

async function loadStations(){
 const fuel=$('fuel').value,self=$('mode').value,radius=$('radius').value;
 const key=`${current.lat.toFixed(7)}|${current.lon.toFixed(7)}|${radius}|${fuel}|${self}`;
 if(stationRequestPromise&&stationRequestKey===key)return stationRequestPromise;
 const seq=++requestSeq;$('status').textContent=T(DATA.mode==='static'?'loadingStatic':'loading');
 stationRequestKey=key;
 const task=(async()=>{
  try{
   const d=await DATA.getStations({lat:current.lat,lon:current.lon,radius,fuel,self});
   if(seq!==requestSeq)return;
   stations=d.stations||[];lastServerState=d;render();renderStationStatus(d);renderAbout();
   persistPrefs();
  }catch(e){
   if(seq!==requestSeq)return;
   stations=[];render();$('status').innerHTML=`<span class="warn">${esc(e.message)}</span>`;
  }finally{
   if(stationRequestKey===key){stationRequestKey=null;stationRequestPromise=null}
  }
 })();
 stationRequestPromise=task;
 return task
}
async function syncNow(){
 if(!DATA.capabilities.sync)return;
 const b=$('sync');b.disabled=true;$('status').textContent=T('syncing');try{const d=await DATA.syncCurrent();$('status').textContent=`${T('syncDone')}: ${d.price_date} · ${T('localHistory')}: ${d.history_days||0} ${T('snapshotDays')}`;await loadStations()}catch(e){$('status').innerHTML=`<span class="warn">${T('syncFailed')}: ${esc(e.message)}</span>`}finally{b.disabled=false}
}
function relocate(lat,lon,zoom=13,reload=true,label=null){selectedStationId=null;closeMobileStationDetail();current={lat,lon};currentLocationLabel=label||`${lat.toFixed(4)}, ${lon.toFixed(4)}`;setSearchGeometry(lat,lon);map.setView([lat,lon],zoom);$('locationSearch').value=currentLocationLabel;persistPrefs();if(reload)loadStations()}
function useLocation(){if(!navigator.geolocation){$('status').textContent=T('browserGeoUnavailable');return}navigator.geolocation.getCurrentPosition(p=>relocate(p.coords.latitude,p.coords.longitude,14,true,T('currentLocation')),e=>$('status').textContent=`${T('locationDenied')}: ${e.message}`)}
async function searchLocation(query){
 const results=$('searchResults');results.classList.add('show');results.innerHTML=`<div class="search-item">${T('searching')}</div>`;
 try{const d=await DATA.searchPlaces({query,lang});if(!d.results.length){results.innerHTML=`<div class="search-item">${T('searchNoResults')}</div>`;return}results.innerHTML=d.results.map((x,i)=>`<div class="search-item" data-i="${i}">${esc(x.display_name)}</div>`).join('');results.querySelectorAll('.search-item[data-i]').forEach(el=>el.addEventListener('click',()=>{const x=d.results[+el.dataset.i];results.classList.remove('show');relocate(x.lat,x.lon,14,true,x.display_name)}))}catch(e){results.innerHTML=`<div class="search-item">${T('searchError')}: ${esc(e.message)}</div>`}
}
function pan(dir){const step=170,delta={up:[0,-step],down:[0,step],left:[-step,0],right:[step,0]}[dir];if(delta)map.panBy(delta,{animate:true})}
function resizeMapSoon(){map.invalidateSize({pan:false});setTimeout(()=>map.invalidateSize({pan:false}),220)}

function applyProviderCapabilities(){
 $('sync').hidden=!DATA.capabilities.sync;
 $('searchForm').hidden=!DATA.capabilities.search
}

function bindEvents(){
 document.querySelectorAll('[data-pan]').forEach(b=>b.addEventListener('click',()=>pan(b.dataset.pan)));document.querySelector('[data-zoom="in"]').addEventListener('click',()=>map.zoomIn());document.querySelector('[data-zoom="out"]').addEventListener('click',()=>map.zoomOut());document.querySelector('[data-recenter]').addEventListener('click',()=>map.setView([current.lat,current.lon],map.getZoom(),{animate:true}));$('fitRadiusNav').addEventListener('click',fitRadius);
 $('radius').addEventListener('input',e=>{$('radiusValue').textContent=`${e.target.value} km`;updateRadiusCircle();persistPrefs()});$('radius').addEventListener('change',loadStations);
 $('fillLitres').addEventListener('input',e=>{$('fillLitresValue').textContent=`${e.target.value} L`;persistPrefs();render()});
 $('fuel').addEventListener('change',()=>{persistPrefs();loadStations()});$('mode').addEventListener('change',()=>{persistPrefs();loadStations()});$('maxAgeDays').addEventListener('change',()=>{persistPrefs();render()});
 $('refresh').addEventListener('click',loadStations);if(DATA.capabilities.sync)$('sync').addEventListener('click',syncNow);$('locate').addEventListener('click',useLocation);$('rankSort').addEventListener('change',()=>{persistPrefs();render()});$('rankLimit').addEventListener('change',()=>{persistPrefs();render()});
 $('filterToggle').addEventListener('click',()=>{$('filterPopover').hidden=!$('filterPopover').hidden});
 $('distToggle').addEventListener('click',()=>{mobileDistributionOpen=!mobileDistributionOpen;updateDistributionState()});
 $('filterPriceEnabled').addEventListener('change',()=>{filterPriceEnabled=$('filterPriceEnabled').checked;persistPrefs();render()});
 $('filterDistanceEnabled').addEventListener('change',()=>{filterDistanceEnabled=$('filterDistanceEnabled').checked;persistPrefs();render()});
 $('filterPriceSlider').addEventListener('input',()=>{filterMaxPrice=+$('filterPriceSlider').value;filterPriceEnabled=true;$('filterPriceEnabled').checked=true;persistPrefs();render()});
 $('filterDistanceSlider').addEventListener('input',()=>{filterMaxDistance=+$('filterDistanceSlider').value;filterDistanceEnabled=true;$('filterDistanceEnabled').checked=true;persistPrefs();render()});
 $('filterReset').addEventListener('click',()=>{filterPriceEnabled=false;filterDistanceEnabled=false;filterMaxPrice=null;filterMaxDistance=null;persistPrefs();render()});
 $('searchForm').addEventListener('submit',e=>{e.preventDefault();const q=$('locationSearch').value.trim();if(q)searchLocation(q)});
 $('langToggle').addEventListener('click',()=>{lang=lang==='en'?'it':'en';applyLanguage()});
 $('helpBtn').addEventListener('click',()=>openHelp('guide'));$('closeHelp').addEventListener('click',closeHelpModal);$('helpModal').addEventListener('click',e=>{if(e.target===$('helpModal'))closeHelpModal()});
 document.querySelectorAll('[data-help-tab]').forEach(button=>button.addEventListener('click',()=>setHelpTab(button.dataset.helpTab)));
 $('collapseControls').addEventListener('click',()=>{setControlCollapsed(!$('controlBody').classList.contains('collapsed'));if(document.body.classList.contains('mobile-detail-open'))mobileControlsBeforeDetail=null});$('hideSidebar').addEventListener('click',()=>setSidebarCollapsed(true));$('showSidebar').addEventListener('click',()=>setSidebarCollapsed(false));
 map.on('click',e=>relocate(e.latlng.lat,e.latlng.lng,map.getZoom(),true));map.on('zoomend',()=>{configureAutoLabels(shownStations);updateCustomScale();persistPrefs()});map.on('moveend',updateCustomScale);map.on('resize',updateCustomScale);
 document.addEventListener('keydown',e=>{const tag=(e.target&&e.target.tagName||'').toLowerCase(),typing=tag==='input'||tag==='select'||tag==='textarea';if(e.key==='Escape'){closeHelpModal();$('searchResults').classList.remove('show');closeMobileStationDetail();map.closePopup();return}if(typing)return;const k=e.key.toLowerCase();if(k==='/'){e.preventDefault();$('locationSearch').focus();return}if(k==='h'||e.key==='?'){openHelp('guide');return}if(k==='r'){loadStations();return}if(k==='l'){useLocation();return}if(e.key==='0'){map.setView([current.lat,current.lon],map.getZoom(),{animate:true});return}if(e.key==='+'||e.key==='='){map.zoomIn();return}if(e.key==='-'){map.zoomOut();return}const keyDir={w:'up',arrowup:'up',s:'down',arrowdown:'down',a:'left',arrowleft:'left',d:'right',arrowright:'right'}[k];if(keyDir){e.preventDefault();pan(keyDir)}});
 document.addEventListener('click',e=>{if(!e.target.closest('.search-row'))$('searchResults').classList.remove('show');if(!e.target.closest('#filterPopover')&&!e.target.closest('#filterToggle'))$('filterPopover').hidden=true})
 MOBILE_LAYOUT.addEventListener('change',()=>{mobileDistributionOpen=false;closeMobileStationDetail();updateResponsiveControls();render();if(lastServerState&&lastServerState.price_date)renderStationStatus(lastServerState);resizeMapSoon()})
}

applyPrefs();applyProviderCapabilities();setSearchGeometry(current.lat,current.lon);bindEvents();updateResponsiveControls();applyLanguage();updateCustomScale();loadStations();
