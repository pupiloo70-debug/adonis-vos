"""Synthetic-only victim-origin effective-remedy trace. Research candidate, no legal determinations."""
from __future__ import annotations
from collections import defaultdict

ALLOWED_STATUSES = {'CLAIM','OBSERVED','VERIFIED','UNVERIFIED'}
PROCEDURAL = {'NOT_SUBMITTED','SUBMITTED','RESPONDED','PARTIAL','NOT_RESPONDED','WITHDRAWN'}

def _valid_id(v):
    return isinstance(v, str) and bool(v.strip())

def review(case):
    """Fail-closed attribution without deleting independently reviewable issues.

    The tool does not authenticate inputs; source links remain claims of provenance.
    """
    if not isinstance(case,dict) or case.get('synthetic') is not True:
        raise ValueError('SYNTHETIC_ONLY')
    if not all(_valid_id(case.get(k)) for k in ('case_id','track_id','subject_id')):
        raise ValueError('SCOPE_REQUIRED')
    items=case.get('issues',[])
    if not isinstance(items,list): raise ValueError('ISSUES_NOT_ARRAY')
    result=[];held=[];seen=set()
    for item in items:
        if not isinstance(item,dict) or not _valid_id(item.get('id')):
            held.append({'id': None,'reason':'INVALID_ISSUE'});continue
        key=item['id']
        if key in seen:
            held.append({'id':key,'reason':'DUPLICATE_ID'});continue
        seen.add(key)
        if any(item.get(k)!=case[k] for k in ('case_id','track_id','subject_id')):
            held.append({'id':key,'reason':'SCOPE_CONFLICT'});continue
        if not _valid_id(item.get('question')):
            held.append({'id':key,'reason':'QUESTION_MISSING'});continue
        claims=item.get('claims',[])
        if not isinstance(claims,list):held.append({'id':key,'reason':'CLAIMS_INVALID'});continue
        if any(not isinstance(c,dict) or not _valid_id(c.get('actor')) or not _valid_id(c.get('source_ref')) or c.get('evidence_state') not in ALLOWED_STATUSES for c in claims):
            held.append({'id':key,'reason':'CLAIM_PROVENANCE_INVALID'});continue
        submissions=item.get('submissions',[])
        responses=item.get('responses',[])
        if not isinstance(submissions,list) or not isinstance(responses,list):
            held.append({'id':key,'reason':'TRACK_INVALID'});continue
        if any(not isinstance(x,dict) or not _valid_id(x.get('source_ref')) or x.get('state') not in PROCEDURAL for x in submissions+responses):
            held.append({'id':key,'reason':'TRACK_PROVENANCE_INVALID'});continue
        if any(x.get('issue_id')!=key for x in submissions+responses):
            held.append({'id':key,'reason':'ISSUE_LINK_CONFLICT'});continue
        # An institution's unilateral conclusion cannot certify source verification.
        # A missing controller-owned record never becomes claimant failure.
        controller=item.get('controller',{})
        if not isinstance(controller,dict):
            held.append({'id':key,'reason':'CONTROLLER_INVALID'});continue
        if controller and (not _valid_id(controller.get('actor')) or not _valid_id(controller.get('material_ref'))):
            held.append({'id':key,'reason':'CONTROLLER_PROVENANCE_INVALID'});continue
        if not all(isinstance(x,bool) for x in (item.get('raw_evidence_verified',False),item.get('legal_conditions_verified',False))):
            held.append({'id':key,'reason':'VERIFICATION_FLAG_INVALID'});continue
        has_response=any(x['state'] in {'RESPONDED','PARTIAL'} for x in responses)
        has_submission=any(x['state'] in {'SUBMITTED','RESPONDED','PARTIAL'} for x in submissions)
        open_question=not (item.get('raw_evidence_verified') is True and item.get('legal_conditions_verified') is True and has_response)
        result.append({'id':key,'question':item['question'],
                       'evidence_status':'VERIFIED' if item.get('raw_evidence_verified') is True else 'UNVERIFIED',
                       'submission_status':'SUBMITTED' if has_submission else 'NOT_CONFIRMED',
                       'counsel_response':'DOCUMENTED_RESPONSE' if has_response else 'RESPONSE_NOT_CONFIRMED',
                       'counsel_misconduct':'NOT_DETERMINED',
                       'controller_explanation_due_for_review':bool(controller and controller.get('access_state') in {'WITHHELD','NOT_SEARCHED','UNKNOWN','LOST','DESTROYED'}),
                       'unresolved':open_question,
                       'next_review':'CHECK_SOURCE_AND_COUNTEREVIDENCE' if open_question else 'REVIEW_COMPLETE_FOR_THIS_QUESTION',
                       'legal_adverse_inference':'REVIEW_ONLY' if item.get('legal_conditions_verified') is True and item.get('raw_evidence_verified') is True else 'NOT_EVALUATED'})
    return {'status':'RESEARCH_ONLY','accepted':result,'held':held,
            'total_score':None,'automatic_guilt':False,'automatic_immunity':False,'external_action':False,
            'approval_state_changed':False,'default_path_connected':False}
