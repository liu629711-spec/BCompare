import re
p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()

old = '''                string headerText = topName;
                if (spec.TopAccess != null && spec.TopAccess.TryGetValue(spec.View, out var accMap)
                    && accMap.TryGetValue(topName, out var key) && !string.IsNullOrEmpty(key))
                {
                    // inject the access key at the first occurrence of the letter
                    int at = headerText.IndexOf(key, StringComparison.OrdinalIgnoreCase);
                    headerText = at >= 0
                        ? headerText.Insert(at, "&")
                        : "&" + key + " " + headerText;
                }
                var mi = new MenuItem { Header = headerText };'''
new = '''                // Top access keys are RUNTIME-assigned (first submenu item's key),
                // often a letter absent from the menu title (File->'o' from
                // 'Open File...'). BC's live UIA Name shows just 'File' with
                // AccessKey='o' — i.e. the key is a property, not header text.
                var mi = new MenuItem { Header = topName };
                if (spec.TopAccess != null && spec.TopAccess.TryGetValue(spec.View, out var accMap)
                    && accMap.TryGetValue(topName, out var key) && !string.IsNullOrEmpty(key))
                {
                    System.Windows.Automation.AutomationProperties.SetAccessKey(mi, "Alt+" + key);
                }'''
assert old in s, 'anchor missing'
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('top access key set as property (not header text)')
