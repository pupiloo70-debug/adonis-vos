// Synthetic-only 0.3 research adapter; does not modify 0.2 or CIVIC-TRACE.
// Distinguishes attributable testimony, document-supported gaps, and remedies.
import { createHash } from 'node:crypto';

export const VERSION = '0.3-testimony-controller-context/research-1';
const allowed = new Set(['CLAIM_ONLY','DOCUMENT_LINKED','INDEPENDENTLY_CHECKED']);
const isObj = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const nonempty = x => typeof x === 'string' && x.trim().length > 0;
const sha = x => createHash('sha256').update(x).digest('hex');
const reject = s => {throw new Error(s)};
function array(v,name) {if (!Array.isArray(v)) reject('INVALID_'+name);return v;}
function idSet(arr,name) {
 const ids=new Set(); for(const x of arr){if(!isObj(x)||!nonempty(x.id)||ids.has(x.id))reject('INVALID_OR_DUPLICATE_'+name);ids.add(x.id)}
 return ids;
}
// Correct trivial spacing; do not rewrite a user's meaning, inject claims, or retain raw wording.
function clean(s){return s.normalize('NFC').replace(/\s+/g,' ').trim()}
export function reviewContext(input) {
 if(!isObj(input)||input.schema!=='ADONIS-0.3-CONTEXT/SYNTHETIC-1'||input.synthetic!==true||!nonempty(input.case_id)) reject('SYNTHETIC_INPUT_ONLY');
 const statements=array(input.statements,'STATEMENTS'), records=array(input.records,'RECORDS'), remedies=array(input.remedies,'REMEDIES');
 idSet(statements,'STATEMENT');const recordIds=idSet(records,'RECORD');idSet(remedies,'REMEDY');
 const claims=new Map(), duplicates=[];
 for(const s of statements){
   if(!nonempty(s.claim_key)||!nonempty(s.summary)||!nonempty(s.speaker_role)||!nonempty(s.event_time)||!nonempty(s.report_time)||!['DIRECT','HEARSAY','INTERPRETATION'].includes(s.basis)) reject('INVALID_STATEMENT');
   if(Object.hasOwn(s,'raw_transcript')||Object.hasOwn(s,'raw_text')||Object.hasOwn(s,'private_conversation')) reject('RAW_PRIVATE_TEXT_NOT_ACCEPTED');
   const summary=clean(s.summary); if(summary.length>700)reject('SUMMARY_TOO_LONG');
   const key=clean(s.claim_key); // only explicit stable key, never fuzzy similarity overreach
   if(claims.has(key)){
      const item=claims.get(key);item.occurrences+=1;item.statement_ids.push(s.id);
      if(item.summary!==summary) item.requires_human_merge_review=true;
      duplicates.push({statement_id:s.id,canonical_statement_id:item.statement_ids[0],not_new_evidence:true});
   }else claims.set(key,{claim_key:key,summary,speaker_role:s.speaker_role,basis:s.basis,event_time:s.event_time,report_time:s.report_time,statement_ids:[s.id],occurrences:1,requires_human_merge_review:false,truth_status:'NOT_ADJUDICATED'});
 }
 const docGaps=[];
 for(const r of records){
  if(!nonempty(r.controller)||!nonempty(r.item)||!['AVAILABLE','NOT_PROVIDED','ACCESS_RESTRICTED','REPORTED_MISSING','REPORTED_DESTROYED','UNKNOWN'].includes(r.state)||!allowed.has(r.evidence_status)||!Array.isArray(r.source_refs)||r.source_refs.some(x=>!nonempty(x)))reject('INVALID_RECORD');
  if(r.evidence_status!=='CLAIM_ONLY'&&r.source_refs.length===0)reject('DOCUMENT_STATUS_WITHOUT_SOURCE');
  const gap=r.state!=='AVAILABLE';
  const documentary=r.evidence_status!=='CLAIM_ONLY';
  docGaps.push({record_id:r.id,controller:r.controller,item:r.item,reported_state:r.state,source_refs:[...r.source_refs],verification_status:r.evidence_status,
    access_asymmetry:gap?'REVIEW_REQUIRED':'NOT_INDICATED',
    controller_explanation:gap?'REQUEST_REVIEW':'NOT_REQUIRED_BY_THIS_RECORD',
    investigation_review:gap&&documentary&&['REPORTED_DESTROYED','REPORTED_MISSING'].includes(r.state)?'PRESERVATION_AND_INVESTIGATION_REVIEW':'NOT_AUTOMATIC',
    guilt:'NOT_ADJUDICATED',victim_proof_failure:'NOT_INFERRED'});
 }
 const checklist={monetary:false,source_access:false,independent_review:false,explanation:false,correction:false};
 for(const m of remedies){if(!Object.hasOwn(checklist,m.type)||!['CLAIMED','DOCUMENTED','INDEPENDENTLY_VERIFIED'].includes(m.status)||!Array.isArray(m.source_refs)||m.source_refs.some(x=>!nonempty(x)))reject('INVALID_REMEDY');if(m.status==='INDEPENDENTLY_VERIFIED'&&m.source_refs.length>0)checklist[m.type]=true;}
 const complete=Object.values(checklist).every(Boolean);
 return {schema:'ADONIS-0.3-CONTEXT-REVIEW/RESEARCH-1',case_id:input.case_id,version:VERSION,total_score:null,
  testimony:[...claims.values()],duplicates,documentary_gaps:docGaps,
  ethical_gravity:{duration_note:nonempty(input.unresolved_duration_note)?clean(input.unresolved_duration_note):null,score:null,repeated_statements_do_not_increase_weight:true},
  substantive_remedy:{components_verified:checklist,overall:complete?'COMPONENTS_VERIFIED_REQUIRES_HUMAN_REVIEW':'UNRESOLVED',money_alone_never_closes:true},
  decision_boundaries:{auto_guilt:false,auto_immunity:false,auto_causality:false,auto_adverse_inference:false,dispatch:'NOT_SENT',release:'NOT_APPROVED'}};
}
