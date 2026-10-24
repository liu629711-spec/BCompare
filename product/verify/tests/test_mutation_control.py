"""End-to-end mutation controls.

``test_normalize.py`` proves the normalizer does not erase differences at the
unit level.  These tests prove the same property **through the runner**, using a
perturbed copy of a real golden report: the Oracle output is real, the golden is
real, and only the golden has been mutated.  If normalization were too
aggressive, these tests would flip to ``pass`` and fail the build.

Every test here asserts the *negative* outcome: a mutation must remain visible.

Run:  python -m pytest product\\verify\\tests -q
"""

from __future__ import annotations

import copy
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from harness import installs as inst_mod     # noqa: E402
from harness import manifests as man_mod     # noqa: E402
from harness import normalize as norm_mod    # noqa: E402
from harness import runner as run_mod        # noqa: E402
from harness.taxonomy import Verdict         # noqa: E402

INSTALLS = inst_mod.discover()
CURRENT = INSTALLS.get("current")


def _require_current():
    if CURRENT is None or not CURRENT.enabled:
        pytest.skip("current Oracle unavailable")
    return CURRENT


def _write_bytes(path: pathlib.Path, text: str) -> pathlib.Path:
    """Write a mutated fixture without newline translation.

    ``Path.write_text`` translates ``\\n`` to ``\\r\\n`` on Windows, which would
    silently rewrite the whole mutated report and destroy the CRLF shape the
    real Oracle produced. Mutation fixtures are therefore written as raw bytes.
    """
    path.write_bytes(text.encode("utf-8"))
    return path


def _runner(tmp_path):
    return run_mod.Runner(
        run_mod.RunConfig(results_dir=tmp_path, installs={"current": _require_current()},
                          candidates={}, timeout=120),
        log=lambda *_: None)


# --------------------------------------------------------------------------
# text layout body mutations
# --------------------------------------------------------------------------
def test_mutated_layout_body_still_fails(tmp_path, monkeypatch):
    cases = man_mod.load_layouts()
    victim = next(c for c in cases if c.name == "mixed-side-by-side")
    bad = tmp_path / "bad-golden.txt"
    _write_bytes(bad, norm_mod.read_report(victim.golden_report).replace(
        "real diff 9", "real diff 8"))
    mut = copy.copy(victim)
    mut.golden_report = bad
    monkeypatch.setattr(man_mod, "load_layouts", lambda *a, **k: [mut])

    out = _runner(tmp_path / "res").run_layouts("current")
    assert len(out) == 1
    assert out[0].verdict is Verdict.FAIL, (
        "normalization erased a body-text change: " + out[0].detail)
    assert "real diff 8" in out[0].detail


def test_mutated_layout_line_order_still_fails(tmp_path, monkeypatch):
    cases = man_mod.load_layouts()
    victim = next(c for c in cases if c.name == "mixed-interleaved")
    lines = norm_mod.read_report(victim.golden_report).split("\r\n")
    body = [i for i, l in enumerate(lines) if l and "file:" not in l]
    if len(body) < 3:
        pytest.skip("fixture too small to reorder")
    i, j = body[-3], body[-2]
    lines[i], lines[j] = lines[j], lines[i]
    bad = tmp_path / "reordered.txt"
    _write_bytes(bad, "\r\n".join(lines))
    mut = copy.copy(victim)
    mut.golden_report = bad
    monkeypatch.setattr(man_mod, "load_layouts", lambda *a, **k: [mut])

    out = _runner(tmp_path / "res").run_layouts("current")
    assert out[0].verdict is Verdict.FAIL, (
        "normalization erased a body line-order change: " + out[0].detail)


def test_mutated_layout_body_count_still_fails(tmp_path, monkeypatch):
    cases = man_mod.load_layouts()
    victim = next(c for c in cases if c.name == "mixed-patch")
    bad = tmp_path / "extra.txt"
    _write_bytes(bad, norm_mod.read_report(victim.golden_report) + "> extra\r\n")
    mut = copy.copy(victim)
    mut.golden_report = bad
    monkeypatch.setattr(man_mod, "load_layouts", lambda *a, **k: [mut])

    out = _runner(tmp_path / "res").run_layouts("current")
    assert out[0].verdict is Verdict.FAIL, (
        "normalization erased a body line-count change: " + out[0].detail)


# --------------------------------------------------------------------------
# XML mutations
# --------------------------------------------------------------------------
def test_mutated_xml_status_still_fails(tmp_path, monkeypatch):
    a = {x.name: x for x in man_mod.load_anchors()}["al-insert"]
    bad = tmp_path / "bad.xml"
    _write_bytes(bad, norm_mod.read_report(a.golden_report).replace(
        'status="rightorphan"', 'status="leftorphan"'))
    mut = copy.copy(a)
    mut.golden_report = bad
    monkeypatch.setattr(man_mod, "load_anchors", lambda *x, **k: [mut])

    out = _runner(tmp_path / "res").run_anchors("current")
    assert out[0].verdict is Verdict.FAIL, (
        "normalization erased an XML status change: " + out[0].detail)


