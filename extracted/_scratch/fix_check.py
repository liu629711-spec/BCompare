p = r'D:\Rea\tools\uia-menu-check.py'
s = open(p, encoding='utf-8').read()
old = '''        verified = 0
        for m in o_tops:
            if m not in live:
                continue
            top_el, live_label, live_acc = live[m]
            oracle_acc = oracle[m][0][2] if oracle[m] else ""
            live_norm = live_acc[4:] if live_acc.lower().startswith("alt+") else live_acc
            if live_norm.lower() != oracle_acc.lower():
                problems.append(f"[{m}] top AccessKey: oracle={oracle_acc!r} live={live_acc!r}")
            try:
                top_el.click_input()
                time.sleep(0.8)
                got = [(x[0], x[1]) for x in children_rows(top_el)]'''
new = '''        verified = 0

        def current_tops():
            """Re-read the app menu bar AFTER each open/close: WPF popups
            invalidate the UIA references captured before the click."""
            rows = live_menu_rows(win)
            return rows or {}

        for m in o_tops:
            if m not in live:
                continue
            oracle_acc = oracle[m][0][2] if oracle[m] else ""
            live_acc = live[m][2]
            live_norm = live_acc[4:] if live_acc.lower().startswith("alt+") else live_acc
            if live_norm.lower() != oracle_acc.lower():
                problems.append(f"[{m}] top AccessKey: oracle={oracle_acc!r} live={live_acc!r}")
            try:
                tops_now = current_tops()
                if m not in tops_now:
                    problems.append(f"[{m}] top item vanished after re-read")
                    continue
                top_el = tops_now[m][0]
                top_el.click_input()
                time.sleep(0.8)
                tops_open = current_tops()
                if m in tops_open:
                    got = [(x[0], x[1]) for x in children_rows(tops_open[m][0])]
                else:
                    got = [(x[0], x[1]) for x in children_rows(top_el)]'''
assert old in s, 'anchor missing'
s = s.replace(old, new)
old2 = '''                top_el.click_input()
                time.sleep(0.4)
            except Exception as e:
                problems.append(f"[{m}] expand failed: {type(e).__name__}: {str(e)[:100]}")'''
new2 = '''                tops_now = current_tops()
                if m in tops_now:
                    tops_now[m][0].click_input()
                time.sleep(0.4)
            except Exception as e:
                problems.append(f"[{m}] expand failed: {type(e).__name__}: {str(e)[:100]}")'''
assert old2 in s
s = s.replace(old2, new2)
open(p, 'w', encoding='utf-8').write(s)
print('checker re-reads menu bar around each click')
