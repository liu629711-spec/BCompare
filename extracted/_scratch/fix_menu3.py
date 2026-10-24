import re
p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()
old = '''                    int at = headerText.IndexOf(key, StringComparison.OrdinalIgnoreCase);
                    headerText = at >= 0
                        ? headerText.Insert(at + 1, "&")
                        : "&" + key + " " + headerText;'''
new = '''                    int at = headerText.IndexOf(key, StringComparison.OrdinalIgnoreCase);
                    headerText = at >= 0
                        ? headerText.Insert(at, "&")
                        : "&" + key + " " + headerText;'''
assert old in s, 'anchor missing'
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('insert position fixed (& goes BEFORE the letter)')
