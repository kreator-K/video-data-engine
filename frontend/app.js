import { comparisonRanking, sourceCount, sentimentParts, analysisValidity, distinct, evidenceByIds, safeLink, sourceLink, displayText, escapeAttribute, completedLabel, watchAnalysisJob, safeEvidenceImage } from './analytics.mjs';
const state = { dataset:null, visibleRefs:false, query:'', refs:'', error:'', busy:false, isPreview:false, activeEvidence:null };
const app=document.querySelector('#app');
const esc=v=>escapeAttribute(displayText(v));
const attr=escapeAttribute;
const evidenceAttribute=ids=>attr(JSON.stringify(ids));
const get=id=>document.getElementById(id);
const icon={play:'▶',search:'⌕',clip:'⊕',arrow:'↗',audio:'◖',image:'▣',brand:'◈',spark:'✦'};
function scaffold(){
 app.innerHTML=`<div class="shell"><nav class="topbar"><a class="logo" href="#top"><span class="logo-icon">${icon.play}</span>VIDEO DATA AGENT</a><div class="top-actions"><a href="#results">Insights</a><a href="#sources">Sources</a><span class="pill">Video-native intelligence</span></div></nav>
 <main id="top"><section class="hero"><div class="eyebrow">Multimodal product & brand intelligence</div><h1>Find the insights hiding <br>inside video.</h1><p>Understand what people say, show and compare across videos - with every important insight connected to its evidence.</p>
 <div class="composer"><textarea class="compose-input" id="query" aria-label="Insight topic" placeholder="What product, brand, or industry insights would you like to explore today?"></textarea><div id="refs" class="ref-field hidden"><label for="reference-text">Reference video URLs · optional</label><textarea id="reference-text" placeholder="One URL per line. These references supplement discovery when supported."></textarea></div>
 <div class="compose-foot"><div class="left-acts"><button class="btn btn-subtle" id="ref-toggle" type="button">${icon.clip} Add reference videos</button><label class="btn hidden" id="import-label" for="import-input">↑ Open saved analysis</label><input id="import-input" type="file" accept=".json,application/json" class="hidden"></div><div class="right-acts"><button class="btn btn-primary" type="button" id="analyze">Search & analyze 10 videos</button></div></div></div>
 <div class="examples"><span class="muted small">Try a topic</span><button class="chip" data-example="iPhone Duo reviews">iPhone Duo reviews</button><button class="chip" data-example="Samsung foldable reviews">Samsung foldable reviews</button><button class="chip" data-example="Electric SUV reviews">Electric SUV reviews</button><button class="chip" data-example="Protein drink reviews">Protein drink reviews</button></div>
 <div id="message" role="status"></div>
 <div id="saved-library"></div><button class="btn hidden" id="preview">${icon.spark} Open illustrative design preview</button>
 </section><section id="results"></section></main><footer class="footer">Video Data Agent · Source-grounded video intelligence.</footer></div><div id="drawer-root"></div>`;
 get('analyze').textContent='Search & analyze 10 videos';
 get('query').value=state.query;get('reference-text').value=state.refs;
 get('query').addEventListener('input',e=>state.query=e.target.value);
 get('reference-text').addEventListener('input',e=>state.refs=e.target.value);
 get('ref-toggle').onclick=()=>{state.visibleRefs=!state.visibleRefs;get('refs').classList.toggle('hidden',!state.visibleRefs);get('ref-toggle').textContent=state.visibleRefs?'− Hide reference videos':'+ Add reference videos';};
 get('import-input').onchange=async e=>{const f=e.target.files?.[0];if(!f)return;try{if(f.size>5*1024*1024)throw Error('Report exceeds the 5 MB import limit.');const d=JSON.parse(await f.text());loadData(d,false);}catch(err){setMessage('Unable to read saved JSON: '+err.message,true)}};
 get('analyze').onclick=submitAnalysis;
 if(new URLSearchParams(location.search).get('preview')==='1')get('preview').classList.remove('hidden');
 get('preview').onclick=async()=>{try{let d=await (await fetch('./data/design-preview.json')).json();loadData(d,true);}catch(e){setMessage('Could not load design preview.',true)}};
 document.querySelectorAll('[data-example]').forEach(b=>b.onclick=()=>{state.query=b.dataset.example;get('query').value=state.query;get('query').focus()});
 renderReport();
 loadLibrary();
 resumeJob();
}
function setMessage(msg,err=false){get('message').innerHTML=msg?`<div class="notice ${err?'error':''}">${esc(msg)}</div>`:''}
async function loadLibrary(){
 const target=get('saved-library');target.innerHTML='';
 try {
  const res=await fetch('/api/analyses');if(!res.ok)return;
  const data=await res.json();
  const completed=(data.analyses||[]).filter(a=>a.status==='completed');
  if(!completed.length)return;
  target.innerHTML='<label for="saved-choice">Completed analyses</label><select id="saved-choice"><option value="">Choose an analysis…</option>'+completed.map(a=>`<option value="${attr(a.id)}">${esc(a.title)}${a.completed_at?` · ${esc(completedLabel(a.completed_at))}`:""}</option>`).join('')+'</select>';
  get('import-label').classList.remove('hidden');
  get('saved-choice').onchange=async e=>{if(!e.target.value)return;try{const r=await fetch('/api/analyses/'+encodeURIComponent(e.target.value));const body=await r.json();if(!r.ok)throw Error(body.error);loadData(body.analysis,false)}catch(error){setMessage(error.message,true)}};
 }catch{/* Keep history hidden if the backend is unreachable. */}
}
async function pollJob(id){
 const job=await watchAnalysisJob(id,{
  onProgress:job=>setMessage(job.message||job.status),
  onReconnect:()=>setMessage('Connection interrupted. Reconnecting to your analysis...'),
  clearActive:()=>localStorage.removeItem('active-analysis-job'),
 });
 loadData(job.analysis,false);await loadLibrary();setMessage(job.message);
}
async function resumeJob(){
 const id=localStorage.getItem('active-analysis-job');if(!id)return;
 state.busy=true;get('analyze').disabled=true;get('analyze').textContent='Analyzing…';
 try{await pollJob(id)}catch(error){setMessage(error.message,true)}
 finally{state.busy=false;get('analyze').disabled=false;get('analyze').textContent=localStorage.getItem('active-analysis-job')?'Resume analysis':'Search & analyze 10 videos'}
}
async function submitAnalysis(){
 if(state.busy)return;
 if(localStorage.getItem('active-analysis-job')){await resumeJob();return;}
 if(!state.query.trim()){setMessage('Enter a topic to analyze.',true);return;}
 state.dataset=null;state.closeEvidence?.();renderReport();
 state.busy=true;get('analyze').disabled=true;get('analyze').textContent='Analyzing…';setMessage('Submitting analysis…');
 try {
  const refs=state.refs.split(/[\r\n]+/).map(x=>x.trim()).filter(Boolean);
  const res=await fetch('/api/searches',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:state.query.trim(),reference_urls:refs})});
  const result=await res.json();
  if(!res.ok)throw new Error(result.error||'Analysis service unavailable. Open a saved normalized JSON report.');
  if(!result.id)throw new Error('Search job was not created.');
  localStorage.setItem('active-analysis-job',result.id);
  await pollJob(result.id);
 }catch(err){setMessage(err.message||'Could not contact analysis service.',true)}
 finally{state.busy=false;get('analyze').disabled=false;get('analyze').textContent=localStorage.getItem('active-analysis-job')?'Resume analysis':'Search & analyze 10 videos'}
}
function loadData(data,preview){const err=analysisValidity(data);if(err){setMessage(err,true);return;}state.dataset=data;state.isPreview=!!preview||data.kind==='synthetic';state.error='';setMessage('');renderReport();get('results').scrollIntoView({behavior:'smooth',block:'start'});}
function section(title,subtitle,content,extra=''){return `<section class="panel section"><div class="section-head"><div><h3>${esc(title)}</h3><p>${esc(subtitle)}</p></div>${extra?`<span class="section-flag">${esc(extra)}</span>`:''}</div>${content}</section>`}
function evidenceButton(ids,label){let clean=distinct(ids||[]);return clean.length?`<button class="anchor-button" data-evidence="${evidenceAttribute(clean)}">${esc(label||'See evidence')} ↗</button>`:''}
function renderReport(){
 const target=get('results');const d=state.dataset;
 if(!d){target.innerHTML='';return;}
 const src=d.sources||[];const n=src.filter(s=>s.status==='completed').length;const competitors=comparisonRanking(d.comparisons||[]);const top=competitors[0];const tiedLeaders=top?competitors.filter(c=>c.source_count===top.source_count):[];const preview=state.isPreview;
 let html=`<div class="report-head"><div><div class="eyebrow">${preview?'Design preview · synthetic data':'Analysis results'}</div><h2>${esc(d.title||d.query)}</h2><div class="meta"><span>${n}/${src.length} sources processed</span>${d.completed_at||d.analyzed_at?`<span>${esc(completedLabel(d.completed_at||d.analyzed_at))}</span>`:''}</div></div><div class="report-actions"><button class="btn" id="export">↓ Export JSON</button><button class="btn btn-subtle" id="new-analysis">New analysis</button></div></div>`;
 if(preview) html+=`<div class="preview-note"><strong>ILLUSTRATIVE UI DATA</strong> · All findings, counts, product comparisons and video moments below are synthetic placeholders - not real review results. Import an actual normalized agent report to replace them.</div>`;
 if((d.limitations||[]).length)html+=`<details class="notice"><summary>About this analysis</summary><ul>${d.limitations.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></details>`;
 if((d.source_summaries||[]).length)html+=section('Source summaries','Existing per-video reports. These are not consolidated executive findings.',`<div class="grid theme-grid">${d.source_summaries.map(x=>`<article class="theme-card"><h4>${esc(x.title)}</h4><p>${esc(x.description)}</p><span class="tag neutral">Source-level summary</span></article>`).join('')}</div>`);
 const insights=d.insights||[];
 html+=section('Executive insights','The most important findings visible across the analyzed source videos',insights.length?`<div class="grid insight-grid">${insights.map((x,i)=>`<article class="insight-card" data-evidence="${evidenceAttribute(x.evidence_ids||[])}" tabindex="0" role="button"><div class="small muted">0${i+1} · ${sourceCount(x)}/${n} video${sourceCount(x)===1?'':'s'}</div><strong>${esc(x.title)}</strong><p>${esc(x.description)}</p><div class="insight-foot"><span class="tag">${esc(x.modality||'Evidence linked')}</span><span class="small muted">${(x.evidence_ids||[]).length} moments ↗</span></div></article>`).join('')}</div>`:'<p class="muted">No evidence-backed executive insights are available in this report.</p>');
 const attrs=d.attributes||[];
 const attrHtml=attrs.length?attrs.map(a=>{let p=sentimentParts(a);return `<div class="attr-row"><div><div class="attr-name">${esc(a.name)}</div><div class="attr-reason">${esc(a.driver||'')}</div></div><div class="bartrack" aria-label="Sentiment distribution for ${esc(a.name)}">${p.total?p.pct.map((v,i)=>`<span class="${['bar-positive','bar-neutral','bar-negative'][i]}" style="width:${v}%"></span>`).join(''):'<span class="small muted">Sentiment unavailable</span>'}</div><div class="attr-count">${sourceCount(a)}/${n} videos${p.total?`<br><small>${p.counts.join(" / ")} + / neutral / − observations</small>`:""}</div></div>`}).join(''):'<p class="muted">No attribute-level observations are available.</p>';
 const compRows=competitors.length?competitors.map(c=>`<div class="compet-row"><span class="name" title="${esc(c.name)}">${esc(c.name)}</span><div class="line"><i style="width:${n?Math.round(c.source_count/n*100):0}%"></i></div><span class="num">${c.source_count}/${n} videos</span></div>`).join(''):'<p class="muted">No supported direct comparison records supplied.</p>';
 html+=`<div class="twocol">${section('Product & attribute perception','Coverage, sentiment and reasons behind attribute-level observations',`${attrHtml}<div class="sep"></div><div class="small muted"><span style="color:var(--green)">●</span> Positive &nbsp; <span style="color:#a8b2c0">●</span> Neutral &nbsp; <span style="color:var(--red)">●</span> Negative · Bars show only sentiment-tagged observations.</div>`)}${section('Most compared-with product','Direct comparison coverage, not incidental name mentions',`<div class="compare-hero"><div class="label">Most directly compared product</div><div class="big">${top?esc(tiedLeaders.length>1?tiedLeaders.map(x=>x.name).join(' · ')+' (tie)':top.name):'Direct comparison data unavailable'}</div><div class="foot">${top?`${top.source_count} of ${n} reviewed videos contain a direct comparison`:'Available only when direct comparison evidence exists'}</div></div><div class="compet-list">${compRows}</div>`)}</div>`;
 const themes=d.themes||[];
 html+=section('Discussion themes','What reviewers are actually discussing beyond broad attribute names',themes.length?`<div class="grid theme-grid">${themes.map(t=>`<div class="theme-card"><h4>${esc(t.name)}</h4><p>${esc(t.description)}</p><span class="small muted">${sourceCount(t)}/${n} sources · ${evidenceButton(t.evidence_ids,'Evidence')}</span></div>`).join('')}</div>`:'<p class="muted">No recurring themes available.</p>');
 const maxcols=src.filter(s=>s.status==='completed');
 let heat='<p class="muted">Attribute and per-video mapping is not present in these results.</p>';
 if(maxcols.length&&attrs.length){heat=`<div class="heatmap-wrap"><table class="heatmap"><thead><tr><th>Attribute</th>${maxcols.map((s,i)=>`<th title="${esc(s.title)}">V${i+1}</th>`).join('')}</tr></thead><tbody>${attrs.map(a=>`<tr><th>${esc(a.name)}</th>${maxcols.map(s=>{const observations=(a.source_ids||[]).filter(id=>id===s.id).length;return `<td class="${observations?'on':''}" title="${esc(s.title)}: ${observations?'Discussed':'Not observed'}">${observations?'●':'·'}</td>`}).join('')}</tr>`).join('')}</tbody></table></div>`}
 html+=section('Cross-video consistency','Which attributes recur across independent source videos',heat,'Distinct video coverage');
 const matrix=(d.comparisons||[]).filter(c=>c.is_direct===true);
 html+=section('Competitive intelligence','The products compared, the attributes involved and what the videos actually establish',matrix.length?`<div class="table-wrap"><table class="comparison-table"><thead><tr><th>Compared product</th><th>Attribute</th><th>Observed comparison</th><th>Coverage / Evidence</th></tr></thead><tbody>${matrix.map(c=>`<tr><td>${esc(c.competitor)}</td><td>${esc(c.attribute||'General')}</td><td>${esc(c.observation||'Direct comparison found; detail unavailable')}</td><td>${sourceCount(c)} videos · ${evidenceButton(c.evidence_ids,'Verify')}</td></tr>`).join('')}</tbody></table></div>`:'<p class="muted">Direct product comparison data is not available in this report.</p>');
 const evid=d.evidence||[];
 html+=section('Multimodal evidence','What was said, what appeared visually, and where both align',evid.length?`<div class="grid gallery">${evid.slice(0,12).map(e=>`<article class="evidence-card" role="button" tabindex="0" data-evidence="${evidenceAttribute([e.id])}"><div class="frame">${safeEvidenceImage(e.image_url)?`<img src="${attr(e.image_url)}" alt="Saved analyzed video frame">`:esc(e.emoji||'▷')}<span class="timestamp">${esc(e.timestamp||'Time unavailable')}</span></div><strong>${esc(e.title)}</strong><p>${esc(e.summary||'')}</p><span class="tag neutral">${esc(e.modality||'Evidence')}</span></article>`).join('')}</div>`:'<p class="muted">No verified multimodal evidence segments supplied.</p>');
 if((d.word_phrases||[]).length)html+=section('Common discussion language','A secondary exploratory view - not a substitute for structured themes',`<div class="wordstrip">${d.word_phrases.slice(0,18).map((w,i)=>`<span style="font-size:${Math.min(21,11+Number(w.weight||0)*2)}px">${esc(w.phrase)}</span>`).join('')}</div>`,'Optional');
 html+=section('Source videos','The exact videos included in the analyzed corpus',src.length?`<div class="source-list" id="sources">${src.map((s,i)=>`<div class="source-item"><div class="source-index">${i+1}</div><span title="${esc(s.title)}">${safeLink(s.url)?`<a href="${attr(safeLink(s.url))}" target="_blank" rel="noopener noreferrer">${esc(s.title)}</a>`:esc(s.title)}</span><span class="status ${s.status==='completed'?'':'failed'}">${esc(s.status||'unknown')}</span></div>`).join('')}</div>`:'<p class="muted">No sources supplied.</p>');
 target.innerHTML=html;
 target.querySelectorAll('[data-evidence]').forEach(el=>{const fn=()=>openEvidence(JSON.parse(el.dataset.evidence));el.addEventListener('click',fn);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fn();}})});
 get('export').onclick=()=>{const blob=new Blob([JSON.stringify(d,null,2)],{type:'application/json'});const a=document.createElement('a');const url=URL.createObjectURL(blob);a.href=url;a.download='video-data-agent-analysis.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),500)};
 get('new-analysis').onclick=()=>{get('query').focus();window.scrollTo({top:0,behavior:'smooth'})};
}
function openEvidence(ids){state.closeEvidence?.();const d=state.dataset;if(!d)return;const segments=evidenceByIds(d,ids);const e=segments[0];if(!e){return;}const source=(d.sources||[]).find(s=>s.id===e.source_id);state.activeEvidence=ids;const backdrop=document.createElement('div');backdrop.className='evidence-backdrop';backdrop.innerHTML=`<aside class="drawer" role="dialog" aria-modal="true" aria-label="Supporting evidence"><div class="drawer-top"><div><div class="eyebrow">Source verification</div><h3>${esc(e.title||'Evidence moment')}</h3></div><button class="btn" id="close-drawer" aria-label="Close evidence">✕</button></div><p>${esc(e.summary||'')}</p><div class="frame">${safeEvidenceImage(e.image_url)?`<img src="${attr(e.image_url)}" alt="Saved analyzed video frame">`:esc(e.emoji||'▷')}<span class="timestamp">${esc(e.timestamp||'Unknown time')}</span></div><span class="tag neutral">${esc(e.modality||'Evidence')}</span><h4>What was said</h4><p>${esc(e.spoken||'No transcript excerpt is available for this moment.')}</p><h4>What was shown</h4><p>${esc(e.shown||'No visual observation is available for this moment.')}</p><h4>Source</h4><p>${esc(source?.title||e.source_id||'Source unavailable')} · ${esc(e.timestamp||'')}</p>${sourceLink(source,e)?`<a class="btn" href="${attr(sourceLink(source,e))}" target="_blank" rel="noopener noreferrer">Open source video ↗</a>`:''}<div class="sep"></div><p class="small muted">${segments.length} supporting moment${segments.length===1?'':'s'} in this selection. ${state.isPreview?'Preview evidence is illustrative and not real.':''}</p>${segments.length>1?`<div class="grid">${segments.slice(1).map(x=>`<button class="btn" data-select="${attr(x.id)}">${esc(x.title)} · ${esc(x.timestamp)}</button>`).join('')}</div>`:''}</aside>`;
 get('drawer-root').replaceChildren(backdrop);
 const previousFocus=document.activeElement;
 const onKey=ev=>{if(ev.key==='Escape')close();if(ev.key==='Tab'){const items=[...backdrop.querySelectorAll('button,a[href]')];const first=items[0],last=items.at(-1);if(ev.shiftKey&&document.activeElement===first){ev.preventDefault();last.focus()}else if(!ev.shiftKey&&document.activeElement===last){ev.preventDefault();first.focus()}}};
 const close=()=>{document.removeEventListener('keydown',onKey);get('drawer-root').replaceChildren();state.closeEvidence=null;previousFocus?.focus()};state.closeEvidence=close;get('close-drawer').onclick=close;backdrop.onclick=ev=>{if(ev.target===backdrop)close()};backdrop.querySelectorAll('[data-select]').forEach(b=>b.onclick=()=>openEvidence([b.dataset.select]));
 document.addEventListener('keydown',onKey);get('close-drawer').focus();
}
scaffold();
