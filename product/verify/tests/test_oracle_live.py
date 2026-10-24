"""Live integration tests -- these DO invoke the real Beyond Compare Oracle.

They are separated from the pure-unit tests because they need a local install
and take a few seconds.  They are still part of the default collection: the
project's acceptance rule is that infrastructure must be provable, and a
skipped-by-default integration test proves nothing.

If no install is present, each test skips with an explicit reason rather than
silently passing.

Run:  python -m pytest product\\verify\\tests -q
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from harness import installs as inst_mod     # noqa: E402
from harness import manifests as man_mod     # noqa: E402
from harness import normalize as norm_mod    # noqa: E402
from harness import oracle as orc            # noqa: E402
from harness import runner as run_mod        # noqa: E402
from harness.taxonomy import Verdict, summarize  # noqa: E402

INSTALLS = inst_mod.discover()
CURRENT = INSTALLS.get("current")


def _require_current():
    if CURRENT is None or not CURRENT.enabled:
        pytest.skip(f"current Oracle unavailable: "
                    f"{CURRENT.disabled_reason if CURRENT else 'not configured'}")
    return CURRENT


# --------------------------------------------------------------------------
# Oracle recipes
# --------------------------------------------------------------------------
def test_oracle_runs_in_place_and_reports_version(tmp_path):
    inst = _require_current()
    a = {x.name: x for x in man_mod.load_anchors()}["al-insert"]
    sp = orc.write_script(tmp_path / "s.txt", [orc.text_script("xml")])
    outp = tmp_path / "o.xml"
    run = orc.run(inst.oracle_path, sp, str(a.left), str(a.right), outp, timeout=120)
    assert run.exit_code == 0, f"exit {run.exit_code}: {run.stderr}"
    assert run.report_bytes > 0
    assert "filename1" in outp.read_text(encoding="utf-8", errors="replace")


def test_oracle_is_invoked_from_its_own_directory(tmp_path):
    inst = _require_current()
    a = {x.name: x for x in man_mod.load_anchors()}["al-insert"]
    sp = orc.write_script(tmp_path / "s.txt", [orc.text_script("xml")])
    run = orc.run(inst.oracle_path, sp, str(a.left), str(a.right),
                  tmp_path / "o.xml", timeout=120)
    assert pathlib.Path(run.command[0]).parent == pathlib.Path(inst.oracle_path).parent


def test_folder_report_without_load_fails_with_106(tmp_path):
    """The documented trap: folder-report alone exits 106 and writes 0 bytes."""
    inst = _require_current()
    cases = man_mod.load_folder_cases()
    if not cases:
        pytest.skip("no folder fixtures")
    c = cases[0]
    sp = orc.write_script(tmp_path / "s.txt",
                          ['folder-report layout:xml output-to:"%3" "%1" "%2"'])
    run = orc.run(inst.oracle_path, sp, str(c.left), str(c.right),
                  tmp_path / "o.xml", timeout=120)
    assert run.exit_code == 106
    assert run.report_bytes == 0


def test_folder_recipe_with_load_then_expand_succeeds(tmp_path):
    inst = _require_current()
    cases = man_mod.load_folder_cases()
    if not cases:
        pytest.skip("no folder fixtures")
    c = cases[0]
    sp = orc.write_script(tmp_path / "s.txt", list(orc.FOLDER_SCRIPT_LINES))
    outp = tmp_path / "o.xml"
    run = orc.run(inst.oracle_path, sp, str(c.left), str(c.right), outp, timeout=120)
    assert run.exit_code == 0
    assert run.report_bytes > 0
    text = outp.read_text(encoding="utf-8", errors="replace")
    assert "<foldercomp>" in text
    assert 'status="ltonly"' in text and 'status="rtonly"' in text


def test_missing_input_file_exits_107(tmp_path):
    inst = _require_current()
    sp = orc.write_script(tmp_path / "s.txt", [orc.text_script("xml")])
    run = orc.run(inst.oracle_path, sp, str(tmp_path / "no-L.txt"),
                  str(tmp_path / "no-R.txt"), tmp_path / "o.xml", timeout=120)
    assert run.exit_code == 107


def test_bad_layout_name_exits_106(tmp_path):
    inst = _require_current()
    a = {x.name: x for x in man_mod.load_anchors()}["al-insert"]
    sp = orc.write_script(tmp_path / "s.txt", [orc.text_script("zzz")])
    run = orc.run(inst.oracle_path, sp, str(a.left), str(a.right),
                  tmp_path / "o.xml", timeout=120)
    assert run.exit_code == 106


def test_oracle_run_is_deterministic_apart_from_timestamp(tmp_path):
    """The same case twice must normalise to the same thing."""
    inst = _require_current()
    a = {x.name: x for x in man_mod.load_anchors()}["al-swap-blocks"]
    sp = orc.write_script(tmp_path / "s.txt", [orc.text_script("xml")])
    outs = []
    for i in range(2):
        o = tmp_path / f"o{i}.xml"
        run = orc.run(inst.oracle_path, sp, str(a.left), str(a.right), o, timeout=120)
        assert run.exit_code == 0
        outs.append(norm_mod.normalize_xml(o.read_text(encoding="utf-8",
                                                       errors="replace")))
    assert outs[0].structure == outs[1].structure
    assert outs[0].text == outs[1].text


# --------------------------------------------------------------------------
# The M0 acceptance gate: 45/45 status sequences on the current install
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def anchor_run(tmp_path_factory):
    inst = _require_current()
    d = tmp_path_factory.mktemp("anchors")
    cfg = run_mod.RunConfig(results_dir=d, installs={"current": inst},
                            candidates={}, timeout=180)
    runner = run_mod.Runner(cfg, log=lambda *_: None)
    return runner.run_anchors("current")


def test_all_anchors_execute(anchor_run):
    # The anchor manifest is append-only; assert against it, not a frozen count.
    assert len(anchor_run) == len(man_mod.load_anchors())
    assert all(r.verdict is not Verdict.NOT_RUN for r in anchor_run), \
        "no anchor may be skipped: " + str(
            [(r.test_id, r.detail) for r in anchor_run
             if r.verdict is Verdict.NOT_RUN])


def test_m0_gate_all_status_sequences_on_current_install(anchor_run):
    s = summarize(anchor_run)
    assert s["error"] == 0, [r.test_id for r in anchor_run
                             if r.verdict is Verdict.ERROR]
    assert s["missing_output"] == 0
    assert s["timeout"] == 0
    assert s["unparseable"] == 0
    assert s["pass"] == len(man_mod.load_anchors()), [r.test_id for r in anchor_run
                             if r.verdict is not Verdict.PASS]


def test_every_anchor_result_records_the_required_fields(anchor_run):
    for r in anchor_run:
        assert r.test_id and r.suite == "anchor"
        assert r.left and r.right and r.raw_report
        assert r.oracle_path and r.oracle_version
        assert r.exit_code == 0
        assert r.elapsed_s >= 0
        assert r.normalizer_ruleset
        assert r.verdict is not None
        assert r.parsed["status_sequence_matches_golden"] is True


def test_raw_and_normalized_reports_are_both_kept(anchor_run):
    for r in anchor_run:
        assert pathlib.Path(r.raw_report).exists(), r.test_id
        assert pathlib.Path(r.normalized_report).exists(), r.test_id


def test_anchors_with_localisation_have_rules_recorded(anchor_run):
    by_id = {r.test_id: r for r in anchor_run}
    for tid in ("enc-latin1", "opt-display-matches", "opt-display-context",
                "opt-display-mismatches"):
        r = by_id[tid]
        assert r.rules_applied, f"{tid} needed normalisation rules but none recorded"


# --------------------------------------------------------------------------
# Layouts
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def layout_run(tmp_path_factory):
    inst = _require_current()
    d = tmp_path_factory.mktemp("layouts")
    cfg = run_mod.RunConfig(results_dir=d, installs={"current": inst},
                            candidates={}, timeout=180)
    runner = run_mod.Runner(cfg, log=lambda *_: None)
    return runner.run_layouts("current")


def test_all_layouts_execute(layout_run):
    # 30 M1 entries + the M2 comments-summary case.
    assert len(layout_run) == 31
    assert all(r.verdict is not Verdict.NOT_RUN for r in layout_run)


def test_layouts_normalize_to_golden_on_current_install(layout_run):
    s = summarize(layout_run)
    assert s["error"] == 0 and s["missing_output"] == 0
    assert s["pass"] == 31, [
        (r.test_id, r.verdict.value, r.detail) for r in layout_run
        if r.verdict is not Verdict.PASS]


# --------------------------------------------------------------------------
# Cross-locale corroboration: the label table is OBSERVED, not asserted
# --------------------------------------------------------------------------
def test_reference_install_label_pairs_corroborate_current_install(tmp_path):
    ref = INSTALLS.get("reference")
    if ref is None or not ref.enabled:
        pytest.skip("reference install unavailable")
    inst = _require_current()
    cfg = run_mod.RunConfig(results_dir=tmp_path, installs={"current": inst,
                                                            "reference": ref},
                            candidates={}, timeout=180,
                            include_reference_labels=True)
    runner = run_mod.Runner(cfg, log=lambda *_: None)
    runner.run_layouts("current")
    ref_results = runner.run_reference_corroboration()
    assert ref_results
    s = summarize(ref_results)
    assert s["pass"] == len(ref_results), [
        (r.test_id, r.detail) for r in ref_results if r.verdict is not Verdict.PASS]


# --------------------------------------------------------------------------
# Candidate adapter against the live prototype
# --------------------------------------------------------------------------
def test_prototype_candidate_runs_through_the_adapter(tmp_path):
    from harness import candidate as cand_mod
    cands = cand_mod.load_candidates()
    c = cands["bcx-prototype"]
    if not c.available:
        pytest.skip("prototype binary not built")
    cfg = run_mod.RunConfig(results_dir=tmp_path, installs={}, candidates=cands,
                            timeout=60)
    runner = run_mod.Runner(cfg, log=lambda *_: None)
    out = runner.run_candidate_anchors("bcx-prototype")
    n_anchors = len(man_mod.load_anchors())
    assert len(out) == n_anchors
    s = summarize(out)
    # Recorded, not asserted as a product claim: the prototype is not the product.
    assert s["pass"] + s["fail"] + s["error"] + s["missing_output"] + \
        s["timeout"] + s["unparseable"] + s["not_run"] == n_anchors
    assert all(r.subject == "candidate" for r in out)
    assert all(r.artifacts["is_product"] is False for r in out)


def test_mixed_side_by_side_known_difference_is_preserved(tmp_path):
    """``mixed-side-by-side`` must still FAIL for the prototype and must be
    labelled as a known difference -- never special-cased green."""
    from harness import candidate as cand_mod
    from harness import report as rep_mod
    cands = cand_mod.load_candidates()
    if not cands["bcx-prototype"].available:
        pytest.skip("prototype binary not built")
    cfg = run_mod.RunConfig(results_dir=tmp_path, installs={}, candidates=cands,
                            timeout=60)
    runner = run_mod.Runner(cfg, log=lambda *_: None)
    out = runner.run_candidate_layouts("bcx-prototype")
    by_id = {r.test_id: r for r in out}
    r = by_id["mixed-side-by-side"]
    assert r.verdict is Verdict.FAIL, (
        "the documented divergence must remain a failure; "
        f"got {r.verdict} / {r.detail}")
    assert "mixed-side-by-side" in rep_mod.KNOWN_DIFFERENCES
    assert rep_mod.KNOWN_DIFFERENCES_SCOPE["mixed-side-by-side"] == "candidate"


def test_candidate_other_layouts_are_not_affected_by_the_known_difference(tmp_path):
    from harness import candidate as cand_mod
    cands = cand_mod.load_candidates()
    if not cands["bcx-prototype"].available:
        pytest.skip("prototype binary not built")
    cfg = run_mod.RunConfig(results_dir=tmp_path, installs={}, candidates=cands,
                            timeout=60)
    runner = run_mod.Runner(cfg, log=lambda *_: None)
    out = runner.run_candidate_layouts("bcx-prototype")
    s = summarize(out)
    # The prototype misses mixed-side-by-side (the documented difference) and
    # comments-summary (it predates the M2 importance engine); everything
    # else passes.
    failed = {r.test_id for r in out if r.verdict is not Verdict.PASS}
    assert failed == {"mixed-side-by-side", "comments-summary"}, failed
    assert s["pass"] == 29


# --------------------------------------------------------------------------
# Reconciliation with the audit's independently measured figures
# --------------------------------------------------------------------------
def test_layout_agreement_reconciles_with_the_audit_figures(layout_run):
    """Reference: 30/30 after time-only stripping. Current: 5/30 (25 are zh labels).

    These are the figures product/docs/02-version-and-evidence.md reports from
    an independent probe. Reproducing them here is what shows the harness's
    normalizer is measuring the same thing the audit measured.
    """
    ref = INSTALLS.get("reference")
    if ref is None or not ref.enabled:
        pytest.skip("reference install unavailable")

    def counts(rs):
        n = len(rs)
        norm = sum(1 for r in rs if r.parsed.get("normalized_matches_golden"))
        time_only = sum(1 for r in rs
                        if r.parsed.get("raw_equal_after_volatile_only"))
        return n, norm, time_only

    n, norm, time_only = counts(layout_run)
    assert (n, norm, time_only) == (31, 31, 5), (
        f"current install layout agreement drifted: {n}/{norm}/{time_only}")

    import tempfile
    d = pathlib.Path(tempfile.mkdtemp(prefix="reflay-"))
    cfg = run_mod.RunConfig(results_dir=d, installs={"reference": ref},
                            candidates={}, timeout=180)
    ref_run = run_mod.Runner(cfg, log=lambda *_: None).run_layouts("reference")
    n2, norm2, time_only2 = counts(ref_run)
    # 31 entries after the M2 comments-summary addition (was 30/30/30).
    assert (n2, norm2, time_only2) == (31, 31, 31), (
        f"reference install layout agreement drifted: {n2}/{norm2}/{time_only2}")


def test_byte_equal_layouts_are_exactly_the_headerless_patch_layouts(layout_run):
    """The 5 byte-identical cases must be the 5 patch reports (no header)."""
    equal = [r.test_id for r in layout_run
             if r.parsed.get("raw_bytes_equal_golden")]
    assert sorted(equal) == sorted(
        ["identical-patch", "insert-patch", "mixed-patch",
         "orphans-patch", "similar-patch"]), equal
