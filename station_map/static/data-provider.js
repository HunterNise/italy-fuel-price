(()=>{
'use strict';

const config={mode:'local',dataBase:'./data',...(window.FUEL_MAP_CONFIG||{})};

function errorMessage(data,response){
 if(data&&data.error)return String(data.error);
 return `HTTP ${response.status}`;
}
async function fetchJson(url,{cache='default'}={}){
 const response=await fetch(url,{cache});
 let data;
 try{data=await response.json()}
 catch{throw Error(`Invalid JSON from ${url}`)}
 if(!response.ok||data&&data.ok===false)throw Error(errorMessage(data,response));
 return data
}
function baseUrl(path){
 const root=String(config.dataBase||'./data').replace(/\/+$/,'');
 return `${root}/${String(path).replace(/^\/+/,'')}`
}
function versioned(path,version){
 const url=baseUrl(path);
 return version?`${url}?v=${encodeURIComponent(version)}`:url
}
function normalizeText(value){
 const plain=String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('it').replaceAll('ß','ss');
 return plain.replace(/[^a-z0-9]+/g,' ').trim().replace(/\s+/g,' ')
}
function boolFlag(value){return value===true||value===1||value==='1'}
function haversineKm(lat1,lon1,lat2,lon2){
 const earth=6371.0088;
 const p1=lat1*Math.PI/180,p2=lat2*Math.PI/180;
 const dlat=(lat2-lat1)*Math.PI/180,dlon=(lon2-lon1)*Math.PI/180;
 const h=Math.sin(dlat/2)**2+Math.cos(p1)*Math.cos(p2)*Math.sin(dlon/2)**2;
 return 2*earth*Math.asin(Math.sqrt(h))
}
function bboxCellKeys(lat,lon,radius,size,available){
 const dlat=radius/111.0;
 const dlon=radius/(111.0*Math.max(.2,Math.cos(lat*Math.PI/180)));
 const imin=Math.floor((lat-dlat)/size),imax=Math.floor((lat+dlat)/size);
 const jmin=Math.floor((lon-dlon)/size),jmax=Math.floor((lon+dlon)/size);
 const out=[];
 for(let i=imin;i<=imax;i++){
  for(let j=jmin;j<=jmax;j++){
   const key=`${i}_${j}`;
   if(!available||available.has(key))out.push(key)
  }
 }
 return out
}

function createLocalProvider(){
 return{
  mode:'local',
  capabilities:{search:true,sync:true,history:true,historyDays:[7,30,90]},
  async getStations({lat,lon,radius,fuel,self}){
   const q=new URLSearchParams({lat,lon,radius,fuel,self:boolFlag(self)?1:0});
   return fetchJson(`/api/stations?${q}`,{cache:'no-store'})
  },
  async getHistory({id,fuel,self,days}){
   const q=new URLSearchParams({id,fuel,self:boolFlag(self)?1:0,days});
   return fetchJson(`/api/history?${q}`,{cache:'no-store'})
  },
  async searchPlaces({query,lang}){
   const q=new URLSearchParams({q:query,lang});
   return fetchJson(`/api/geocode?${q}`,{cache:'no-store'})
  },
  async syncCurrent(){
   return fetchJson('/api/sync',{cache:'no-store'})
  }
 }
}

function createStaticProvider(){
 let metadataPromise=null,placesPromise=null,localitiesPromise=null,historyMetadataPromise=null;
 const currentCells=new Map(),historyCells=new Map(),stationCellById=new Map();

 async function metadata(){
  if(!metadataPromise)metadataPromise=fetchJson(baseUrl('metadata.json'),{cache:'no-store'});
  return metadataPromise
 }
 async function places(){
  if(!placesPromise){
   placesPromise=(async()=>{
    const meta=await metadata();
    const path=meta.places&&meta.places.path||'places.json';
    return fetchJson(versioned(path,meta.generated_at))
   })()
  }
  return placesPromise
 }
 async function localities(){
  if(!localitiesPromise){
   localitiesPromise=(async()=>{
    const meta=await metadata();
    if(!meta.localities||!meta.localities.enabled)return{localities:[]};
    return fetchJson(versioned(meta.localities.path||'localities.json',meta.generated_at))
   })()
  }
  return localitiesPromise
 }
 async function currentCell(key){
  if(!currentCells.has(key)){
   currentCells.set(key,(async()=>{
    const meta=await metadata();
    const payload=await fetchJson(versioned(`cells/${key}.json`,meta.generated_at));
    for(const station of payload.stations||[])stationCellById.set(String(station.id),key);
    return payload
   })())
  }
  return currentCells.get(key)
 }
 async function historyMetadata(){
  if(!historyMetadataPromise){
   historyMetadataPromise=(async()=>{
    const meta=await metadata();
    if(!meta.history||!meta.history.enabled)return null;
    return fetchJson(versioned(meta.history.metadata_path||'history/metadata.json',meta.generated_at))
   })()
  }
  return historyMetadataPromise
 }
 async function historyCell(key){
  if(!historyCells.has(key)){
   historyCells.set(key,(async()=>{
    const meta=await metadata();
    return fetchJson(versioned(`history/cells/${key}.json`,meta.generated_at))
   })())
  }
  return historyCells.get(key)
 }

 return{
  mode:'static',
  capabilities:{search:true,sync:false,history:true,historyDays:[7]},
  async getStations({lat,lon,radius,fuel,self}){
   lat=Number(lat);lon=Number(lon);radius=Number(radius);
   const meta=await metadata();
   const size=Number(meta.grid&&meta.grid.size_degrees)||.5;
   const available=new Set(meta.grid&&meta.grid.cells||[]);
   const keys=bboxCellKeys(lat,lon,radius,size,available);
   const payloads=await Promise.all(keys.map(currentCell));
   const stations=[];
   for(const payload of payloads){
    for(const station of payload.stations||[]){
     const price=(station.prices||[]).find(
      item=>item.fuel===fuel&&Boolean(item.self)===boolFlag(self)
     );
     if(!price)continue;
     const distance=haversineKm(lat,lon,Number(station.lat),Number(station.lon));
     if(distance>radius)continue;
     stations.push({
      id:String(station.id),
      lat:Number(station.lat),
      lon:Number(station.lon),
      address:station.address||'',
      road_type:station.road_type||'',
      price:Number(price.price),
      updated:price.updated||'',
      observed_date:meta.price_date,
      fuel,
      isSelf:boolFlag(self),
      distance_km:Math.round(distance*1000)/1000
     })
    }
   }
   stations.sort((a,b)=>a.price-b.price||a.distance_km-b.distance_km);
   return{
    ok:true,
    stations,
    price_date:meta.price_date,
    registry_date:meta.registry_date,
    history_days:meta.history&&meta.history.available_snapshot_dates
      ?meta.history.available_snapshot_dates.length:0,
    tracked_station_rows:0,
    generated_at:meta.generated_at,
    warning:null
   }
  },
  async getHistory({id,fuel,self,days}){
   const meta=await metadata();
   const hmeta=await historyMetadata();
   if(!hmeta){
    return{ok:true,points:[],requested_days:Number(days)||7,observed_days:0,missing_days:Number(days)||7,
      start:null,end:null,available_total_days:0,available_start:null,available_end:null,interpolated:false}
   }
   const key=stationCellById.get(String(id));
   const requested=Math.max(1,Math.min(Number(days)||7,Number(hmeta.window_days)||7));
   const allDays=hmeta.days||[];
   const selectedDays=allDays.slice(-requested);
   if(!key||!(hmeta.cells||[]).includes(key)){
    return{ok:true,points:[],requested_days:requested,observed_days:0,missing_days:requested,
      start:selectedDays[0]||null,end:selectedDays.at(-1)||null,available_total_days:0,
      available_start:null,available_end:null,interpolated:false}
   }
   const payload=await historyCell(key);
   const combo=`${fuel}:${boolFlag(self)?1:0}`;
   const values=payload.stations&&payload.stations[String(id)]
    ?payload.stations[String(id)][combo]||[]:[];
   const offset=Math.max(0,allDays.length-requested);
   const points=[];
   for(let i=offset;i<allDays.length;i++){
    const value=values[i];
    if(value==null)continue;
    points.push({date:allDays[i],price:Number(value),source:'mimit_08_static',communicated_at:null})
   }
   const availableIndices=[];
   values.forEach((value,index)=>{if(value!=null)availableIndices.push(index)});
   return{
    ok:true,
    points,
    requested_days:requested,
    observed_days:points.length,
    missing_days:Math.max(0,requested-points.length),
    start:selectedDays[0]||null,
    end:selectedDays.at(-1)||null,
    available_total_days:availableIndices.length,
    available_start:availableIndices.length?allDays[availableIndices[0]]:null,
    available_end:availableIndices.length?allDays[availableIndices.at(-1)]:null,
    interpolated:false
   }
  },
  async searchPlaces({query,lang}){
   const q=normalizeText(query);
   if(!q)return{ok:true,results:[]};
   const placePayload=await places();
   const municipalityMatches=[];
   for(const place of placePayload.places||[]){
    const name=normalizeText(place.name),province=normalizeText(place.province);
    const label=`${name} ${province}`.trim();
    let rank=99;
    if(name===q)rank=0;
    else if(name.startsWith(q)||label.startsWith(q))rank=2;
    else if(name.includes(q)||label.includes(q))rank=4;
    if(rank===99)continue;
    municipalityMatches.push({rank,place})
   }

   const localityMatches=[];
   if(q.length>=3){
    const localityPayload=await localities();
    for(const row of localityPayload.localities||[]){
     const [rawName,rawType,proCom,municipality,rawLat,rawLon]=row;
     const name=normalizeText(rawName);
     const parent=normalizeText(municipality);
     const label=`${name} ${parent}`.trim();
     let rank=99;
     if(name===q)rank=1;
     else if(name.startsWith(q)||label.startsWith(q))rank=3;
     else if(name.includes(q)||label.includes(q))rank=5;
     if(rank===99)continue;

     const lat=Number(rawLat),lon=Number(rawLon),type=Number(rawType);
     const duplicateMunicipality=municipalityMatches.some(({place})=>
      normalizeText(place.name)===name&&
      haversineKm(lat,lon,Number(place.lat),Number(place.lon))<=15
     );
     if(duplicateMunicipality)continue;
     localityMatches.push({rank,name:rawName,type,proCom,municipality,lat,lon})
    }
   }

   municipalityMatches.sort((a,b)=>a.rank-b.rank
    ||Number(b.place.station_count||0)-Number(a.place.station_count||0)
    ||String(a.place.name).localeCompare(String(b.place.name),'it'));

   localityMatches.sort((a,b)=>a.rank-b.rank
    ||a.type-b.type
    ||String(a.name).localeCompare(String(b.name),'it')
    ||String(a.municipality).localeCompare(String(b.municipality),'it')
    ||String(a.proCom).localeCompare(String(b.proCom)));

   const ranked=[
    ...municipalityMatches.map(({rank,place})=>({
     rank,
     result:{
      display_name:[place.name,place.province].filter(Boolean).join(', '),
      lat:Number(place.lat),
      lon:Number(place.lon),
      type:'municipality',
      boundingbox:[]
     }
    })),
    ...localityMatches.map(item=>{
     const italian=String(lang||'').toLowerCase().startsWith('it');
     const kind=item.type===2
      ?(italian?'nucleo abitato':'inhabited nucleus')
      :(italian?'località':'locality');
     const parent=item.municipality?` — ${item.municipality}`:` (${item.proCom})`;
     return{
      rank:item.rank,
      result:{
       display_name:`${item.name}${parent} · ${kind}`,
       lat:item.lat,
       lon:item.lon,
       type:'locality',
       boundingbox:[]
      }
     }
    })
   ];
   ranked.sort((a,b)=>a.rank-b.rank||a.result.display_name.localeCompare(b.result.display_name,'it'));
   return{ok:true,results:ranked.slice(0,8).map(item=>item.result)}
  },
  async syncCurrent(){
   throw Error('Current snapshot sync is unavailable in static mode.')
  }
 }
}

window.FuelMapData=config.mode==='static'?createStaticProvider():createLocalProvider();
})();
