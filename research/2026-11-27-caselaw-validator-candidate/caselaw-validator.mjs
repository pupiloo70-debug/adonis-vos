import {createHash} from 'node:crypto';
export const sha256 = s => createHash('sha256').update(s,'utf8').digest('hex');
// Local synthetic registry only. Never authenticates a live court source.
export function createSyntheticValidator(records) {
  const registry = structuredClone(records);
  return function validate(citations) {
    if (!Array.isArray(citations)) throw Error('INVALID_CITATIONS');
    const results = citations.map(c => {
      const reasons=[];
      if (!c || typeof c !== 'object') return {status:'BLOCKED',reasons:['INVALID_CITATION']};
      const matches=registry.filter(r=>r.id===c.id);
      const r=matches.length===1?matches[0]:null;
      if(!r) reasons.push('UNIQUE_SOURCE_NOT_FOUND');
      else {
        for(const k of ['court','date','jurisdiction','procedure','issue']) if(typeof c[k]!=='string'||!c[k]||c[k]!==r[k]) reasons.push('MISMATCH_'+k.toUpperCase());
        if(r.access!=='FULL_TEXT'||typeof r.text!=='string'||sha256(r.text)!==r.sha256) reasons.push('SOURCE_UNVERIFIED');
        if(r.currentness!=='CHECKED_SYNTHETIC') reasons.push('CURRENTNESS_UNVERIFIED');
        if(r.role!=='COURT_HOLDING') reasons.push('NOT_COURT_HOLDING');
        if(typeof c.quote!=='string'||!c.quote.trim()||c.quote!==r.holding||!r.text?.includes(c.quote)) reasons.push('HOLDING_MISMATCH');
        if(c.proposition!==r.proposition) reasons.push('PROPOSITION_MISMATCH');
        if(r.dissentRequired && c.dissent!==r.dissent) reasons.push('DISSENT_OMITTED');
      }
      return {id:typeof c.id==='string'?c.id:null,status:reasons.length?'BLOCKED':'SYNTHETIC_MATCH_ONLY',reasons,source_sha256:r?.sha256??null};
    });
    return {results,real_citation_authorized:false,total_score:null,legal_liability:'NOT_ADJUDICATED'};
  };
}
