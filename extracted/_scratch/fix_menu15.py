p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()
old = 'System.Windows.Automation.AutomationProperties.SetAccessKey(mi, "Alt+" + key);'
new = '''// BC's live UIA AccessKey is the bare letter ('n'); WPF composes the Alt+
// modifier itself when the user presses it, so store just the letter.
                    System.Windows.Automation.AutomationProperties.SetAccessKey(mi, key);'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('bare access key')
