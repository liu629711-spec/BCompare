p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()
# children back to native MenuItem: the subclass works for top bars but the
# submenu items live in a popup whose peer factory apparently drops the
# subclass's items; native MenuItem keeps the popup tree intact and the checker
# composes Label+gesture from header + InputGestureText.
old = "                    var child = new BcMenuItem"
new = "                    var child = new MenuItem"
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('children back to native MenuItem')
