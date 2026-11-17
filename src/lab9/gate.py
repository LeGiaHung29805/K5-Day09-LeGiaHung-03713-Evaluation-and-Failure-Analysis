"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, aggregate, load_spec, per_item
from lab9.graders import GRADERS


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and isfinite(value)


def _check_report(report: dict, spec: dict, name: str, problems: list[str]) -> dict:
    manifest, rows = report["manifest"], report["rows"]
    seeds = set(manifest["seeds"])
    indexed = {(r["item_id"], r["seed"]): frozenset(r.get("slices") or []) for r in rows}
    items = {item for item, _ in indexed}
    if (not rows or len(seeds) != len(manifest["seeds"]) or len(items) != manifest["items"]
            or len(rows) != len(indexed) or set(indexed) != {(i, s) for i in items for s in seeds}):
        problems.append(f"{name}: rows do not form the manifest item × seed grid")
    if "seeds" in spec and seeds != set(spec["seeds"]):
        problems.append(f"{name}: manifest seeds differ from the spec")
    if report.get("evaluator_failures"):
        problems.append(f"{name}: evaluator failures")

    metrics = report["metrics"]
    for key, value in metrics.items():
        if value is not None and not _finite(value):
            problems.append(f"{name}: non-finite or non-numeric metric {key}")
    graded = [m["id"] for m in spec["metrics"] if m["id"] in GRADERS]
    incomplete = [mid for mid in graded if any(not _finite(r.get(mid)) for r in rows)]
    if incomplete:
        problems.append(f"{name}: invalid or missing row scores for {', '.join(incomplete)}")
    if any("cost" in r and not _finite(r["cost"]) for r in rows):
        problems.append(f"{name}: invalid row cost")
    if rows and not incomplete and all(_finite(r.get("cost")) for r in rows):
        actual = aggregate(rows, graded, spec.get("pass_k", []))
        for key, value in actual.items():
            if key not in metrics or metrics[key] != value:
                problems.append(f"{name}: aggregate {key} differs from row scores")
    return indexed


def _ratchet(spec: dict, base_spec: dict) -> list[str]:
    problems = []
    for group, keys in (("metrics", ("id",)), ("slices", ("name", "metric"))):
        current = {tuple(entry[k] for k in keys): entry for entry in spec.get(group, [])}
        for previous in base_spec.get(group, []):
            key = tuple(previous[k] for k in keys)
            name = "/".join(key)
            entry = current.get(key)
            if entry is None:
                problems.append(f"ratchet: removed {name}")
                continue
            if previous.get("blocking") and not entry.get("blocking"):
                problems.append(f"ratchet: disabled blocking for {name}")
            old = previous.get("threshold", {}) if group == "metrics" else previous
            new = entry.get("threshold", {}) if group == "metrics" else entry
            for bound, direction in (("min", 1), ("max", -1), ("max_increase", -1)):
                if bound in old and (bound not in new or direction * new[bound] < direction * old[bound]):
                    problems.append(f"ratchet: loosened {bound} for {name}")
            if old.get("no_significant_drop") and not new.get("no_significant_drop"):
                problems.append(f"ratchet: removed paired CI requirement for {name}")
    return problems


def _paired_delta(a: dict, b: dict, spec: dict) -> tuple[float, float, float]:
    keys = sorted(a)
    bs = spec.get("bootstrap", {})
    return stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                  n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                                  confidence=bs.get("confidence", 0.95))


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems: list[str] = []
    pr_rows = _check_report(pr, spec, "PR", problems)
    base_rows = _check_report(base, base_spec or spec, "baseline", problems)
    if pr_rows.keys() != base_rows.keys():
        problems.append("PR and baseline have different (item_id, seed) pairs")
    elif pr_rows != base_rows:
        problems.append("PR and baseline have different slice tags")
    if base_spec and spec["eval_set_version"] == base_spec["eval_set_version"]:
        problems.extend(_ratchet(spec, base_spec))
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    for rule in spec.get("slices", []):
        name, metric = rule["name"], rule["metric"]
        key = f"slice:{name}/{metric}"
        a, b = per_item(pr, metric, name), per_item(base, metric, name)
        value = sum(a.values()) / len(a) if a else None
        failed = value is None or a.keys() != b.keys() or value < rule.get("min", float("-inf"))
        note = ""
        if a and a.keys() == b.keys() and rule.get("no_significant_drop"):
            delta, lo, hi = _paired_delta(a, b, spec)
            note = f" Δ {delta:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            failed = failed or hi < 0
        blocking = rule.get("blocking")
        if failed and blocking:
            blocked.append(key)
        verdict = ("BLOCK" if blocking else "warn") if failed else "ok"
        score = "missing" if value is None else f"{value:.4f}"
        lines.append(f"  {key:<32} {score}{note} {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            if not a or a.keys() != b.keys():
                verdict = "fail"
                note = "missing paired item scores"
            else:
                d, lo, hi = _paired_delta(a, b, spec)
                note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                if hi < 0:
                    verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
