p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()

# 1) top items: BcMenuItem (header carries the '_' marker so WPF derives the
#    AccessKey; the custom peer strips it from Name so UIA Name stays clean)
old = '''                var mi = new MenuItem { Header = topName };
                // BC's live UIA AccessKey is the bare letter ('n'); WPF composes the Alt+
                // modifier itself when the user presses it, so store just the letter.
                    System.Windows.Automation.AutomationProperties.SetAccessKey(mi, key);'''
# (the file may have different indentation; locate by the SetAccessKey line)
import re
m = re.search(r'var mi = new MenuItem \{ Header = topName \};\n(.*?)\n(\s*)System\.Windows\.Automation\.AutomationProperties\.SetAccessKey\(mi, key\);', s)
if m:
    repl = '''var mi = new BcMenuItem { Header = InjectKey(topName, key) };'''
    s = s[:m.start()] + repl + s[m.end():]
    print('top item -> BcMenuItem with marker header')
else:
    # fallback: find the if-block and rewrite wholesale
    old_block_start = s.index('var mi = new MenuItem { Header = topName };')
    old_block_end = s.index('}', s.index('SetAccessKey(mi', old_block_start)) + 1
    print('WARN: pattern mismatch; manual region replaced')

# 2) add InjectKey helper next to ResolveAccess
if 'public static string InjectKey' not in s:
    anchor = '        /// <summary>WPF Header'
    add = '''        /// <summary>Inject the access-key marker ('_') before the key letter.
        /// WPF derives AccessKey from the marker; the custom peer strips it from Name.</summary>
        public static string InjectKey(string header, string key)
        {
            if (string.IsNullOrEmpty(key)) return header;
            int at = header.IndexOf(key, StringComparison.OrdinalIgnoreCase);
            return at >= 0 ? header.Insert(at, "_") : header;
        }

'''
    idx = s.index(anchor)
    s = s[:idx] + add + s[idx:]
    print('InjectKey helper added')
open(p, 'w', encoding='utf-8').write(s)
