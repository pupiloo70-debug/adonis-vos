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
 return summarizeContext(input,false);
}

function summarizeContext(input,preserveProvenance) {
 if(!isObj(input)||input.schema!=='ADONIS-0.3-CONTEXT/SYNTHETIC-1'||input.synthetic!==true||!nonempty(input.case_id)) reject('SYNTHETIC_INPUT_ONLY');
 const statements=array(input.statements,'STATEMENTS'), records=array(input.records,'RECORDS'), remedies=array(input.remedies,'REMEDIES');
 idSet(statements,'STATEMENT');const recordIds=idSet(records,'RECORD');idSet(remedies,'REMEDY');
 const claims=new Map(), duplicates=[];
 for(const s of statements){
   if(!nonempty(s.claim_key)||!nonempty(s.summary)||!nonempty(s.speaker_role)||!nonempty(s.event_time)||!nonempty(s.report_time)||!['DIRECT','HEARSAY','INTERPRETATION'].includes(s.basis)) reject('INVALID_STATEMENT');
   if(Object.hasOwn(s,'raw_transcript')||Object.hasOwn(s,'raw_text')||Object.hasOwn(s,'private_conversation')) reject('RAW_PRIVATE_TEXT_NOT_ACCEPTED');
   // An optional explicitly scoped statement must not be silently assigned to a different case.
   if(Object.hasOwn(s,'case_id')&&s.case_id!==input.case_id) reject('STATEMENT_CASE_MISMATCH');
   // References are identifiers supplied by the fixture, not proof that the sources are authentic.
   if(Object.hasOwn(s,'source_refs')&&(!Array.isArray(s.source_refs)||s.source_refs.some(x=>!nonempty(x)))) reject('INVALID_STATEMENT_SOURCES');
   const refs=Object.hasOwn(s,'source_refs')?[...s.source_refs]:[];
   const summary=clean(s.summary); if(summary.length>700)reject('SUMMARY_TOO_LONG');
   const key=clean(s.claim_key); // only explicit stable key, never fuzzy similarity overreach
   const attribution={statement_id:s.id,speaker_role:s.speaker_role,basis:s.basis,event_time:s.event_time,report_time:s.report_time,source_refs:refs};
   if(preserveProvenance){
      Object.assign(attribution,{summary,review_id:s.review_id??null,review_version:s.review_version??null});
   }
   const identity=o=>JSON.stringify([o.summary,o.speaker_role,o.basis,o.event_time,o.review_id,o.review_version,[...new Set(o.source_refs)].sort()]);
   if(claims.has(key)){
      const item=claims.get(key);item.occurrences+=1;item.statement_ids.push(s.id);
      // Different speakers, observation bases or event dates must not be merged as one witness.
      if(item.summary!==summary||item.speaker_role!==s.speaker_role||item.basis!==s.basis||item.event_time!==s.event_time) item.requires_human_merge_review=true;
      const same=preserveProvenance?item.attribution_variants.find(o=>identity(o)===identity(attribution)):item.attribution_variants[0];
      item.attribution_variants.push(attribution);
      if(same) duplicates.push({statement_id:s.id,canonical_statement_id:same.statement_id,not_new_evidence:true});
   }else claims.set(key,{claim_key:key,summary,speaker_role:s.speaker_role,basis:s.basis,event_time:s.event_time,report_time:s.report_time,statement_ids:[s.id],attribution_variants:[attribution],occurrences:1,requires_human_merge_review:false,truth_status:'NOT_ADJUDICATED'});
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

// Additive, fail-closed P02 research route. Legacy reviewContext stays byte-semantically
// unchanged so callers must explicitly opt in to item-level quarantine.
// Item IDs and dependencies are scoped to their own collection; no cross-category inference.
export function reviewContextIsolated(input) {
  // Deny nonsynthetic and malformed top-level inputs before processing any child.
  reviewContext({...input,statements:[],records:[],remedies:[]});
  const names=['statements','records','remedies'];
  for(const name of names) array(input[name],name.toUpperCase());
  const preserved={};
  const held=[];
  let sourceAttestationsDowngraded=0;
  const reportedRecordAttestations=new Map();
  for (const name of names) {
    const originals=input[name];
    const counts=new Map();
    for (const x of originals) if (isObj(x)&&nonempty(x.id)) counts.set(x.id,(counts.get(x.id)||0)+1);
    const valid=new Map();
    for (const row of originals) {
      const id=isObj(row)&&nonempty(row.id)?row.id:null;
      let reason=null;
      if (!isObj(row)||!id) reason='INVALID_ITEM_OR_ID';
      else if (counts.get(id)>1) reason='AMBIGUOUS_DUPLICATE_ID';
      else if (Object.hasOwn(row,'case_id')&&row.case_id!==input.case_id) reason='OUT_OF_SCOPE_CASE';
      else if (['subject_id','material_id','question_id'].some(key=>Object.hasOwn(row,key)&&(!nonempty(input[key])||input[key]!==row[key]))) reason='SCOPE_NOT_BOUND_TO_PROJECT';
      else if (Object.hasOwn(row,'depends_on')&&(!Array.isArray(row.depends_on)||row.depends_on.some(x=>!nonempty(x)))) reason='INVALID_DEPENDENCY_FORMAT';
      if (!reason && name==='statements' && ['review_id','review_version'].some(k=>Object.hasOwn(row,k)&&row[k]!==null&&!nonempty(row[k]))) reason='INVALID_REVIEW_METADATA';
      if (!reason) {
        try {
          // Validate each child independently before any evidence is combined.
          const singleton={...input,statements:[],records:[],remedies:[],[name]:[row]};
          reviewContext(singleton);
        } catch (err) { reason='ITEM_VALIDATION_FAILED'; }
      }
      if(reason) held.push({collection:name,id,reason});
      else valid.set(id,row);
    }
    // Fixed-point removal for missing or held dependencies, plus cycle isolation.
    let changed=true;
    while(changed){
      changed=false;
      for(const [id,row] of valid){
        const deps=row.depends_on||[];
        if(deps.some(dep=>!valid.has(dep))){
          valid.delete(id);held.push({collection:name,id,reason:'DEPENDENCY_HELD_OR_MISSING'});changed=true;
        }
      }
    }
    const discovered=new Set(), cycles=new Set();
    // Kahn's algorithm avoids recursion limits and holds cycles plus dependants.
    const reverse=new Map([...valid.keys()].map(x=>[x,[]]));
    const degree=new Map([...valid.keys()].map(x=>[x,0]));
    for(const [id,row] of valid) for(const dep of new Set(row.depends_on||[])){
      degree.set(id,degree.get(id)+1);reverse.get(dep).push(id);
    }
    const ready=[...degree].filter(([,n])=>n===0).map(([id])=>id);
    for(let ix=0;ix<ready.length;ix++){
      const node=ready[ix];discovered.add(node);
      for(const dependent of reverse.get(node)){
        degree.set(dependent,degree.get(dependent)-1);
        if(degree.get(dependent)===0) ready.push(dependent);
      }
    }
    for(const id of valid.keys())if(!discovered.has(id))cycles.add(id);
    for(const id of cycles){valid.delete(id);held.push({collection:name,id,reason:'DEPENDENCY_CYCLE_OR_DEPENDENT'});}
    preserved[name]=[...valid.values()].map(row=>{
      if(name==='remedies'&&row.status==='INDEPENDENTLY_VERIFIED'){
        // Source reference strings do not authenticate themselves; fail-closed.
        sourceAttestationsDowngraded++;
        return {...row,status:row.source_refs.length?'DOCUMENTED':'CLAIMED'};
      }
      if(name==='records'&&row.evidence_status==='INDEPENDENTLY_CHECKED'){
        reportedRecordAttestations.set(row.id,row.evidence_status);
        return {...row,evidence_status:'DOCUMENT_LINKED'};
      }
      return row;
    });
  }
  const r=summarizeContext({...input,...preserved},true);
  for(const row of r.documentary_gaps){
    if(reportedRecordAttestations.has(row.record_id)){
      row.reported_verification_status=reportedRecordAttestations.get(row.record_id);
    }
  }
  return {...r,isolation_report:{mode:'ITEM_LEVEL_SYNTHETIC_RESEARCH',revision:'P02-CC04-PROVENANCE-FOLLOWUP-1',held,
    accepted_counts:Object.fromEntries(names.map(name=>[name,preserved[name].length])),
    source_truth_authenticated:false,remedy_attestations_downgraded:sourceAttestationsDowngraded,
    record_attestations_downgraded:reportedRecordAttestations.size,
    independent_valid_work_preserved:Object.values(preserved).some(rows=>rows.length>0),provenance_strict_policy:'UNVERIFIED_UNTIL_INDEPENDENT_AUTHENTICATION',
    reported_states_are_not_judicial_findings:true}};
}
