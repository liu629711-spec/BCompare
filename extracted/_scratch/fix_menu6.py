import re
p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()
old = '''                string headerText = topName;
                if (spec.TopAccess != null && spec.TopAccess.TryGetValue(spec.View, out var accMap)
                    && accMap.TryGetValue(topName, out var key) && !string.IsNullOrEmpty(key))
                {
                    int at = headerText.IndexOf(key, StringComparison.OrdinalIgnoreCase);
                    headerText = at >= 0
                        ? headerText.Insert(at, "_")
                        : "_" + key + " " + headerText;
                }
                var mi = new MenuItem { Header = headerText };'''
new = '''                // WPF parses access keys from Header TEXT ('_' marker). Only inject
                // when the key letter is ALREADY in the title (Session->'n' etc.);
                // when it is not (File->'o' from 'Open File...'), BC's live Name is
                // the plain title with AccessKey set — injecting text would corrupt
                // the Name, so we set the property instead.
                string headerText = topName;
                bool keyInTitle = false;
                if (spec.TopAccess != null && spec.TopAccess.TryGetValue(spec.View, out var accMap)
                    && accMap.TryGetValue(topName, out var key) && !string.IsNullOrEmpty(key))
                {
                    int at = headerText.IndexOf(key, StringComparison.OrdinalIgnoreCase);
                    if (at >= 0)
                    {
                        headerText = headerText.Insert(at, "_");
                        keyInTitle = true;
                    }
                }
                var mi = new MenuItem { Header = headerText };
                if (!keyInTitle && spec.TopAccess != null
                    && spec.TopAccess.TryGetValue(spec.View, out var am2)
                    && am2.TryGetValue(topName, out var k2) && !string.IsNullOrEmpty(k2))
                {
                    System.Windows.Automation.AutomationProperties.SetAccessKey(mi, "Alt+" + k2);
                }'''
assert old in s, 'anchor missing'
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('conditional access-key injection')
