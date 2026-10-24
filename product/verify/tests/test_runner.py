"""Unit tests for the result taxonomy, the runner's failure taxonomy, the
manifest loaders, the install identity reader and the write-scope guard.

These tests do **not** need a Beyond Compare installation except where marked;
the Oracle-dependent behaviour is covered by ``test_oracle_live.py``.

Run:  python -m pytest product\\verify\\tests -q
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from harness import candidate as cand_mod      # noqa: E402
from harness import installs as inst_mod       # noqa: E402
from harness import manifests as man_mod       # noqa: E402
from harness import normalize as norm_mod      # noqa: E402
from harness import runner as run_mod          # noqa: E402
from harness.taxonomy import (                 # noqa: E402
    Verdict, TestResult, summarize, summarize_by,
)


# --------------------------------------------------------------------------
# 1. verdicts are disjoint and non-passes are never folded in
# --------------------------------------------------------------------------
def _r(v: Verdict, tid="t", suite="anchor", subject="oracle", ver="1.0") -> TestResult:
    return TestResult(test_id=tid, suite=suite, verdict=v, subject=subject,
                      oracle_version=ver)


def test_every_verdict_is_distinct():
    vals = [v.value for v in Verdict]
    assert len(vals) == len(set(vals))
    assert set(vals) == {"pass", "fail", "error", "missing_output", "timeout",
                         "unparseable", "not_run"}


def test_summarize_counts_are_exhaustive():
    results = [_r(v) for v in Verdict]
    s = summarize(results)
    assert s["total"] == len(results) == 7
    assert s["pass"] == 1
    assert s["fail"] == 1
    assert s["error"] == 1
    assert s["missing_output"] == 1
    assert s["timeout"] == 1
    assert s["unparseable"] == 1
    assert s["not_run"] == 1


def test_error_is_never_counted_as_a_pass():
    s = summarize([_r(Verdict.ERROR), _r(Verdict.MISSING_OUTPUT),
                   _r(Verdict.TIMEOUT), _r(Verdict.UNPARSEABLE),
                   _r(Verdict.NOT_RUN)])
    assert s["pass"] == 0
    assert s["compared"] == 0
    assert s["pass_rate_of_total"] == 0.0
    assert s["pass_rate_of_compared"] is None   # nothing was compared


def test_compared_rate_excludes_unexecuted():
    s = summarize([_r(Verdict.PASS), _r(Verdict.PASS), _r(Verdict.FAIL),
                   _r(Verdict.ERROR), _r(Verdict.NOT_RUN)])
    assert s["compared"] == 3
    assert s["pass_rate_of_compared"] == round(2 / 3, 4)
    assert s["pass_rate_of_total"] == round(2 / 5, 4)


def test_empty_result_set_is_not_a_pass():
    s = summarize([])
    assert s["total"] == 0 and s["pass"] == 0
    assert s["pass_rate_of_total"] is None


def test_summarize_by_groups_without_merging_versions():
    results = [
        _r(Verdict.PASS, ver="5.2.1.32035"),
        _r(Verdict.FAIL, ver="5.2.1.32035"),
        _r(Verdict.PASS, ver="5.2.6.32774"),
    ]
    by = summarize_by(results, lambda x: x.oracle_version)
    assert by["5.2.1.32035"]["pass"] == 1 and by["5.2.1.32035"]["fail"] == 1
    assert by["5.2.6.32774"]["pass"] == 1 and by["5.2.6.32774"]["fail"] == 0


# --------------------------------------------------------------------------
# 2. manifest loaders read the real, read-only assets correctly
# --------------------------------------------------------------------------
def test_anchor_manifest_loads_every_entry():
    # The anchor manifest is append-only (45 M1 + M2/m53/m55 waves).  The
    # guard is loader fidelity -- one case per manifest entry, names unique --
    # not a frozen count that goes stale every time the corpus grows.
    raw = json.loads((man_mod.GOLDEN_DIR / "manifest.json")
                     .read_text(encoding="utf-8"))
    anchors = man_mod.load_anchors()
    assert len(anchors) == len(raw)
    assert len({a.name for a in anchors}) == len(anchors)


def test_anchor_options_are_recovered_from_note():
    anchors = {a.name: a for a in man_mod.load_anchors()}
    assert anchors["opt-display-matches"].options == "display-matches"
    assert anchors["opt-display-context"].options == "display-context"
    assert anchors["opt-display-mismatches"].options == "display-mismatches"
    assert anchors["opt-display-all"].options == "display-all"
    assert anchors["opt-ignore-unimportant"].options == "ignore-unimportant"
    # anchors without an options: note must not invent one
    assert anchors["al-insert"].options is None
    assert anchors["ws-trailing"].options is None


def test_anchor_manifest_is_not_rewritten_by_loading():
    p = man_mod.GOLDEN_DIR / "manifest.json"
    before = p.read_bytes()
    man_mod.load_anchors()
    assert p.read_bytes() == before


def test_layout_manifest_loads_every_entry():
    # 30 M1 entries (5 txt cases x 6 layouts) + the M2 comments-summary case.
    cases = man_mod.load_layouts()
    assert len(cases) == 31
    assert len({c.layout for c in cases}) == 6
    assert len({c.case for c in cases}) == 6


def test_layout_fixture_paths_are_derived_not_hardcoded():
    for c in man_mod.load_layouts():
        assert c.left.name == f"{c.case}-L.{c.ext}"
        assert c.right.name == f"{c.case}-R.{c.ext}"


def test_folder_case_loads_and_preserves_the_stored_broken_manifest():
    cases = man_mod.load_folder_cases()
    assert len(cases) == 1
    c = cases[0]
    assert c.left.is_dir() and c.right.is_dir()
    # The stored manifest records the pre-fix failure; it must be surfaced as
    # historical evidence, never regenerated.
    assert c.stored_manifest_entries, "stored report manifest should load"
    assert c.stored_manifest_entries.get("xml", {}).get("exit") == 106
    assert c.stored_manifest_entries.get("xml", {}).get("bytes") == 0


def test_statuses_from_xml_matches_manifest():
    a = {x.name: x for x in man_mod.load_anchors()}["al-insert"]
    text = a.golden_report.read_text(encoding="utf-8", errors="replace")
    assert man_mod.statuses_from_xml(text) == a.statuses


# --------------------------------------------------------------------------
# 3. write-scope guard
#
# The guard is an ALLOW-LIST: a target must live under a writable root, and is
# refused if it also falls in a protected tree / file pattern / the harness's
# own source. These tests pin both halves.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("target", [
    # the original set
    r"D:\Rea\verify\golden\manifest.json",
    r"D:\Rea\verify\layouts\x.txt",
    r"D:\Rea\clone\target\debug\bcx.exe",
    r"D:\Rea\extracted\anything.json",
    r"D:\Rea\specs\text\README.md",
    r"D:\BCompare\BCompare\BCompare.exe",
    r"D:\bc-official\app\BCompare.exe",
    # newly protected by the hardening fix
    r"D:\Rea\tools\x.txt",
    r"D:\Rea\tools\_audit\x.txt",
    r"D:\Rea\tools\_audit\probe-anchor-both.py",
    r"D:\Rea\tools\bc-verify.py",
    r"D:\Rea\tools\_audit\anchors\summary.json",
    r"D:\Rea\ghidra-project\x.txt",
    r"D:\Rea\help\x.html",
    r"D:\Rea\rea-snapshot\x.txt",
    r"D:\Rea\product\docs\x.md",
    r"D:\Rea\product\docs\00-current-state.md",
    # top-level reports
    r"D:\Rea\report-algorithm.md",
    r"D:\Rea\report-final.md",
    r"D:\Rea\report-verified.md",
    r"D:\Rea\report-anything-new.md",
    # the harness's own source tree
    r"D:\Rea\product\verify\harness\runner.py",
    r"D:\Rea\product\verify\tests\test_runner.py",
    r"D:\Rea\product\verify\README.md",
    r"D:\Rea\product\verify\MANIFEST-FORMAT.md",
    # never-enumerated paths: the allow-list must catch these too
    r"D:\Rea\some-new-directory\x.txt",
    r"D:\Rea\x.txt",
    r"D:\somewhere-else\entirely\x.txt",
])
def test_write_guard_refuses_everything_outside_the_results_tree(target):
    with pytest.raises(RuntimeError, match="refusing to write"):
        run_mod.assert_writable(pathlib.Path(target))


@pytest.mark.parametrize("target", [
    r"D:\Rea\product\verify\runs\whatever\a.txt",
    r"D:\Rea\product\verify\runs\A1-final\report.json",
    r"D:\Rea\product\verify\runs\A1-final\raw\anchor-current-al-insert.xml",
    r"D:\Rea\product\verify\runs\A1-final\scripts\s.txt",
    r"D:\Rea\product\verify\runs\A1-final\normalized\x.txt",
    r"D:\Rea\product\verify\runs\x.txt",
])
def test_write_guard_allows_the_harness_results_tree(target):
    run_mod.assert_writable(pathlib.Path(target))


def test_write_guard_allows_a_caller_supplied_results_root(tmp_path):
    """``RunConfig.out`` passes its own results_dir, which must be honoured."""
    run_mod.assert_writable(tmp_path / "run" / "raw" / "x.xml",
                            allowed_roots=(tmp_path / "run",))


@pytest.mark.parametrize("bad_root, target, rule", [
    # A results root pointed AT a protected tree must still be refused: the
    # allow-list alone would otherwise let a mis-set root through.
    (r"D:\Rea\verify\golden", r"D:\Rea\verify\golden\x.txt", "read-only asset tree"),
    (r"D:\Rea\tools\_audit", r"D:\Rea\tools\_audit\x.txt", "read-only asset tree"),
    (r"D:\Rea\tools", r"D:\Rea\tools\x.txt", "read-only asset tree"),
    (r"D:\Rea\ghidra-project", r"D:\Rea\ghidra-project\x", "read-only asset tree"),
    (r"D:\Rea\clone", r"D:\Rea\clone\x", "read-only asset tree"),
    (r"D:\Rea\product\verify\harness", r"D:\Rea\product\verify\harness\x.py",
     "harness source tree"),
    (r"D:\Rea\product\verify\tests", r"D:\Rea\product\verify\tests\x.py",
     "harness source tree"),
    (r"D:\Rea", r"D:\Rea\report-final.md", "read-only file"),
])
def test_write_guard_rules_still_fire_when_the_results_root_is_bad(
        bad_root, target, rule):
    """Defence in depth: a mis-configured results root cannot reach protected data."""
    with pytest.raises(RuntimeError, match=rule):
        run_mod.assert_writable(pathlib.Path(target),
                                allowed_roots=(pathlib.Path(bad_root),))


def test_write_guard_protects_tools_audit_specifically():
    """Regression pin for the defect found in review.

    ``tools/_audit/`` was writable before this fix because the deny-list did not
    mention ``D:\\Rea\\tools``. It holds the audit probes and their output.
    """
    for target in (r"D:\Rea\tools\_audit\probe-current-oracle.py",
                   r"D:\Rea\tools\_audit\summary.json",
                   r"D:\Rea\tools\_audit\anchors\x.xml"):
        with pytest.raises(RuntimeError):
            run_mod.assert_writable(pathlib.Path(target))
    assert pathlib.Path(r"D:\Rea\tools").resolve() in \
        [p.resolve() for p in run_mod.READ_ONLY_ROOTS]


def test_write_guard_protects_top_level_reports_by_pattern():
    """A newly written ``report-*.md`` is protected without a code change."""
    assert r"D:\Rea\report-*.md" in run_mod.READ_ONLY_FILE_PATTERNS
    for name in ("report-algorithm.md", "report-brand-new.md"):
        with pytest.raises(RuntimeError, match="read-only file"):
            run_mod.assert_writable(pathlib.Path(rf"D:\Rea\{name}"),
                                    allowed_roots=(pathlib.Path(r"D:\Rea"),))


def test_write_guard_docstring_does_not_overclaim():
    """The docstring must describe the allow-list, not 'anywhere outside'."""
    doc = run_mod.assert_writable.__doc__ or ""
    assert "allow-list" in doc.lower()
    assert "anywhere outside" not in doc.lower()


# --------------------------------------------------------------------------
# 4. candidate adapter is declarative and labels the prototype honestly
# --------------------------------------------------------------------------
def test_prototype_candidate_is_labelled_not_the_product():
    cands = cand_mod.load_candidates()
    bcx = cands["bcx-prototype"]
    assert bcx.is_product is False
    assert "NOT the product" in bcx.label or "not the product" in bcx.note.lower()
    assert "prototype" in bcx.kind


def test_product_candidate_seam_is_declared_and_now_built():
    # Milestone M1 (task A-2) built the product binary at the seam path, so the
    # reserved entry is now available.  Before M1 this test asserted the entry
    # was declared-but-absent; that not_run behaviour is still covered by
    # test_runner_marks_unavailable_candidate_as_not_run, which uses a
    # synthetic absent candidate instead of depending on reacmp's lifecycle.
    cands = cand_mod.load_candidates()
    prod = cands["reacmp"]
    assert prod.is_product is True
    assert prod.available is True
    assert prod.path.endswith(r"product\cli\target\release\reacmp.exe")


def test_candidate_command_is_built_from_config_not_from_code():
    cands = cand_mod.load_candidates()
    cmd = cands["bcx-prototype"].command(left="L", right="R", output="O",
                                         options="display-all")
    assert cmd[0].endswith("bcx.exe")
    assert cmd[1:4] == ["L", "R", "O"]
    assert "--opt=display-all" in cmd


def test_candidate_layout_flag_only_added_for_layouts():
    cands = cand_mod.load_candidates()
    c = cands["bcx-prototype"]
    assert not any(x.startswith("--layout") for x in
                   c.command(left="L", right="R", output="O"))
    assert any(x.startswith("--layout") for x in
               c.command(left="L", right="R", output="O", layout="patch"))


def test_candidate_config_file_can_add_a_new_entry(tmp_path):
    cfg = tmp_path / "candidates.json"
    cfg.write_text(json.dumps({
        "my-product": {
            "label": "my product", "kind": "product", "is_product": True,
            "path": r"D:\nowhere\none.exe",
            "argv": ["{path}", "--left", "{left}", "--right", "{right}",
                     "--out", "{output}"],
        }
    }), encoding="utf-8")
    cands = cand_mod.load_candidates(cfg)
    c = cands["my-product"]
    assert c.is_product
    assert c.command(left="L", right="R", output="O") == [
        r"D:\nowhere\none.exe", "--left", "L", "--right", "R", "--out", "O"]


# --------------------------------------------------------------------------
# 5. install identity is measured, not assumed
# --------------------------------------------------------------------------
def test_identity_reads_versions_from_the_binaries():
    inst = inst_mod.discover()
    if not pathlib.Path(inst["current"].app_path).exists():
        pytest.skip("current install not present")
    # Measured values, asserted against the documented identity.
    assert inst["current"].app_version == "5.2.1.32035"
    assert inst["current"].locale == "zh"


def test_pe_version_parser_rejects_non_pe(tmp_path):
    f = tmp_path / "not_a_pe.bin"
    f.write_bytes(b"\x00" * 128)
    assert inst_mod.pe_file_version(f) == ""


def test_pe_version_parser_rejects_truncated_pe(tmp_path):
    f = tmp_path / "trunc.bin"
    f.write_bytes(b"MZ" + b"\x00" * 62)
    assert inst_mod.pe_file_version(f) == ""


def test_grouped_hex_is_eight_digit_groups():
    h = "0123456789abcdef" * 4
    grouped = inst_mod.grouped_hex(h)
    assert grouped.split() == [h[i:i + 8] for i in range(0, 64, 8)]
    assert len(grouped.split()) == 8
    assert grouped.replace(" ", "") == h


def test_identity_report_prints_hash_in_groups_not_one_line():
    """Guards the environment quirk: long hex must be grouped to be read back."""
    inst = {"k": inst_mod.InstallIdentity(
        key="k", label="l", oracle_path="o", app_path="a",
        oracle_sha256="ab" * 32, app_sha256="cd" * 32)}
    txt = inst_mod.identity_report(inst)
    assert (" ".join(["ab" * 4] * 8)) in txt
    # A single unbroken 64-char run must not appear.
    assert "ab" * 32 not in txt


# --------------------------------------------------------------------------
# 6. runner-level failure classification (no Oracle needed)
# --------------------------------------------------------------------------
class _Cfg:
    def __init__(self, d):
        self.results_dir = d


def _fake_install(**kw) -> inst_mod.InstallIdentity:
    base = dict(key="current", label="fake", oracle_path=r"D:\nope\BComp.com",
                app_path=r"D:\nope\BCompare.exe", app_version="0.0.0.0",
                oracle_version="0.0.0.0")
    base.update(kw)
    return inst_mod.InstallIdentity(**base)


def test_runner_records_missing_fixture_as_not_run(tmp_path, monkeypatch):
    broken = man_mod.AnchorCase(
        name="ghost", unit="x", note="", left=pathlib.Path(r"D:\nope\L.txt"),
        right=pathlib.Path(r"D:\nope\R.txt"),
        golden_report=pathlib.Path(r"D:\nope\R.xml"), statuses=[], options=None)
    monkeypatch.setattr(man_mod, "load_anchors", lambda *a, **k: [broken])

    cfg = run_mod.RunConfig(results_dir=tmp_path / "res",
                            installs={"current": _fake_install()}, candidates={})
    runner = run_mod.Runner(cfg, log=lambda *_: None)
    out = runner.run_anchors("current")
    assert len(out) == 1
    assert out[0].verdict is Verdict.NOT_RUN
    assert "fixture missing" in out[0].detail


def test_runner_never_writes_outside_its_results_dir(tmp_path):
    cfg = run_mod.RunConfig(results_dir=tmp_path / "res", installs={}, candidates={})
    run_mod.Runner(cfg, log=lambda *_: None)
    assert (tmp_path / "res" / "scripts").is_dir()
    assert (tmp_path / "res" / "raw").is_dir()
    assert (tmp_path / "res" / "normalized").is_dir()


def test_runner_marks_nonzero_oracle_exit_as_error(tmp_path, monkeypatch):
    """A non-zero Oracle exit must be ERROR, never MISSING_OUTPUT or PASS."""
    anchor = man_mod.load_anchors()[0]
    monkeypatch.setattr(man_mod, "load_anchors", lambda *a, **k: [anchor])

    class _Run:
        timed_out = False
        exit_code = 106
        report_exists = False
        report_bytes = 0
        report_path = str(tmp_path / "never.xml")
        elapsed_s = 0.1
        containment = "job-object"
        tree_killed = False

    def _fake_oracle_run(*a, **k):
        return _Run()

    monkeypatch.setattr(run_mod.oracle_mod, "run", _fake_oracle_run)
    monkeypatch.setattr(run_mod.oracle_mod, "write_script",
                        lambda p, lines: pathlib.Path(p))

    cfg = run_mod.RunConfig(results_dir=tmp_path / "res",
                            installs={"current": _fake_install()}, candidates={})
    runner = run_mod.Runner(cfg, log=lambda *_: None)
    out = runner.run_anchors("current")
    assert len(out) == 1
    assert out[0].verdict is Verdict.ERROR
    assert "106" in out[0].detail
    assert summarize(out)["pass"] == 0


def test_runner_marks_zero_exit_without_report_as_missing_output(tmp_path, monkeypatch):
    anchor = man_mod.load_anchors()[0]
    monkeypatch.setattr(man_mod, "load_anchors", lambda *a, **k: [anchor])

    class _Run:
        timed_out = False
        exit_code = 0
        report_exists = False
        report_bytes = 0
        report_path = str(tmp_path / "never.xml")
        elapsed_s = 0.1
        containment = "job-object"
        tree_killed = False

    monkeypatch.setattr(run_mod.oracle_mod, "run", lambda *a, **k: _Run())
    monkeypatch.setattr(run_mod.oracle_mod, "write_script",
                        lambda p, lines: pathlib.Path(p))

    cfg = run_mod.RunConfig(results_dir=tmp_path / "res",
                            installs={"current": _fake_install()}, candidates={})
    runner = run_mod.Runner(cfg, log=lambda *_: None)
    out = runner.run_anchors("current")
    assert out[0].verdict is Verdict.MISSING_OUTPUT
    assert summarize(out)["pass"] == 0


def test_runner_marks_timeout_as_timeout(tmp_path, monkeypatch):
    anchor = man_mod.load_anchors()[0]
    monkeypatch.setattr(man_mod, "load_anchors", lambda *a, **k: [anchor])

    class _Run:
        timed_out = True
        exit_code = -1
        report_exists = False
        report_bytes = 0
        report_path = str(tmp_path / "never.xml")
        elapsed_s = 5.0
        containment = "job-object"
        tree_killed = True

    monkeypatch.setattr(run_mod.oracle_mod, "run", lambda *a, **k: _Run())
    monkeypatch.setattr(run_mod.oracle_mod, "write_script",
                        lambda p, lines: pathlib.Path(p))

    cfg = run_mod.RunConfig(results_dir=tmp_path / "res",
                            installs={"current": _fake_install()}, candidates={})
    runner = run_mod.Runner(cfg, log=lambda *_: None)
    out = runner.run_anchors("current")
    assert out[0].verdict is Verdict.TIMEOUT
    assert summarize(out)["pass"] == 0


def test_runner_marks_unknown_xml_tag_as_unparseable(tmp_path, monkeypatch):
    """A format change must degrade to ``unparseable``, not to a silent pass."""
    anchor = man_mod.load_anchors()[0]
    monkeypatch.setattr(man_mod, "load_anchors", lambda *a, **k: [anchor])

    bad = tmp_path / "bad.xml"
    bad.write_text('<?xml version="1.0" encoding="utf-8"?>'
                   '<bcreport><brandnewtag/></bcreport>', encoding="utf-8")

    class _Run:
        timed_out = False
        exit_code = 0
        report_exists = True
        report_bytes = bad.stat().st_size
        report_path = str(bad)
        elapsed_s = 0.1
        containment = "job-object"
        tree_killed = False

    monkeypatch.setattr(run_mod.oracle_mod, "run", lambda *a, **k: _Run())
    monkeypatch.setattr(run_mod.oracle_mod, "write_script",
                        lambda p, lines: pathlib.Path(p))

    cfg = run_mod.RunConfig(results_dir=tmp_path / "res",
                            installs={"current": _fake_install()}, candidates={})
    runner = run_mod.Runner(cfg, log=lambda *_: None)
    out = runner.run_anchors("current")
    assert out[0].verdict is Verdict.UNPARSEABLE
    assert "unknown_xml_tag" in out[0].detail
    assert summarize(out)["pass"] == 0


def test_runner_marks_unavailable_candidate_as_not_run(tmp_path):
    # Uses a SYNTHETIC absent candidate: reacmp itself has been built since M1,
    # so the absent-candidate path must not depend on any real entry's absence.
    cfg_path = tmp_path / "candidates.json"
    cfg_path.write_text(json.dumps({
        "absent-product": {
            "label": "absent product", "kind": "product", "is_product": True,
            "path": r"D:\nowhere\none.exe",
        }}), encoding="utf-8")
    cands = cand_mod.load_candidates(cfg_path)
    assert cands["absent-product"].available is False
    cfg = run_mod.RunConfig(
        results_dir=tmp_path / "res", installs={},
        candidates=cands)
    runner = run_mod.Runner(cfg, log=lambda *_: None)
    out = runner.run_candidate_anchors("absent-product")
    assert out and all(r.verdict is Verdict.NOT_RUN for r in out)
    assert all("not available" in r.detail for r in out)
    assert summarize(out)["pass"] == 0
    assert all(r.subject == "candidate" for r in out)


def test_candidate_results_are_tagged_with_candidate_identity(tmp_path):
    cfg = run_mod.RunConfig(
        results_dir=tmp_path / "res", installs={},
        candidates=cand_mod.load_candidates())
    runner = run_mod.Runner(cfg, log=lambda *_: None)
    out = runner.run_candidate_anchors("reacmp")
    r = out[0]
    assert r.artifacts["is_product"] is True
    assert r.artifacts["candidate_key"] == "reacmp"
