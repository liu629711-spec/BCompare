import re
p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()

# 1) MenuItemPeer: BC's UIA Name is "Label\tGesture"; WPF's default peer reports
#    only the header (and its '_'/'&' markers). Override GetNameCore to match the
#    oracle format exactly, and expose the access key from the marker letter.
old_marker = """                // WPF parses access keys from Header TEXT ('_' marker). Only inject
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
                }"""
new_marker = """                // Top access keys are runtime-assigned (first submenu item's key)
                // and may be absent from the title (File->'o'). WPF cannot express
                // that in header text without corrupting the Name, so we keep the
                // header clean and hand the key to the custom peer below.
                var mi = new MenuItem { Header = topName };
                if (spec.TopAccess != null && spec.TopAccess.TryGetValue(spec.View, out var accMap)
                    && accMap.TryGetValue(topName, out var key) && !string.IsNullOrEmpty(key))
                {
                    MenuPeers.SetAccessKey(mi, key);
                }"""
assert old_marker in s, 'marker block missing'
s = s.replace(old_marker, new_marker)

# 2) children: register the same custom peer (Header keeps the VCL '&' marker,
#    the peer strips it for Name and derives AccessKey from it)
old_child = """                    if (!string.IsNullOrEmpty(act.Key))
                        System.Windows.Automation.AutomationProperties.SetAutomationId(child, act.Key);"""
new_child = """                    MenuPeers.Attach(child);
                    if (!string.IsNullOrEmpty(act.Key))
                        System.Windows.Automation.AutomationProperties.SetAutomationId(child, act.Key);"""
assert old_child in s, 'child anchor missing'
s = s.replace(old_child, new_child)

# 3) append MenuPeers helper class
s = s.rstrip()
if 'class MenuPeers' not in s:
    s = s[: s.rindex('}')] + """
    /// <summary>
    /// BC's UIA contract for menu items (measured in the live baseline):
    ///   Name       = "<label with access marker removed>\\t<gesture>"
    ///   AccessKey  = single letter ('' when none)
    /// WPF's stock MenuItem peer reports only the header text, so we override.
    /// </summary>
    internal static class MenuPeers
    {
        private static readonly DependencyProperty AccessLetterProperty =
            DependencyProperty.RegisterAttached("AccessLetter", typeof(string), typeof(MenuPeers),
                new PropertyMetadata(null));

        public static void SetAccessKey(MenuItem mi, string letter) =>
            mi.SetValue(AccessLetterProperty, letter);

        public static void Attach(MenuItem mi) { /* peer reads the attached letter lazily */ }

        public static string NameOf(MenuItem mi)
        {
            var header = mi.Header as string ?? "";
            // strip the WPF/VCL access marker for the display name
            var plain = header.Replace("_", "").Replace("&&", "\\u0000").Replace("&", "").Replace("\\u0000", "&");
            var gesture = mi.InputGestureText;
            return string.IsNullOrEmpty(gesture) ? plain : plain + "\\t" + gesture;
        }

        public static string AccessKeyOf(MenuItem mi)
        {
            var letter = mi.GetValue(AccessLetterProperty) as string;
            if (!string.IsNullOrEmpty(letter)) return letter;
            var header = mi.Header as string ?? "";
            // '_x' or '&x' marks the access key in the header text
            foreach (var marker in new[] { "_", "&" })
            {
                int i = header.IndexOf(marker, StringComparison.Ordinal);
                if (i >= 0 && i + 1 < header.Length) return header.Substring(i + 1, 1);
            }
            return "";
        }
    }
}
"""
open(p, 'w', encoding='utf-8').write(s)
print('MenuPeers helper added; call sites rewired')
