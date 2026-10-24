p = r'D:\Rea\tools\uia-menu-check.py'
s = open(p, encoding='utf-8').read()
old = '''                # bring the window truly to the foreground before interacting:
                # a background window yields invalid element rects and the click
                # dies in SetCursorPos (file-not-found) inside pywinauto.
                u32.ShowWindow(hwnd, 9)  # SW_RESTORE
                u32.SetForegroundWindow(hwnd)
                if u32.GetForegroundWindow() != hwnd:
                    # ALT nudge is the documented bypass for the foreground lock
                    u32.keybd_event(0x12, 0, 0, 0)
                    u32.keybd_event(0x12, 0, 2, 0)
                    u32.SetForegroundWindow(hwnd)
                time.sleep(0.6)'''
new = '''                force_foreground(hwnd)
                time.sleep(0.6)'''
assert old in s, 'anchor missing'
s = s.replace(old, new)

helper = '''

def force_foreground(hwnd):
    """Bring a window to the foreground reliably. A plain SetForegroundWindow
    fails while our process is background (the OS foreground lock); the standard
    bypass is AttachThreadInput to the current foreground thread, then Alt-nudge."""
    u32.ShowWindow(hwnd, 9)  # SW_RESTORE
    if u32.GetForegroundWindow() == hwnd:
        return
    fg = u32.GetForegroundWindow()
    our_tid = u32.GetWindowThreadProcessId(u32.GetShellWindow(), None)
    fg_tid = u32.GetWindowThreadProcessId(fg, None) if fg else 0
    me_tid = ctypes.windll.kernel32.GetCurrentThreadId()
    if fg_tid and fg_tid != me_tid:
        u32.AttachThreadInput(me_tid, fg_tid, True)
    try:
        u32.SetForegroundWindow(hwnd)
        u32.SetFocus(hwnd)
    finally:
        if fg_tid and fg_tid != me_tid:
            u32.AttachThreadInput(me_tid, fg_tid, False)
    if u32.GetForegroundWindow() != hwnd:
        u32.keybd_event(0x12, 0, 0, 0)
        u32.keybd_event(0x12, 0, 2, 0)
        u32.SetForegroundWindow(hwnd)

'''
if 'def force_foreground' not in s:
    s = s.replace('\ndef main():', helper + '\ndef main():', 1)
open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('force_foreground helper wired')
