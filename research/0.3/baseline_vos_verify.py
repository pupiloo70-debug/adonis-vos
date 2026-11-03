"""Adonis VOS 0.3 candidate: deterministic, offline evidence checks. No autonomous legal findings."""
import json,re,sys
from pathlib import Path

def verify(item):
    kind=item.get('kind'); claim=item.get('claim',''); evidence=item.get('evidence',{})
    flags=[]; status='NEEDS_REVIEW'; action='HUMAN_REVIEW'
    if kind=='case_law':
        required=('court','case_number','decision_date','primary_text')
        missing=[k for k in required if not evidence.get(k)]
        if missing: flags.append({'code':'PRIMARY_SOURCE_MISSING','fields':missing});status='UNVERIFIED';action='BLOCK_CITATION'
        else:
            quote=item.get('quoted_text','')
            if quote and quote not in evidence['primary_text']:
                flags.append({'code':'QUOTE_NOT_IN_SOURCE'});status='MISQUOTED';action='BLOCK_CITATION'
            else: status='SOURCE_MATCH_CANDIDATE';action='HUMAN_LEGAL_SCOPE_REVIEW'
    elif kind=='paper':
        required=('title','authors','year','primary_text','population','intervention','outcome')
        missing=[k for k in required if not evidence.get(k)]
        if missing:flags.append({'code':'STUDY_FIELDS_MISSING','fields':missing});status='UNVERIFIED';action='BLOCK_EVIDENCE_CLAIM'
        else:
            for field in ('population','intervention','outcome'):
                expected=item.get('claim_scope',{}).get(field)
                if expected and expected!=evidence.get(field):flags.append({'code':'SCOPE_MISMATCH','field':field,'claim':expected,'study':evidence.get(field)})
            if flags:status='MISAPPLIED_EVIDENCE';action='REVISE_CLAIM'
            else:status='SOURCE_MATCH_CANDIDATE';action='HUMAN_METHOD_REVIEW'
    elif kind=='plaintiff_draft':
        phrases=('입증되는 것은 아니다','확정된 것은 아니다','인과관계가 입증되지','책임이 인정되는 것은 아니다')
        hits=[p for p in phrases if p in claim]
        if hits and item.get('purpose') in ('plaintiff_argument','evidence_request'):
            flags.append({'code':'PREEMPTIVE_CONCESSION_REVIEW','matches':hits});status='CONCESSION_RISK';action='SEPARATE_PRIVILEGED_RISK_REVIEW'
        if item.get('evidence_control')=='institution' and not item.get('disclosure_request'):
            flags.append({'code':'EVIDENCE_ASYMMETRY_NOT_ADDRESSED'});status='NEEDS_REVIEW';action='ADD_DISCLOSURE_QUESTION'
        if not flags:status='NO_RULE_HIT';action='HUMAN_REVIEW'
    else:flags.append({'code':'UNKNOWN_KIND'});status='UNVERIFIED'
    return {'id':item.get('id'),'status':status,'flags':flags,'action':action,'human_approval_required':True,'source_verified_externally':False,'total_score':None}

def main():
    data=json.load(open(sys.argv[1],encoding='utf-8'))
    out=[verify(x) for x in data['items']]
    print(json.dumps({'schema':'ADONIS-VOS-0.3-CANDIDATE','results':out,'total_score':None},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
