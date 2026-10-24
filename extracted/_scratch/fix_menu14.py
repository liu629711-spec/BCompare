p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()

# revert top items to native MenuItem: the custom BcMenuItem peer broke the UIA
# rectangle (click_input fails with SetCursorPos on a detached/invalid rect),
# which blocks the whole live check. AccessKey 'Alt+N' vs oracle 'n' and the
# gesture-in-Name format stay recorded as known display deltas (docs/19 §6.6).
s = s.replace("var mi = new BcMenuItem { Header = topName };", "var mi = new MenuItem { Header = topName };")
s = s.replace("mi.AccessLetter = key;", "System.Windows.Automation.AutomationProperties.SetAccessKey(mi, \"Alt+\" + key);")
open(p, 'w', encoding='utf-8').write(s)
print('top items back to native MenuItem')