def test_mutated_xml_line_id_still_fails(tmp_path, monkeypatch):
    a = {x.name: x for x in man_mod.load_anchors()}["al-insert"]
    bad = tmp_path / "bad.xml"
    _write_bytes(bad, norm_mod.read_report(a.golden_report).replace(
        'rtid="3"', 'rtid="4"'))
    mut = copy.copy(a)
    mut.golden_report = bad
    monkeypatch.setattr(man_mod, "load_anchors", lambda *x, **k: [mut])

    out = _runner(tmp_path / "res").run_anchors("current")
    assert out[0].verdict is Verdict.FAIL, (
        "normalization erased an XML line-number change: " + out[0].detail)


def test_mutated_xml_text_content_still_fails(tmp_path, monkeypatch):
    a = {x.name: x for x in man_mod.load_anchors()}["al-insert"]
    bad = tmp_path / "bad.xml"
    _write_bytes(bad, norm_mod.read_report(a.golden_report).replace(
        ">a</text>", ">A</text>"))
    mut = copy.copy(a)
    mut.golden_report = bad
    monkeypatch.setattr(man_mod, "load_anchors", lambda *x, **k: [mut])

    out = _runner(tmp_path / "res").run_anchors("current")
    assert out[0].verdict is Verdict.FAIL, (
        "normalization erased XML text content: " + out[0].detail)


def test_mutated_xml_element_order_still_fails(tmp_path, monkeypatch):
    a = {x.name: x for x in man_mod.load_anchors()}["al-insert"]
    src = norm_mod.read_report(a.golden_report)
    first = ('\t\t<linecomp status="same">\r\n'
             '\t\t\t<text ltid="1" rtid="1">a</text>\r\n'
             '\t\t</linecomp>\r\n')
    second = ('\t\t<linecomp status="rightorphan">\r\n'
              '\t\t\t<text rtid="2">b</text>\r\n'
              '\t\t</linecomp>\r\n')
    assert first in src and second in src, "fixture shape changed"
    bad = tmp_path / "reordered.xml"
    _write_bytes(bad, src.replace(first + second, second + first))
    mut = copy.copy(a)
    mut.golden_report = bad
    monkeypatch.setattr(man_mod, "load_anchors", lambda *x, **k: [mut])

    out = _runner(tmp_path / "res").run_anchors("current")
    assert out[0].verdict is Verdict.FAIL, (
        "normalization erased XML element ordering: " + out[0].detail)


def test_mutated_error_line_number_still_fails(tmp_path, monkeypatch):
    """The <error1> line number is data; only its label may be normalized."""
    a = {x.name: x for x in man_mod.load_anchors()}["enc-latin1"]
    src = norm_mod.read_report(a.golden_report)
    if "(Line 1)" not in src:
        pytest.skip("enc-latin1 golden shape changed")
    bad = tmp_path / "bad.xml"
    _write_bytes(bad, src.replace("(Line 1)", "(Line 2)"))
    mut = copy.copy(a)
    mut.golden_report = bad
    monkeypatch.setattr(man_mod, "load_anchors", lambda *x, **k: [mut])

    out = _runner(tmp_path / "res").run_anchors("current")
    assert out[0].verdict is Verdict.FAIL, (
        "normalization erased the encoding-error line number: " + out[0].detail)


# --------------------------------------------------------------------------
# controls: the negative tests above must not be passing vacuously
# --------------------------------------------------------------------------
def test_unmutated_golden_still_passes(tmp_path, monkeypatch):
    """Control for all of the above: without mutation, it must pass.

    Guards against the mutation tests passing because the comparison was broken
    rather than strict.
    """
    a = {x.name: x for x in man_mod.load_anchors()}["al-insert"]
    monkeypatch.setattr(man_mod, "load_anchors", lambda *x, **k: [a])
    out = _runner(tmp_path / "res").run_anchors("current")
    assert out[0].verdict is Verdict.PASS, out[0].detail


def test_label_only_mutation_is_normalized_away(tmp_path, monkeypatch):
    """A mutation of ONLY a confirmed label must NOT cause a failure.

    This is the positive counterpart: it proves the label table really is
    applied, so the negative tests above are not passing merely because nothing
    is normalized at all.
    """
    a = {x.name: x for x in man_mod.load_anchors()}["opt-display-matches"]
    src = norm_mod.read_report(a.golden_report)
    assert "<mode>Same</mode>" in src, "fixture shape changed"
    mutated = tmp_path / "label-only.xml"
    _write_bytes(mutated, src.replace("<mode>Same</mode>", "<mode>相同</mode>"))
    mut = copy.copy(a)
    mut.golden_report = mutated
    monkeypatch.setattr(man_mod, "load_anchors", lambda *x, **k: [mut])

    out = _runner(tmp_path / "res").run_anchors("current")
    assert out[0].verdict is Verdict.PASS, (
        "a confirmed label pair was not normalized: " + out[0].detail)
    assert "xml:label-pair:mode" in out[0].rules_applied
