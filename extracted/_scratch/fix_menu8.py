p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()
old = "child.InputBindings.Add(new KeyBinding(new RelayCommand(), gesture, gkey));"
new = "child.InputBindings.Add(new KeyBinding(new RelayCommand(), gkey, gesture));"
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('KeyBinding ctor args fixed (Key, ModifierKeys)')
