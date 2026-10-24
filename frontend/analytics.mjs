/** Pure presentation-layer helpers; never infer missing observations. */
export function distinct(values = []) { return [...new Set((Array.isArray(values) ? values : []).filter(Boolean))]; }
export function sourceCount(item) { return distinct(item?.source_ids).length; }
export function comparisonRanking(comparisons = []) {
  const groups = new Map();
  for (const comparison of comparisons || []) {
    if (!comparison || comparison.is_direct !== true || !comparison.competitor) continue;
    const name = String(comparison.competitor).trim();
    if (!name) continue;
    const key = name.toLocaleLowerCase();
    const curr = groups.get(key) || { name, sources: new Set(), comparisons: 0, evidence_ids: new Set() };
    for (const id of distinct(comparison.source_ids)) curr.sources.add(id);
    for (const id of distinct(comparison.evidence_ids)) curr.evidence_ids.add(id);
    curr.comparisons += 1;
    groups.set(key, curr);
  }
  return [...groups.values()].map(x => ({ name: x.name, source_count: x.sources.size, comparison_count: x.comparisons, evidence_ids: [...x.evidence_ids] }))
    .filter(x => x.source_count > 0)
    .sort((a,b) => b.source_count - a.source_count || b.comparison_count - a.comparison_count || a.name.localeCompare(b.name));
}
export function insightCoverage(insight, totalSources) { const n = sourceCount(insight); return totalSources ? `${n}/${totalSources} videos` : `${n} videos`; }
export function sentimentParts(attr) {
  const raw = attr?.sentiment_counts || {};
  const counts = ['positive','neutral','negative'].map(k => Math.max(0, Number(raw[k]) || 0));
  const total = counts.reduce((a,b)=>a+b,0);
  return { counts, total, pct: total ? counts.map(n=>n/total*100) : [0,0,0] };
}
export function analysisValidity(d) {
  if (!d || typeof d !== 'object' || typeof d.query !== 'string' || !Array.isArray(d.sources)) return 'A report needs a query string and sources array.';
  for (const field of ['insights','attributes','themes','comparisons','evidence','source_summaries','limitations','word_phrases']) if (d[field] != null && !Array.isArray(d[field])) return `The ${field} field must be an array.`;
  if((d.limitations||[]).some(x=>typeof x!=='string'))return 'Limitations must be text.';
  const sources=new Set(d.sources.map(s=>s?.id));
  if(d.sources.some(s=>!s||typeof s.id!=='string'||!s.id||typeof s.title!=='string')||sources.size!==d.sources.length)return 'Sources need unique IDs and titles.';
  const completed=new Set(d.sources.filter(s=>s.status==='completed').map(s=>s.id));
  const evidence=new Map((d.evidence||[]).map(e=>[e?.id,e]));
  if(evidence.size!==(d.evidence||[]).length)return 'Evidence IDs must be unique.';
  for(const e of d.evidence||[])if(!e||typeof e.id!=='string'||!completed.has(e.source_id))return 'Evidence must resolve to a source.';
  for(const a of d.attributes||[]){if(typeof a?.name!=='string')return 'Attributes need names.';if(a.sentiment_counts&&Object.values(a.sentiment_counts).some(v=>!Number.isInteger(v)||v<0))return 'Sentiment counts must be nonnegative observation counts.';}
  for(const field of ['insights','attributes','themes','comparisons'])for(const row of d[field]||[]){
   if(!row||!Array.isArray(row.source_ids)||row.source_ids.some(id=>!completed.has(id)))return 'Finding coverage must resolve to sources.';
   if(row.evidence_ids&&(!Array.isArray(row.evidence_ids)||row.evidence_ids.some(id=>!evidence.has(id))))return 'Finding evidence references must resolve.';
   if(field==='comparisons'&&row.is_direct===true&&d.kind!=='synthetic'){
    if(!row.evidence_ids?.length||row.source_ids.some(id=>!row.evidence_ids.some(eid=>evidence.get(eid)?.source_id===id)))return 'Direct comparisons require evidence for each counted source.';
    if(row.evidence_ids.some(id=>!Number.isFinite(evidence.get(id)?.start_seconds)))return 'Direct comparisons require timestamped evidence.';
   }
  }
  return null;
}
export function evidenceByIds(dataset, ids=[]) { const allowed=new Set(ids||[]); return (dataset.evidence||[]).filter(e=>allowed.has(e.id)); }

export function safeLink(value) {
  try { const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&['youtube.com','www.youtube.com','m.youtube.com','youtu.be'].includes(u.hostname)?u.href:''; } catch {return '';}
}
export function sourceLink(source,evidence) {
 const raw=safeLink(source?.url);if(!raw)return '';
 const u=new URL(raw);
 if(Number.isFinite(evidence?.start_seconds)&&evidence.start_seconds>=0)u.searchParams.set('t',String(Math.floor(evidence.start_seconds)));
 return u.href;
}

/** Required frontend copy policy, applied without changing stored evidence. */
export function displayText(value) {
 return String(value ?? '').replace(/[ \t]*\u2014[ \t]*/g, ' - ');
}

/** Escape markup attributes without changing URLs or opaque identifiers. */
export function escapeAttribute(value) {
 return String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
export function completedLabel(value) {
 const date=new Date(value);
 return Number.isNaN(date.getTime())?displayText(value):date.toLocaleString();
}
/** Poll only backend-owned status. Transient failures retain the resumable ID. */
export async function watchAnalysisJob(id, {
 request=fetch, wait=ms=>new Promise(resolve=>setTimeout(resolve,ms)),
 onProgress=()=>{}, onReconnect=()=>{}, clearActive=()=>{},
 requestTimeout=15000, maxFailures=6,
}={}) {
 let failures=0;
 for(;;){
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),requestTimeout);
  let response,job;
  try {
   response=await request('/api/searches/'+encodeURIComponent(id),{signal:controller.signal});
   if(response.status>=500||response.status===429)throw Error('Temporary service interruption');
   job=await response.json();
  } catch(error) {
   clearTimeout(timeout);
   failures+=1;onReconnect();
   if(failures>=maxFailures)throw Error('Connection is unavailable. Your analysis is saved. Select Resume analysis to reconnect.');
   await wait(Math.min(1000*2**(failures-1),15000));continue;
  } finally {clearTimeout(timeout);}
  failures=0;
  if(!response.ok){if(response.status===404)clearActive();throw Error(job.error||'Unable to retrieve analysis progress.');}
  onProgress(job);
  if(job.status==='failed'||job.status==='cancelled'){clearActive();throw Error(job.message||'Analysis failed.');}
  if(job.status==='completed'){
   const error=analysisValidity(job.analysis);
   clearActive();
   if(error)throw Error('The completed analysis could not be loaded: '+error);
   return job;
  }
  if(!['queued','running'].includes(job.status))throw Error('Unrecognized analysis status. Select Resume analysis to reconnect.');
  await wait(2000);
 }
}

/** Only the authenticated evidence endpoints may supply report images. */
export function safeEvidenceImage(value) {
 return typeof value==='string'&&/^\/api\/(?:evidence\/[a-f0-9]{64}\.jpg|frames\/[a-f0-9]{20}\/frame_\d+\.jpg)$/.test(value)?value:'';
}
