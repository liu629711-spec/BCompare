"""Oracle invocation.

Two recipes, both verified in this workspace against the current install:

**Text**
    BComp.com /silent @<script> <left> <right> <output>
    script: ``text-report layout:<layout> [options:<opts>] output-to:"%3" "%1" "%2"``

**Folder** (``folder-report`` reports the *currently loaded* base folders, so
``load`` must come first -- without it the exit code is 106 and the report is
0 bytes):
    script: ``load "%1" "%2"`` / ``expand all`` /
            ``folder-report layout:xml output-to:"%3"``

Hard rules enforced here:

* The Oracle is **always** invoked from its real install directory (its own
  ``cwd``), and never copied.  Copying ``BCompare.exe``/``BComp.com`` elsewhere
  triggers ``Trial mode error ... Error = 5`` and exit 104.
* Every script and every report the harness writes lands under the harness
  results directory.  Nothing is written next to the read-only fixtures.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import pathlib
import subprocess
import time
from dataclasses import dataclass

from .taxonomy import OracleError

#: Observed exit statuses.  0 is success; the rest are the documented failures.
EXIT_MEANINGS = {
    0: "success",
    104: "licensing / trial error (Oracle was relocated?)",
    105: "script error",
    106: "script command error (e.g. folder-report without load)",
    107: "file not found / argument error",
}

#: Errors that must abort probing of an install entirely rather than be
#: recorded per-test: a licensing failure means every later invocation would
#: produce the same bogus result.
FATAL_EXITS = {104}


# ==========================================================================
# Process-tree containment
# ==========================================================================
# ``BComp.com`` is a *launcher stub*: it spawns ``BCompare.exe`` as a GUI host,
# which is its grandchild. Measured in this workspace:
#
#     BComp.com pid=31788  ->  BCompare.exe pid=38160 (same cmdline + /BCompWnd=)
#
# Killing only the direct child on timeout leaves that grandchild orphaned and
# running. A lone orphan is not just a leaked handle: BCompare.exe is
# single-instance, so a leftover GUI host can take over later invocations and,
# when it hits an error, raise a MODAL dialog that waits for a click forever.
# No Python-side timeout can reclaim it.
#
# The fix is a Windows **Job Object** with ``JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE``.
# Children of a job member inherit job membership by default, so assigning the
# launcher is enough to also own the grandchild. Closing the job handle then
# terminates the whole tree in the kernel -- no per-call process enumeration, so
# this costs nothing across ~257 invocations (a PowerShell CIM sweep measured
# 0.49 s per call, which was not affordable).
#
# The process is created ``CREATE_SUSPENDED`` and resumed only after it has been
# assigned to the job, closing the race where the launcher could spawn its child
# before we had captured it.

_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_CREATE_SUSPENDED = 0x00000004

_IS_WINDOWS = hasattr(ctypes, "windll")


class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", ctypes.c_uint32),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_uint32),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_uint32),
        ("SchedulingClass", ctypes.c_uint32),
    ]


class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", _IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class ProcessTree:
    """Owns a process and every descendant it spawns.

    Used as a context manager. On exit the whole tree is terminated, whether the
    run succeeded, failed or timed out, so no GUI host can outlive its call.
    """

    def __init__(self, *, enabled: bool = True):
        self.handle = None
        self.enabled = enabled and _IS_WINDOWS
        self.containment = "none"
        self.last_error = ""

    def __enter__(self) -> "ProcessTree":
        if self.enabled:
            try:
                k32 = ctypes.windll.kernel32
                k32.CreateJobObjectW.restype = wintypes.HANDLE
                h = k32.CreateJobObjectW(None, None)
                if not h:
                    raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
                info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
                info.BasicLimitInformation.LimitFlags = \
                    _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
                ok = k32.SetInformationJobObject(
                    wintypes.HANDLE(h),
                    _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                    ctypes.byref(info),
                    ctypes.sizeof(info),
                )
                if not ok:
                    k32.CloseHandle(wintypes.HANDLE(h))
                    raise OSError(ctypes.get_last_error(),
                                  "SetInformationJobObject failed")
                self.handle = h
                self.containment = "job-object"
            except OSError as exc:
                self.enabled = False
                self.last_error = str(exc)
                self.containment = "none"
        if not self.enabled:
            self.containment = ("unsupported" if not _IS_WINDOWS
                                else f"unavailable: {self.last_error}")
        return self

    def assign(self, process: subprocess.Popen) -> None:
        """Put ``process`` (and therefore its descendants) inside the job."""
        if not self.enabled or self.handle is None:
            return
        try:
            k32 = ctypes.windll.kernel32
            if not k32.AssignProcessToJobObject(wintypes.HANDLE(self.handle),
                                                wintypes.HANDLE(int(process._handle))):
                raise OSError(ctypes.get_last_error(),
                              "AssignProcessToJobObject failed")
        except OSError as exc:
            self.last_error = str(exc)

    def kill_tree(self) -> bool:
        """Terminate every process in the job. Returns True if a kill was issued."""
        if not self.enabled or self.handle is None:
            return False
        try:
            return bool(ctypes.windll.kernel32.TerminateJobObject(
                wintypes.HANDLE(self.handle), 1))
        except OSError:
            return False

    def __exit__(self, *exc_info) -> None:
        # Closing the handle is itself the guarantee: KILL_ON_JOB_CLOSE takes
        # the whole tree down even if no explicit kill ran.
        if self.handle is not None:
            try:
                ctypes.windll.kernel32.CloseHandle(wintypes.HANDLE(self.handle))
            except OSError:
                pass
            self.handle = None


def _resume(process: subprocess.Popen) -> None:
    """Resume a CREATE_SUSPENDED process.

    ``NtResumeProcess`` is used rather than locating the main thread handle:
    ``subprocess`` does not expose the thread handle from ``CreateProcess``, and
    enumerating threads to find it would be more code and more assumptions for
    no benefit. The syscall is stable and is what ``ResumeThread``-by-handle
    achieves.
    """
    try:
        ntdll = ctypes.windll.ntdll
        ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
        ntdll.NtResumeProcess.restype = ctypes.c_long
        ntdll.NtResumeProcess(wintypes.HANDLE(int(process._handle)))
    except OSError:
        pass



@dataclass
class OracleRun:
    exit_code: int
    elapsed_s: float
    command: list[str]
    script_text: str
    script_path: str
    report_path: str
    stdout: str
    stderr: str
    timed_out: bool = False
    report_bytes: int = 0
    report_exists: bool = False
    #: How the child's descendant tree was contained (see :class:`ProcessTree`).
    containment: str = "none"
    #: True when a timeout forced a tree kill.
    tree_killed: bool = False


def write_script(path: pathlib.Path, lines: list[str]) -> pathlib.Path:
    """Write a BComp script.

    The Oracle reads ``@file`` as ANSI/UTF-8 with CRLF; LF-only scripts have
    been observed to work, but CRLF matches what the Oracle itself emits and
    costs nothing.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8"))
    return path


