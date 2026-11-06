"""Supplemental independent graph/quote checks with a valid primary quote control."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import time

with contextlib.redirect_stdout(io.StringIO()):
    import audit_probes as a

base = copy.deepcopy(a.FIXTURE)
base["facts"][0].update(quoted_text=base["facts"][0]["text"], source_locator="paragraph 1")
base["sources"]["S1"]["text"] = base["facts"][0]["text"]
rows = []
for mode in ("valid_quote", "source_cycle", "valid_diamond", "cross_case_diamond",
             "nested_alias_conflict", "partial_inline_scope", "deep_inline_scope",
             "unknown_ref", "primary_text_only", "invalid_primary_text", "empty_nested_ref"):
    p = copy.deepcopy(base)
    if mode == "source_cycle":
        p["sources"]["S1"]["source_ref"] = "S1"
    if mode in ("valid_diamond", "cross_case_diamond"):
        p["sources"]["S2"] = {**p["sources"]["S1"], "source_ref": "S4"}
        p["sources"]["S3"] = {**p["sources"]["S1"], "source_ref": "S4"}
        p["sources"]["S4"] = {**p["sources"]["S1"]}
        p["sources"]["S1"]["source_refs"] = ["S2", "S3"]
        if mode == "cross_case_diamond":
            p["sources"]["S4"]["case_id"] = "OTHER"
    if mode == "nested_alias_conflict":
        p["facts"][0]["evidence"] = {"case_id":p["case_id"], "track_id":p["track_id"], "procedure_id":"OTHER"}
    if mode == "partial_inline_scope":
        p["facts"][0]["evidence"] = {"case_id":p["case_id"]}
    if mode == "deep_inline_scope":
        child = {"source_ref":"S1"}
        for _ in range(70):
            child = {"child":child}
        p["facts"][0]["evidence"] = child
    if mode == "unknown_ref":
        p["facts"][0]["payload"] = {"support_ref":"S1"}
    if mode == "primary_text_only":
        p["sources"]["S1"]["primary_text"] = p["sources"]["S1"].pop("text")
    if mode == "invalid_primary_text":
        p["items"][0]["evidence"] = {"primary_text":123}
        p["items"][0].pop("source_ref")
    if mode == "empty_nested_ref":
        p["facts"][0]["evidence"] = {"source_ref":None}
    before = copy.deepcopy(p)
    start = time.monotonic()
    report = a.v.run_consistency_loop(p,a.NOW)
    fact = report["support_packet"]["fact_ledger"][0]
    allowed = mode in {"valid_quote", "valid_diamond", "primary_text_only", "invalid_primary_text"}
    passed = (fact["in_primary_paragraph"] is allowed
              and (fact["scope_review"]["status"] == "IN_SCOPE") is allowed
              and p == before and not a.v.invariants(report))
    if mode == "primary_text_only":
        passed &= fact["evidence_scrutiny"]["underlying_text_supplied"] is True
    if mode == "invalid_primary_text":
        passed &= report["results"][0]["evidence_scrutiny"]["underlying_text_supplied"] is False
    rows.append({"probe":mode, "passed":passed, "in_primary_paragraph":fact["in_primary_paragraph"],
                 "scope":fact["scope_review"]["status"], "milliseconds":round((time.monotonic()-start)*1000,2)})
print(json.dumps({"passed":sum(row["passed"] for row in rows),"total":len(rows),"results":rows},indent=2))
