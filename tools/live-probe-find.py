#!/usr/bin/env python
"""
Beyond Compare Find-in-File Dialog Probe
Strict single-launch measurement protocol
"""

import sys
import os
import json
import time
import ctypes
from pathlib import Path
import uiautomation as auto

# Windows constants
JOBOBJECTLIMIT_SETKILLONJOBEND = 2
JOB_OBJECT_LIMIT_KILL_ON_JOB_END = 0x2000

class JobObject:
    """Job Object wrapper for process containment"""
    def __init__(self):
        self.handle = None
    
    def create(self):
        self.handle = ctypes.windll.kernel32.CreateJobObjectW(None, None)
        if not self.handle:
            raise RuntimeError("Failed to create job object")
        return self
    
    def assign_process(self, hprocess):
        result = ctypes.windll.kernel32.AssignProcessToJobObject(self.handle, hprocess)
        if not result:
            raise RuntimeError("Failed to assign process to job object")
        return result
    
    def set_kill_on_end(self):
        try:
            # Use minimal structure - DWORD flags field
            class JobLimit(ctypes.Structure):
                _fields_ = [("Flags", ctypes.c_ulong)]
            
            info = JobLimit()
            info.Flags = JOB_OBJECT_LIMIT_KILL_ON_JOB_END
            
            result = ctypes.windll.kernel32.SetInformationJobObject(
                self.handle, JOBOBJECTLIMIT_SETKILLONJOBEND,
                ctypes.byref(info), ctypes.sizeof(info)
            )
            return bool(result)
        except Exception as e:
            print(f"Note: Could not set kill-on-end: {e}")
            return False
    
    def close(self):
        if self.handle:
            try:
                ctypes.windll.kernel32.CloseHandle(self.handle)
            finally:
                self.handle = None


