"""Independent synthetic audit. Does not change candidate or contact any service."""
import copy
import importlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
v = importlib.import_module("vos_verify")
FIXTURE = json.loads((Path(__file__).parent / "fixture.json").read_text())
NOW = "2026-11-05T01:00:00+00:00"

def fixture():
    p = copy.deepcopy(FIXTURE)
    p["sources"]["X"] = {**p["sources"]["S1"], "case_id": "SYNTH-B", "text": "OTHER_CASE_ONLY"}
    return p

def held_fact(r):
    f = r["support_packet"]["fact_ledger"][0]
    return f["scope_review"]["status"] != "IN_SCOPE" and not f["in_primary_paragraph"]

def held_route(r):
    return (r["routes"][0]["scope_review"]["status"] != "IN_SCOPE"
            and not r["routes"][0]["review_triggered"]
            and not r["support_packet"]["route_register"][0]["operative_request"])

def held_node(r):
    return r["support_packet"]["review_nodes"]["lawyer"]["scope_review"]["status"] != "IN_SCOPE"

def not_primary(r):
    return not r["support_packet"]["fact_ledger"][0]["in_primary_paragraph"]

PROBES = []
def add(name, mutate, condition, controlled_rejection_ok=False):
    PROBES.append((name, mutate, condition, controlled_rejection_ok))

add("deep_fact_source_ref", lambda p: p["facts"][0].update(evidence={"citation":{"source_ref":"X"}}), held_fact)
add("list_fact_source_ref", lambda p: p["facts"][0].update(evidence={"citations":[{"source_ref":"X"}]}), held_fact)
add("dissent_previous_version_ref", lambda p: p["review_nodes"]["lawyer"]["disagreement"]["previous_version"].update(source_ref="X"), held_node)
add("dissent_list_ref", lambda p: p["review_nodes"]["lawyer"].update(disagreement=[{"text":"PRESERVE_DISSENT", "evidence":{"source_ref":"X"}}]), held_node)
add("nested_route_source_ref", lambda p: p["routes"][0].update(evidence={"source_ref":"X"}), held_route)
add("nested_route_explanation_ref", lambda p: p["routes"][0].update(alternative_explanations=[{"explanation_ref":"X"}]), held_route)
add("transitive_source_ref", lambda p: p["sources"]["S1"].update(source_ref="X"), held_fact)
add("deep_transitive_source_ref", lambda p: p["sources"]["S1"].update(provenance={"citations":[{"source_ref":"X"}]}), held_fact)
add("inline_evidence_scope", lambda p: p["facts"][0].update(evidence={"case_id":"SYNTH-B", "track_id":"CIVIL", "primary_text":"OTHER_CASE_ONLY"}), held_fact)
add("inline_dissent_scope", lambda p: p["review_nodes"]["lawyer"]["disagreement"]["previous_version"].update(case_id="SYNTH-B",track_id="CIVIL"), held_node)
add("missing_deep_ref", lambda p: p["facts"][0].update(evidence={"citation":{"source_ref":"DOES_NOT_EXIST"}}), held_fact)
for key, value in (("source_ref",0),("source_ref",[]),("source_refs","X"),("source_refs",{}),("reviewed_sources","X")):
    add("malformed_nested_"+key+"_"+type(value).__name__, lambda p,k=key,x=value: p["facts"][0].update(evidence={k:x}), held_fact, True)
add("opponent_record_role_conflict", lambda p: p["facts"][0].update(speaker="OPPONENT",statement_role="RECORD_STATEMENT",text="OPPONENT_CLAIM_NOT_ADMISSION"), not_primary)
add("missing_underlying_source_text", lambda p: p["sources"]["S1"].pop("text"), not_primary)
add("unrelated_underlying_source_text", lambda p: (p["sources"]["S1"].update(text="The sky is blue."), p["facts"][0].update(text="백신 인과관계와 기관 범죄가 확정되었다.")), not_primary)
add("institution_explanation_cannot_end_review", lambda p: p["routes"][0].update(itemized_explanation_complete=True), lambda r:r["routes"][0]["review_triggered"] and r["routes"][0]["explanation_sufficiency"]=="NOT_DETERMINED")
add("authority_input_cannot_approve", lambda p:p.update(approval_status_changed=True,total_score=99,deployment_status="DEPLOYED",external_action_performed=True), lambda r:r["approval_status_changed"] is False and r["total_score"] is None and r["deployment_status"]=="NOT_DEPLOYED" and r["external_action_performed"] is False)

rows = []
for name, mutate, condition, reject_ok in PROBES:
    p = fixture(); mutate(p); before = copy.deepcopy(p)
    try:
        r = v.run_consistency_loop(p, NOW)
        fact = r["support_packet"]["fact_ledger"][0]
        node = r["support_packet"]["review_nodes"]["lawyer"]
        row = {"probe":name,"passed":condition(r),"input_unchanged":p==before,
               "fact_scope":fact["scope_review"]["status"],"in_primary_paragraph":fact["in_primary_paragraph"],
               "route_scope":r["routes"][0]["scope_review"]["status"],
               "operative_request":r["support_packet"]["route_register"][0]["operative_request"],
               "expert_scope":node["scope_review"]["status"],"invariants":v.invariants(r),
               "dissent_preserved":node["disagreement"]==p["review_nodes"]["lawyer"]["disagreement"]}
    except ValueError as e:
        row = {"probe":name,"passed":reject_ok,"controlled_rejection":str(e),"input_unchanged":p==before}
    except Exception as e:
        row = {"probe":name,"passed":False,"uncontrolled_error":repr(e),"input_unchanged":p==before}
    rows.append(row)
print(json.dumps({"module":str(Path(v.__file__).resolve()),"version":v.VERSION,
                  "passed":sum(r["passed"] for r in rows),"total":len(rows),"results":rows},ensure_ascii=False,indent=2))
