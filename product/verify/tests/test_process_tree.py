"""Process-tree containment tests.

``BComp.com`` is a launcher stub: it spawns ``BCompare.exe`` (a GUI host) as its
**grandchild**. Killing only the direct child on timeout orphans that
grandchild. A lone orphan is worse than a leaked handle, because BCompare.exe is
single-instance: a leftover host can adopt later invocations and, on error,
raise a *modal* dialog that waits for a click forever. No Python-side timeout
can reclaim that.

``harness/oracle.py`` therefore runs the Oracle inside a Windows **Job Object**
with ``JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE``, which terminates the whole tree in
the kernel when the job handle closes.

These tests deliberately do **not** need a real crash or a real Oracle. They use
a stub launcher that spawns a long-lived stub grandchild with the same shape as
the real one, so the mechanism is tested directly and quickly.

Run:  python -m pytest product\\verify\\tests -q -p no:cacheprovider
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import time

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from harness import installs as inst_mod     # noqa: E402
from harness import oracle as orc            # noqa: E402
from harness.taxonomy import Verdict         # noqa: E402

INSTALLS = inst_mod.discover()
CURRENT = INSTALLS.get("current")

pytestmark = pytest.mark.skipif(
    not orc._IS_WINDOWS,
    reason="job-object containment is a Windows mechanism",
)

#: Stub launcher: spawns a grandchild that writes its pid and sleeps, then the
#: launcher itself sleeps. Same process shape as BComp.com -> BCompare.exe.
_STUB_GRANDCHILD = (
    "import os, sys, time\n"
    "open(sys.argv[1], 'w').write(str(os.getpid()))\n"
    "time.sleep(300)\n"
)
_STUB_LAUNCHER = (
    "import subprocess, sys, time\n"
    "subprocess.Popen([sys.executable, sys.argv[1], sys.argv[2]])\n"
    "time.sleep(300)\n"
)


def _write(path: pathlib.Path, text: str) -> pathlib.Path:
    path.write_text(text, encoding="utf-8", newline="")
    return path


def _pid_alive(pid: int) -> bool:
    r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                       capture_output=True, text=True, timeout=60)
    return str(pid) in r.stdout


def _wait_dead(pid: int, timeout_s: float = 10.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if not _pid_alive(pid):
            return True
        time.sleep(0.25)
    return False


def _spawn_stub_tree(tmp_path: pathlib.Path, tree: orc.ProcessTree):
    """Start the stub launcher inside ``tree``; return (launcher_popen, pidfile)."""
    gc = _write(tmp_path / "stub_grandchild.py", _STUB_GRANDCHILD)
    ln = _write(tmp_path / "stub_launcher.py", _STUB_LAUNCHER)
    pidfile = tmp_path / "grandchild.pid"
    if pidfile.exists():
        pidfile.unlink()
    proc = subprocess.Popen(
        [sys.executable, str(ln), str(gc), str(pidfile)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=orc._CREATE_SUSPENDED if tree.enabled else 0,
    )
    tree.assign(proc)
    if tree.enabled:
        orc._resume(proc)
    return proc, pidfile


def _read_grandchild_pid(pidfile: pathlib.Path, timeout_s: float = 15.0) -> int | None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if pidfile.exists():
            try:
                return int(pidfile.read_text().strip())
            except (ValueError, OSError):
                pass
        time.sleep(0.2)
    return None


# --------------------------------------------------------------------------
# 1. containment is actually available
# --------------------------------------------------------------------------
def test_job_object_containment_is_available():
    with orc.ProcessTree() as tree:
        assert tree.enabled, f"job object unavailable: {tree.last_error}"
        assert tree.containment == "job-object"


def test_containment_is_disabled_cleanly_when_unavailable():
    """A disabled tree must report why rather than pretend it is protecting."""
    tree = orc.ProcessTree(enabled=False)
    with tree:
        assert tree.enabled is False
        assert tree.containment  # non-empty explanation
    assert tree.handle is None


# --------------------------------------------------------------------------
# 2. THE CORE PROPERTY: closing the job kills the grandchild
# --------------------------------------------------------------------------
def test_closing_job_reaps_the_grandchild(tmp_path):
    """The exact defect: kill the direct child only, and the grandchild lives.

    This test asserts the fix: with the job object, closing the job handle (i.e.
    leaving the ``with`` block, which happens on success, error AND timeout)
    terminates the grandchild too.
    """
    with orc.ProcessTree() as tree:
        assert tree.enabled
        proc, pidfile = _spawn_stub_tree(tmp_path, tree)
        gpid = _read_grandchild_pid(pidfile)
        assert gpid is not None, "stub grandchild never started"
        assert proc.poll() is None, "stub launcher exited early"
        assert _pid_alive(gpid), "grandchild should be alive inside the job"

    # Left the with-block => job handle closed => whole tree must be gone.
    assert _wait_dead(gpid, 10.0), (
        f"grandchild {gpid} survived job close -- process-tree leak is back")
    if proc.poll() is None:
        proc.kill()


def test_explicit_kill_tree_reaps_both_levels(tmp_path):
    with orc.ProcessTree() as tree:
        proc, pidfile = _spawn_stub_tree(tmp_path, tree)
        gpid = _read_grandchild_pid(pidfile)
        assert gpid is not None and _pid_alive(gpid)
        assert tree.kill_tree() is True
        assert _wait_dead(gpid, 10.0)
        assert proc.poll() is not None


def test_direct_child_kill_alone_would_orphan_the_grandchild(tmp_path):
    """Control: documents WHY the job object is needed.

    Started WITHOUT containment, killing only the launcher leaves the
    grandchild running. This is the pre-fix behaviour, reproduced on purpose so
    the regression cannot silently return.
    """
    tree = orc.ProcessTree(enabled=False)
    with tree:
        proc, pidfile = _spawn_stub_tree(tmp_path, tree)
        gpid = _read_grandchild_pid(pidfile)
        assert gpid is not None, "stub grandchild never started"
        proc.kill()
        proc.wait(timeout=20)
        # The grandchild is NOT owned by anything -> it survives.
        time.sleep(1.0)
        orphaned = _pid_alive(gpid)
    # Clean up the orphan this control deliberately created.
    subprocess.run(["taskkill", "/PID", str(gpid), "/T", "/F"],
                   capture_output=True, timeout=60)
    assert orphaned, (
        "expected the grandchild to be orphaned without containment; if this "
        "fails the control is no longer demonstrating the defect")


# --------------------------------------------------------------------------
# 3. the real Oracle path is contained, on success and on timeout
# --------------------------------------------------------------------------
def _require_current():
    if CURRENT is None or not CURRENT.enabled:
        pytest.skip("current Oracle unavailable")
    return CURRENT


def _oracle_procs() -> list[str]:
    r = subprocess.run(["tasklist", "/FO", "CSV", "/NH"],
                       capture_output=True, text=True, timeout=90)
    return [ln for ln in r.stdout.splitlines()
            if "BCompare.exe" in ln or "BComp.com" in ln]


def test_real_oracle_call_is_contained_and_leaves_nothing(tmp_path):
    inst = _require_current()
    from harness import manifests as man_mod
    a = {x.name: x for x in man_mod.load_anchors()}["al-insert"]
    sp = orc.write_script(tmp_path / "s.txt", [orc.text_script("xml")])
    before = _oracle_procs()
    run = orc.run(inst.oracle_path, sp, str(a.left), str(a.right),
                  tmp_path / "o.xml", timeout=120)
    assert run.exit_code == 0
    assert run.containment == "job-object"
    time.sleep(0.5)
    after = _oracle_procs()
    assert len(after) <= len(before), (
        f"a real Oracle call left processes behind: before={before} after={after}")


def test_real_oracle_timeout_reaps_the_tree(tmp_path):
    """Big comparison + tiny timeout forces a real mid-flight tree kill."""
    inst = _require_current()

    def snap():
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
            "Get-Process | Where-Object { $_.ProcessName -match 'BCompare|BComp' } | "
            "ForEach-Object { $_.Id }"],
            capture_output=True, text=True, timeout=90)
        return [x for x in r.stdout.split() if x.strip()]

    # Build a pair big enough that the comparison cannot finish in the timeout.
    body = [f"line {i} {'x' * 60}" for i in range(60000)]
    left = tmp_path / "big-L.txt"
    right = tmp_path / "big-R.txt"
    left.write_text("\n".join(body), encoding="utf-8")
    mod = list(body)
    for i in range(0, len(mod), 500):
        mod[i] = f"CHANGED {i} {'y' * 60}"
    right.write_text("\n".join(mod), encoding="utf-8")

    sp = orc.write_script(tmp_path / "s.txt",
                          [orc.text_script("side-by-side")])
    outs = tmp_path / "big-out.txt"

    stream = orc.run(inst.oracle_path, sp, str(left), str(right), outs,
                     timeout=0.6)
    assert stream.timed_out, "expected the tiny timeout to fire"
    assert stream.tree_killed, "a timeout must issue a tree kill"
    time.sleep(1.5)
    assert snap() == [], f"orphaned Oracle processes after timeout: {snap()}"


def test_next_call_succeeds_after_a_timeout(tmp_path):
    """A leftover orphan would break the following call; this pins that it does not."""
    inst = _require_current()
    from harness import manifests as man_mod
    a = {x.name: x for x in man_mod.load_anchors()}["opt-display-matches"]

    body = [f"line {i} {'x' * 60}" for i in range(60000)]
    left, right = tmp_path / "b-L.txt", tmp_path / "b-R.txt"
    left.write_text("\n".join(body), encoding="utf-8")
    right.write_text("\n".join(body), encoding="utf-8")
    sp_big = orc.write_script(tmp_path / "sbig.txt",
                              [orc.text_script("side-by-side")])
    r1 = orc.run(inst.oracle_path, sp_big, str(left), str(right),
                 tmp_path / "big.txt", timeout=0.6)
    assert r1.timed_out

    sp = orc.write_script(tmp_path / "s.txt", [orc.text_script("xml")])
    r2 = orc.run(inst.oracle_path, sp, str(a.left), str(a.right),
                 tmp_path / "after.xml", timeout=120)
    assert r2.exit_code == 0, (
        "a call following a timeout failed -- possible orphan interference")
    assert r2.report_bytes > 0


# --------------------------------------------------------------------------
# 4. exit-code semantics survive the rewrite
# --------------------------------------------------------------------------
def test_exit_codes_still_pass_through_after_containment_rewrite(tmp_path):
    inst = _require_current()
    sp = orc.write_script(tmp_path / "s.txt", [orc.text_script("xml")])
    r = orc.run(inst.oracle_path, sp, str(tmp_path / "no-L.txt"),
                str(tmp_path / "no-R.txt"), tmp_path / "o.xml", timeout=120)
    assert r.exit_code == 107

    sp2 = orc.write_script(tmp_path / "s2.txt", [orc.text_script("zzz")])
    from harness import manifests as man_mod
    a = {x.name: x for x in man_mod.load_anchors()}["al-insert"]
    r2 = orc.run(inst.oracle_path, sp2, str(a.left), str(a.right),
                 tmp_path / "o2.xml", timeout=120)
    assert r2.exit_code == 106
