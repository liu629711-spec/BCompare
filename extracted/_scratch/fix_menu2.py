import re

# --- MenuHost.cs: inject top access keys into Headers ---
p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()

# 1) MenuSpec gets TopAccess
old = '        public Dictionary<string, List<string>> ItemOrder = new();  // "view|menu" -> labels in live order'
new = old + '''
        /// <summary>Per-view top-menu access keys ("view" -> {menu: letter}).
        /// Measured rule: BC assigns each top menu the access key of its FIRST
        /// submenu item (Session->n from 'New Session', Search->t/c/n by view).</summary>
        public Dictionary<string, Dictionary<string, string>> TopAccess = new();'''
assert old in s, 'MenuSpec anchor missing'
s = s.replace(old, new)

# 2) top Header gets the access key injected
old2 = '''                var mi = new MenuItem { Header = ResolveAccess(topName) };'''
new2 = '''                string headerText = topName;
                if (spec.TopAccess != null && spec.TopAccess.TryGetValue(spec.View, out var accMap)
                    && accMap.TryGetValue(topName, out var key) && !string.IsNullOrEmpty(key))
                {
                    // inject the access key at the first occurrence of the letter
                    int at = headerText.IndexOf(key, StringComparison.OrdinalIgnoreCase);
                    headerText = at >= 0
                        ? headerText.Insert(at + 1, "&")
                        : "&" + key + " " + headerText;
                }
                var mi = new MenuItem { Header = headerText };'''
assert old2 in s, 'top Header anchor missing'
s = s.replace(old2, new2)
open(p, 'w', encoding='utf-8').write(s)
print('MenuHost patched')

# --- MenuMode.cs: load top_access ---
p2 = r'D:\Rea\product\gui\WpfHost\MenuMode.cs'
s2 = open(p2, encoding='utf-8').read()
old3 = '''            if (r.TryGetProperty("item_order", out var io))'''
new3 = '''            if (r.TryGetProperty("top_access", out var ta))
                foreach (var viewKv in ta.EnumerateObject())
                {
                    var d = new Dictionary<string, string>();
                    foreach (var mk in viewKv.Value.EnumerateObject()) d[mk.Name] = mk.Value.GetString() ?? "";
                    spec.TopAccess[viewKv.Name] = d;
                }
            if (r.TryGetProperty("item_order", out var io))'''
assert old3 in s2, 'MenuMode anchor missing'
s2 = s2.replace(old3, new3)
open(p2, 'w', encoding='utf-8').write(s2)
print('MenuMode patched')
