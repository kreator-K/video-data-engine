import assert from 'node:assert/strict';
import { comparisonRanking, sourceCount, sentimentParts, analysisValidity } from './analytics.mjs';
const ranked=comparisonRanking([
 {competitor:'Samsung',is_direct:true,source_ids:['s1','s1','s2'],evidence_ids:['e1']},
 {competitor:'Samsung',is_direct:true,source_ids:['s2','s3'],evidence_ids:['e2']},
 {competitor:'Google',is_direct:true,source_ids:['s2'],evidence_ids:['e3']},
 {competitor:'Apple',is_direct:false,source_ids:['s1','s2','s3','s4'],evidence_ids:[]},
]);
assert.equal(ranked[0].name,'Samsung');
assert.equal(ranked[0].source_count,3);
assert.equal(ranked[1].source_count,1);
assert.equal(ranked.length,2);
assert.equal(sourceCount({source_ids:['s1','s1','s2']}),2);
const pct=sentimentParts({sentiment_counts:{positive:2,negative:1}}).pct;
assert.ok(Math.abs(pct[0]-2/3*100)<1e-8);
assert.ok(Math.abs(pct[2]-1/3*100)<1e-8);
assert.equal(analysisValidity({query:'Review',sources:[]}),null);
assert.match(analysisValidity({query:'',sources:{}}),/sources/);
const { safeLink, sourceLink }=await import('./analytics.mjs');
assert.equal(safeLink('javascript:alert(1)'),'');
assert.equal(sourceLink({url:'https://youtu.be/abc'},{start_seconds:12.5}),'https://youtu.be/abc?t=12');
assert.match(analysisValidity({query:'x',sources:[{id:'v',title:'Video',status:'completed'}],comparisons:[{competitor:'Other',is_direct:true,source_ids:['v'],evidence_ids:[]}]}),/require evidence/);
const fixture=JSON.parse(await (await import('node:fs/promises')).readFile(new URL('./data/design-preview.json',import.meta.url),'utf8'));
assert.equal(analysisValidity(fixture),null);

console.log('All frontend logic tests passed.');

const { displayText }=await import('./analytics.mjs');
for(const value of ['Insight\u2014driver','Chart \u2014 sentiment','Source\u2014title','Evidence \u2014 excerpt']) {
 assert.ok(!displayText(value).includes('\u2014'));
}
assert.equal(displayText('Camera\u2014excellent'),'Camera - excellent');
assert.equal(displayText('Battery life: strong'),'Battery life: strong');

const { escapeAttribute, completedLabel, watchAnalysisJob }=await import('./analytics.mjs');
const opaque='source\u2014id,with"markup<&';
assert.ok(escapeAttribute(opaque).includes('\u2014'));
assert.ok(!displayText(opaque).includes('\u2014'));
assert.equal(escapeAttribute('https://youtu.be/id?x=a&y=b'),'https://youtu.be/id?x=a&amp;y=b');
assert.equal(escapeAttribute('<script>"\''),'&lt;script&gt;&quot;&#39;');
assert.equal(completedLabel('not a date\u2014label'),'not a date - label');
assert.notEqual(completedLabel('2026-10-23T12:00:00Z'),'Invalid Date');
const complete={status:'completed',analysis:{query:'Real topic',sources:[]}};
let requests=0,cleared=0,reconnected=0,progress=[],delays=[];
const recovered=await watchAnalysisJob('opaque\u2014job',{
 request:async(url)=>{assert.ok(url.includes('opaque%E2%80%94job'));requests++;if(requests===1)throw Error('offline');if(requests===2)return {status:503};return {ok:true,status:200,json:async()=>requests===3?{status:'running',message:'Analyzing'}:complete};},
 wait:async ms=>delays.push(ms),onReconnect:()=>reconnected++,clearActive:()=>cleared++,onProgress:j=>progress.push(j.status),
});
assert.equal(recovered,complete);assert.equal(reconnected,2);assert.equal(cleared,1);assert.deepEqual(progress,['running','completed']);assert.deepEqual(delays,[1000,2000,2000]);
cleared=0;
await assert.rejects(watchAnalysisJob('active',{request:async()=>{throw Error('offline')},wait:async()=>{},maxFailures:2,clearActive:()=>cleared++}),/Resume analysis/);
assert.equal(cleared,0,'Transient outages must retain the active job for refresh/reconnect');
await assert.rejects(watchAnalysisJob('missing',{request:async()=>({ok:false,status:404,json:async()=>({error:'Missing job'})}),clearActive:()=>cleared++}),/Missing job/);
assert.equal(cleared,1);
await assert.rejects(watchAnalysisJob('failed',{request:async()=>({ok:true,status:200,json:async()=>({status:'failed',message:'Source failed'})}),clearActive:()=>cleared++}),/Source failed/);
assert.equal(cleared,2);
await assert.rejects(watchAnalysisJob('invalid',{request:async()=>({ok:true,status:200,json:async()=>({status:'completed',analysis:{query:'x',sources:{}}})}),clearActive:()=>cleared++}),/could not be loaded/);
assert.equal(cleared,3,'Terminal malformed report must not trap refresh in a stale job');
await assert.rejects(watchAnalysisJob('slow',{request:async(_,{signal})=>new Promise((_,reject)=>signal.addEventListener('abort',()=>reject(Error('timeout')))),requestTimeout:1,maxFailures:1,clearActive:()=>cleared++}),/Resume analysis/);
assert.equal(cleared,3);
console.log('Frontend reconnect, identity preservation and terminal state regressions passed.');

const {safeEvidenceImage}=await import('./analytics.mjs');
assert.ok(safeEvidenceImage('/api/evidence/'+ 'a'.repeat(64)+'.jpg'));
assert.ok(safeEvidenceImage('/api/frames/'+ 'a'.repeat(20)+'/frame_1.jpg'));
for(const url of ['https://external.example/pixel.jpg','/api/evidence/../secret.jpg','/api/evidence/'+ 'a'.repeat(64)+'.jpg?external=true'])assert.equal(safeEvidenceImage(url),'');

// Opaque evidence IDs remain raw through lookup, JSON selection and validation.
const opaqueEvidence='source\u2014id,with"quotes<&';
const rawReport={query:'Raw identifiers',sources:[{id:'source\u2014id',title:'Source\u2014title',status:'completed'}],evidence:[{id:opaqueEvidence,source_id:'source\u2014id',spoken:'Raw\u2014evidence'}]};
assert.equal(analysisValidity(rawReport),null);
const {evidenceByIds}=await import('./analytics.mjs');
assert.equal(evidenceByIds(rawReport,JSON.parse(JSON.stringify([opaqueEvidence])))[0],rawReport.evidence[0]);
assert.equal(rawReport.evidence[0].spoken,'Raw\u2014evidence');
assert.equal(evidenceByIds(rawReport,[displayText(opaqueEvidence)]).length,0);
