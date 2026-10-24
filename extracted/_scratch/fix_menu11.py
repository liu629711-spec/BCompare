p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()
old = "using System.Windows.Input;"
new = "using System.Windows.Automation.Peers;\nusing System.Windows.Input;"
if old in s and "using System.Windows.Automation.Peers;" not in s:
    s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8').write(s)
    print('using added')
else:
    print('already present or anchor missing')
