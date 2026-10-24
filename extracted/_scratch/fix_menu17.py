p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()
start = s.index('                // Top access keys are runtime-assigned')
end = s.index('                foreach (var (act, label) in items)')
new_block = '''                // Top access keys are runtime-assigned (first submenu item's key)
                // and may be absent from the title (File->'o'). WPF derives the UIA
                // AccessKey from a '_' marker in the Header text; the custom peer
                // (BcMenuItemPeer.GetNameCore) strips it so the UIA Name stays the
                // clean title, exactly like the Oracle live baseline.
                var mi = new BcMenuItem { Header = topName };
                if (spec.TopAccess != null && spec.TopAccess.TryGetValue(spec.View, out var accMap)
                    && accMap.TryGetValue(topName, out var key) && !string.IsNullOrEmpty(key))
                {
                    mi.Header = InjectKey(topName, key);
                    mi.AccessLetter = key;   // used when the letter is not in the title
                }
'''
s = s[:start] + new_block + s[end:]
open(p, 'w', encoding='utf-8').write(s)
print('top item block rewritten cleanly')