def text_script(layout: str, options: str | None = None) -> str:
    opt = f" options:{options}" if options else ""
    return f'text-report layout:{layout}{opt} output-to:"%3" "%1" "%2"'


def table_script(layout: str, title: str | None = None) -> str:
    """The table (CSV) channel (M6). No `options:` exists here -- any
    options payload is a measured exit 105 (docs/13 §4.7), so the golden
    script is always the default display-all form. `title:` replaces the
    frame title (measured X4)."""
    t = f' title:"{title}"' if title else ""
    return f'data-report layout:{layout}{t} output-to:"%3" "%1" "%2"'


def hex_script(layout: str, title: str | None = None) -> str:
    """The hex channel (M7, docs/14). `options:`/`output-options:` are both
    measured 106 (Y9/Y10), so the golden script is the plain form; `title:`
    replaces the frame title (V3/Y11)."""
    t = f' title:"{title}"' if title else ""
    return f'hex-report layout:{layout}{t} output-to:"%3" "%1" "%2"'


FOLDER_SCRIPT_LINES = (
    'load "%1" "%2"',
    "expand all",
    'folder-report layout:xml output-to:"%3"',
)


def run(
    oracle_path: str | pathlib.Path,
    script_path: str | pathlib.Path,
    left: str,
    right: str,
    output: str | pathlib.Path,
    *,
    timeout: float = 180.0,
    script_text: str = "",
) -> OracleRun:
    """Invoke the Oracle once.

    ``oracle_path`` must be the real ``BComp.com`` inside its install
    directory; the process is started with ``cwd`` set to that directory so no
    relocation happens.  The output file is deleted first so a stale report
    from an earlier run can never be mistaken for this run's result.
    """
    oracle = pathlib.Path(oracle_path)
    if not oracle.exists():
        raise OracleError(f"oracle not found: {oracle}", command=[str(oracle)])

    out = pathlib.Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()

    cmd = [str(oracle), "/silent", f"@{script_path}", str(left), str(right), str(out)]
    started = time.perf_counter()
    timed_out = False
    tree_killed = False
    containment = "none"
    stdout = stderr = ""
    code: int | None = None

    # Run inside a job object so the launcher's grandchild (BCompare.exe) cannot
    # outlive this call. See the ProcessTree comment block for the measurement.
    with ProcessTree() as tree:
        containment = tree.containment
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(oracle.parent),        # run IN PLACE -- never relocate
            creationflags=_CREATE_SUSPENDED if tree.enabled else 0,
        )
        tree.assign(proc)
        if tree.enabled:
            _resume(proc)
        try:
            raw_out, raw_err = proc.communicate(timeout=timeout)
            code = proc.returncode
            stdout = raw_out.decode("utf-8", errors="replace")
            stderr = raw_err.decode("utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            timed_out = True
            # Terminate the whole tree, then drain the pipes so the handles are
            # released rather than leaked to the GC.
            tree_killed = tree.kill_tree()
            proc.kill()
            try:
                raw_out, raw_err = proc.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                raw_out = raw_err = b""
            stdout = raw_out.decode("utf-8", errors="replace")
            stderr = raw_err.decode("utf-8", errors="replace")

    elapsed = time.perf_counter() - started

    exists = out.exists()
    size = out.stat().st_size if exists else 0

    run_result = OracleRun(
        exit_code=code if code is not None else -1,
        elapsed_s=round(elapsed, 3),
        command=cmd,
        script_text=script_text,
        script_path=str(script_path),
        report_path=str(out),
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
        report_bytes=size,
        report_exists=exists,
        containment=containment,
        tree_killed=tree_killed,
    )

    if not timed_out and run_result.exit_code in FATAL_EXITS:
        raise OracleError(
            f"Oracle returned fatal exit {run_result.exit_code} "
            f"({EXIT_MEANINGS.get(run_result.exit_code, '?')}); aborting this "
            f"install's probing",
            exit_code=run_result.exit_code,
            command=cmd,
            stderr=stderr,
        )
    return run_result


def exit_meaning(code: int) -> str:
    return EXIT_MEANINGS.get(code, f"undocumented exit {code}")
