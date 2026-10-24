import re
p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()
old = '''                var mi = new MenuItem { Header = topName };
                if (spec.TopAccess != null && spec.TopAccess.TryGetValue(spec.View, out var accMap)
                    && accMap.TryGetValue(topName, out var key) && !string.IsNullOrEmpty(key))
                {
                    System.Windows.Automation.AutomationProperties.SetAccessKey(mi, "Alt+" + key);
                }'''
new = '''                // WPF parses access keys from Header TEXT ('_' marker; the letter
                // renders underlined). Top keys are runtime-assigned (first submenu
                // item's key) and may be absent from the title (File->'o') — WPF
                // cannot express that in text, so we inject the marker on the first
                // occurrence of the letter, else prefix with an underscore+letter.
                string headerText = topName;
                if (spec.TopAccess != null && spec.TopAccess.TryGetValue(spec.View, out var accMap)
                    && accMap.TryGetValue(topName, out var key) && !string.IsNullOrEmpty(key))
                {
                    int at = headerText.IndexOf(key, StringComparison.OrdinalIgnoreCase);
                    headerText = at >= 0
                        ? headerText.Insert(at, "_")
                        : "_" + key + " " + headerText;
                }
                var mi = new MenuItem { Header = headerText };'''
assert old in s, 'anchor missing'
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('top access key via _ marker')