def main():
    if len(sys.argv) < 5:
        print("Usage: python live-probe-find.py <bc_exe> <output_dir> <file1> <file2>")
        sys.exit(1)
    
    bc_exe = sys.argv[1]
    output_dir = Path(sys.argv[2])
    file1 = sys.argv[3]
    file2 = sys.argv[4]
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"=== Beyond Compare Find Dialog Probe ===")
    print(f"BC EXE: {bc_exe}")
    print(f"Output: {output_dir}")
    print(f"Files: {file1}, {file2}")
    
    # Pre-launch window scan
    print("\nPre-launch: Scanning current UIA state...")
    try:
        root = auto.GetRootControl()
        pre_windows = []
        def collect(ctrl, depth=0):
            if depth > 1:
                return
            try:
                if hasattr(ctrl, 'Name') and ctrl.Name:
                    pre_windows.append((ctrl.Name[:60], str(ctrl.ControlType)))
                for child in ctrl.GetChildren():
                    collect(child, depth + 1)
            except:
                pass
        
        collect(root)
        print(f"Found {len(pre_windows)} UIA objects before launch:")
        for name, ctype in pre_windows[:8]:
            print(f"  '{name}' ({ctype})")
        print("...")
    except Exception as e:
        print(f"Pre-scan error: {e}")
    
    print()
    
    # Step 1: Launch BCompare in Text Compare mode with Job Object
    print("[1] Launching BCompare...")
    job = JobObject()
    job.create()
    job.set_kill_on_end()
    
    cmd = f'"{bc_exe}" "{file1}" "{file2}"'
    print(f"Command: {cmd}")
    
    class STARTUPINFO(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong),
                    ("lpReserved", ctypes.c_wchar_p),
                    ("lpDesktop", ctypes.c_wchar_p),
                    ("lpTitle", ctypes.c_wchar_p),
                    ("dwX", ctypes.c_ulong),
                    ("dwY", ctypes.c_ulong),
                    ("dwXSize", ctypes.c_ulong),
                    ("dwYSize", ctypes.c_ulong),
                    ("dwXCountChars", ctypes.c_ulong),
                    ("dwYCountChars", ctypes.c_ulong),
                    ("dwFillAttribute", ctypes.c_ulong),
                    ("dwFlags", ctypes.c_ulong),
                    ("wShowWindow", ctypes.c_ushort),
                    ("cbReserved2", ctypes.c_ushort),
                    ("lpReserved2", ctypes.c_void_p),
                    ("hStdInput", ctypes.c_void_p),
                    ("hStdOutput", ctypes.c_void_p),
                    ("hStdError", ctypes.c_void_p)]
    
    startupinfo = STARTUPINFO()
    startupinfo.cb = ctypes.sizeof(startupinfo)
    
    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [("hProcess", ctypes.c_void_p),
                    ("hThread", ctypes.c_void_p),
                    ("dwProcessId", ctypes.c_ulong),
                    ("dwThreadId", ctypes.c_ulong)]
    
    process_info = PROCESS_INFORMATION()
    
    CREATE_SUSPENDED = 0x00000004
    dwCreationFlags = CREATE_SUSPENDED
    
    result = ctypes.windll.kernel32.CreateProcessW(
        None, cmd, None, None, False, dwCreationFlags, None, None,
        startupinfo, process_info
    )
    
    if not result:
        raise RuntimeError("Failed to launch BCompare")
    
    proc_handle = ctypes.c_void_p(process_info.hProcess)
    thread_handle = ctypes.c_void_p(process_info.hThread)
    
    # Try assign to job (may fail on some systems)
    try:
        job.assign_process(proc_handle)
        print("Process assigned to Job Object successfully")
    except Exception as e:
        print(f"Note: Could not assign to Job Object: {e}")
        print("Continuing without strict process containment...")
    
    # Resume process
    ctypes.windll.kernel32.ResumeThread(thread_handle)
    
    # Give BC time to initialize
    print("Waiting for BCompare main window...")
    time.sleep(5)  # Extended wait
    
    # Find all windows and list them
    print("Scanning available windows...")
    
    try:
        root = auto.GetRootControl()
        print(f"Root control type: {root.ControlType}")
        
        windows = []
        def collect_windows(ctrl, depth=0):
            if depth > 2:
                return
            windows.append((ctrl.Name, str(ctrl.ControlType)))
            try:
                for child in ctrl.GetChildren():
                    collect_windows(child, depth + 1)
            except:
                pass
        
        collect_windows(root)
        print(f"Found {len(windows)} window candidates:")
        for name, ctype in windows[:10]:
            print(f"  - {name} ({ctype})")
        print("...")
        
        # Look specifically for BC comparison window
        bc_window = None
        for attempt in range(15):
            try:
                # Try different approaches
                found = False
                
                # 1. Direct search by name patterns
                for pattern in ["文本比较", "Compare", "BCompare", "Comparison"]:
                    try:
                        w = auto.WindowControl(Name=pattern, searchDepth=2).WaitExist(1000)
                        if w:
                            bc_window = w
                            found = True
                            break
                    except:
                        pass
                
                if found:
                    break
                
                # 2. Get visible top-level windows
                children = root.GetChildren()
                for c in children:
                    try:
                        if hasattr(c, 'BoundingRectangle'):
                            rect = c.BoundingRectangle
                            if rect.Width > 400 and rect.Height > 300:  # Reasonable window size
                                if "Compare" in c.Name or "文本" in c.Name or "BCompare" in c.Name:
                                    bc_window = c
                                    print(f"Found BC window: {c.Name}")
                                    break
                    except:
                        continue
            
            except Exception as e:
                print(f"Scan attempt error: {e}")
            
            time.sleep(1)
        
        if not bc_window:
            # Last resort: take screenshot anyway
            raise RuntimeError("Could not locate any suitable window")
        
    except Exception as e:
        print(f"Window scan failed: {e}")
        raise
    
    print(f"Found main window: {bc_window.Name}")
    
    # Step 2: Launch Find-in-File dialog via Alt+F
    print("\n[2] Triggering Find-in-File (Alt+F)...")
    auto.SendKeys("{ALT+f}")
    time.sleep(1)
    
    # Look for Find dialog
    find_dialog = None
    patterns = ["Find", "Find in Files", "Search", "查找"]
    
    for pattern in patterns:
        try:
            find_dialog = auto.WindowControl(Name=pattern, searchDepth=3).WaitExist(3000, 0.1)
            if find_dialog:
                print(f"Found dialog matching '{pattern}': {find_dialog.Name}")
                break
        except:
            continue
        
        # Try alternative approach
        try:
            dialogs = auto.GetRootControl().GetChildren()
            for d in dialogs:
                children = d.GetChildren()
                for c in children:
                    if pattern in c.Name and c.ControlType == auto.WindowControl:
                        find_dialog = c
                        print(f"Found dialog: {c.Name}")
                        break
                if find_dialog:
                    break
        except:
            pass
        
        if find_dialog:
            break
    
    if not find_dialog:
        print("ERROR: Could not find Find dialog")
        print("Attempting screenshot of current state...")
        try:
            screenshot = ImageGrab.grab()
            screenshot.save(str(output_dir / "dialog.png"))
        except:
            pass
        raise RuntimeError("Find dialog not found")
    
    # Step 3: Take initial screenshot
    print("\n[3] Capturing initial screenshot...")
    try:
        screenshot = ImageGrab.grab()
        screenshot.save(str(output_dir / "dialog.png"))
    except Exception as e:
        print(f"Screenshot error: {e}")
    
    # Step 4: Full UIA tree walk
    print("\n[4] Walking UIA control tree...")
    
    def capture_tree(ctrl, depth=0, max_depth=6):
        if depth > max_depth or ctrl is None:
            return None
        
        node = {
            "control_type": str(ctrl.ControlType),
            "name": ctrl.Name or "",
            "automation_id": ctrl.AutomationId or "",
            "class_name": ctrl.ClassName or "",
            "rectangle": {
                "left": ctrl.BoundingRectangle.Left,
                "top": ctrl.BoundingRectangle.Top,
                "right": ctrl.BoundingRectangle.Right,
                "bottom": ctrl.BoundingRectangle.Bottom,
                "width": ctrl.BoundingRectangle.Width,
                "height": ctrl.BoundingRectangle.Height
            },
            "enabled": ctrl.Enabled,
            "visible": ctrl.Visible,
            "children": []
        }
        
        if depth < max_depth:
            try:
                for child in ctrl.GetChildren():
                    child_tree = capture_tree(child, depth + 1, max_depth)
                    if child_tree:
                        node["children"].append(child_tree)
            except:
                pass
        
        return node
    
    tree = capture_tree(find_dialog)
    
    tree_file = output_dir / "tree.json"
    with open(tree_file, 'w', encoding='utf-8') as f:
        json.dump(tree, f, indent=2, ensure_ascii=False)
    print(f"Tree saved to: {tree_file}")
    
    # Step 5: Extract key information
    print("\n[5] Extracting control states...")
    
    analysis = {
        "dialog_title": find_dialog.Name or "",
        "dialog_rectangle": {
            "left": find_dialog.BoundingRectangle.Left,
            "top": find_dialog.BoundingRectangle.Top,
            "width": find_dialog.BoundingRectangle.Width,
            "height": find_dialog.BoundingRectangle.Height
        },
        "controls": {}
    }
    
    controls_found = []
    
    def analyze_controls(ctrl, path="", depth=0):
        if depth > 4:
            return
        
        try:
            ctrl_type = str(ctrl.ControlType)
            name = ctrl.Name or f"type_{ctrl_type.replace('Control', '')}"
            
            ctrl_info = {
                "path": path,
                "control_type": ctrl_type,
                "name": name,
                "rectangle": {
                    "x": ctrl.BoundingRectangle.Left,
                    "y": ctrl.BoundingRectangle.Top,
                    "width": ctrl.BoundingRectangle.Width,
                    "height": ctrl.BoundingRectangle.Height
                },
                "state": {}
            }
            
            # Get specific states
            if ctrl_type == "EditControl":
                try:
                    val = ctrl.Value()
                    ctrl_info["value"] = val
                    ctrl_info["state"]["text"] = val
                except:
                    pass
            
            elif ctrl_type == "Button":
                ctrl_info["button_name"] = name
            
            elif ctrl_type == "CheckBox":
                try:
                    toggle = ctrl.ToggleControl()
                    if hasattr(toggle, 'ToggleState'):
                        ctrl_info["state"]["checked"] = bool(toggle.ToggleState)
                except:
                    pass
            
            elif ctrl_type == "RadioButton":
                try:
                    sel = ctrl.SelectionControl()
                    if hasattr(sel, 'Value'):
                        ctrl_info["state"]["selected"] = bool(sel.Value)
                except:
                    pass
            
            elif ctrl_type == "ComboBox":
                try:
                    text_ctrl = ctrl.TextControl()
                    ctrl_info["value"] = text_ctrl.Text
                except:
                    pass
            
            analysis["controls"][name] = ctrl_info
            controls_found.append(ctrl_info)
            
            # Recurse
            try:
                for child in ctrl.GetChildren():
                    new_path = f"{path}/{ctrl_type[:10]}" if path else f"{ctrl_type[:10]}"
                    analyze_controls(child, new_path, depth + 1)
            except:
                pass
        except:
            pass
    
    analyze_controls(find_dialog)
    
    # Step 6: Interactions test
    print("\n[6] Testing interactions...")
    
    # Find EditControl (the find text box)
    edits = []
    buttons = []
    
    def find_by_type(ctrl):
        nonlocal edits, buttons
        try:
            ctrl_type = str(ctrl.ControlType)
            if ctrl_type == "EditControl":
                edits.append(ctrl)
            elif ctrl_type == "Button":
                buttons.append(ctrl)
            
            for child in ctrl.GetChildren():
                find_by_type(child)
        except:
            pass
    
    find_by_type(find_dialog)
    print(f"Found {len(edits)} EditControls, {len(buttons)} Buttons")
    
    # Type into first edit control
    if edits:
        print("Typing 'TEST_FIND_TERM' into find field...")
        try:
            edits[0].SetFocus()
            auto.SendKeys("TEST_FIND_TERM")
            time.sleep(0.5)
            
            screenshot = ImageGrab.grab()
            screenshot.save(str(output_dir / "after-type.png"))
            print("Screenshot captured after typing")
        except Exception as e:
            print(f"Error during typing: {e}")
    
    # Click Find Next button
    find_next_btn = None
    for btn in buttons:
        if "Next" in btn.Name or "搜索" in btn.Name:  # Search in Chinese
            find_next_btn = btn
            break
    
    if find_next_btn:
        print(f"Clicking Find Next: {find_next_btn.Name}")
        try:
            find_next_btn.Click()
            time.sleep(0.5)
        except Exception as e:
            print(f"Click error: {e}")
    
    # Summary output
    print("\n=== SUMMARY ===")
    print(f"Dialog title: {analysis['dialog_title']}")
    print(f"Dialog size: {analysis['dialog_rectangle']['width']}x{analysis['dialog_rectangle']['height']} at ({analysis['dialog_rectangle']['left']}, {analysis['dialog_rectangle']['top']})")
    print(f"Total controls found: {len(controls_found)}")
    
    # Checkboxes
    checkboxes = [c for c in controls_found if c.get("control_type") == "CheckBox"]
    print(f"\nCHECKBOXES:")
    for cb in checkboxes:
        checked = cb.get("state", {}).get("checked", False)
        print(f"  {cb['name']}: {'✓ CHECKED' if checked else '✗ UNCHECKED'}")
    
    # Buttons
    button_list = [c for c in controls_found if c.get("control_type") == "Button"]
    print(f"\nBUTTONS:")
    for b in button_list:
        print(f"  - {b['name']}")
    
    # Edits
    edit_list = [c for c in controls_found if c.get("control_type") == "EditControl"]
    print(f"\nEDIT BOXES:")
    for e in edit_list:
        val = e.get("state", {}).get("text", "")
        print(f"  {e['name']}: value='{val}'")
    
    print(f"\nOutputs:")
    print(f"  - {output_dir}/dialog.png (initial)")
    print(f"  - {output_dir}/after-type.png (after typing)")
    print(f"  - {output_dir}/tree.json (UIA tree)")
    print(f"  - {output_dir}/summary.txt (this summary)")
    
    # Write summary file
    summary_file = output_dir / "summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=== BEYOND COMPARE FIND-DIALOG PROBE SUMMARY ===\n\n")
        f.write(f"Dialog Title: {analysis['dialog_title']}\n")
        f.write(f"Dialog Dimensions: {analysis['dialog_rectangle']['width']}x{analysis['dialog_rectangle']['height']} pixels\n")
        f.write(f"Position: X={analysis['dialog_rectangle']['left']}, Y={analysis['dialog_rectangle']['top']}\n\n")
        
        f.write("INITIAL CHECKBOX STATES:\n")
        for cb in checkboxes:
            checked = cb.get("state", {}).get("checked", False)
            f.write(f"  {cb['name']}: {'CHECKED' if checked else 'UNCHECKED'}\n")
        f.write("\n")
        
        f.write("BUTTONS:\n")
        for b in button_list:
            f.write(f"  - {b['name']}\n")
        f.write("\n")
        
        f.write("EDIT BOXES:\n")
        for e in edit_list:
            val = e.get("state", {}).get("text", "")
            f.write(f"  {e['name']}: value='{val}'\n")
        f.write("\n")
        
        f.write("KEY BINDINGS:\n")
        f.write("  Dialog triggered by: ALT+F\n")
        f.write("  Alternative: Tools → Find in Files menu\n")
    
    print(f"\nSummary written to: {summary_file}")
    
    # Cleanup check
    print("\n[7] Process termination check...")
    print("NOTE: Job Object should terminate BCompare when script exits")
    print("Manual verification: tasklist | findstr BCompare.exe")
    
    job.close()
    print("\nProbe complete!")


if __name__ == "__main__":
    from PIL import ImageGrab
    main()
