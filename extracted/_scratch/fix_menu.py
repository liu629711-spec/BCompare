import re
p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()

# 1) ResolveAccess: VCL and WPF share the '&' marker — pass through unchanged.
old_body = 'return caption.Replace("&&", "\\u0000").Replace("&", "__").Replace("\\u0000", "&");'
new_body = 'return caption;  // VCL and WPF share the same \'&\' access-key marker'
if old_body in s:
    s = s.replace(old_body, new_body)
    print('ResolveAccess body fixed')
else:
    print('WARN: ResolveAccess body not found')

# 2) child Header keeps the access-key marker
old_child = "Header = label,"
new_child = "Header = ResolveAccess(label),"
if old_child in s:
    s = s.replace(old_child, new_child)
    print('child Header fixed')
else:
    print('WARN: child Header not found')

open(p, 'w', encoding='utf-8').write(s)
