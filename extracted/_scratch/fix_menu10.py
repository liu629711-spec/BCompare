p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()

# replace the Attach/SetAccessKey statics with a real MenuItem subclass whose
# AutomationPeer produces BC's exact Name/AccessKey contract.
old = s[s.index("    internal static class MenuPeers"):]
new = """    /// <summary>
    /// BC's UIA contract for menu items (measured in the live baseline):
    ///   Name       = "<label, access marker removed>\\t<gesture>"
    ///   AccessKey  = single letter ('' when none)
    /// WPF's stock MenuItem peer reports only the header text (and leaves the
    /// '_'/'&' markers in it), so we override both.
    /// </summary>
    internal sealed class BcMenuItem : MenuItem
    {
        public string AccessLetter;

        protected override AutomationPeer OnCreateAutomationPeer() => new BcMenuItemPeer(this);
    }

    internal sealed class BcMenuItemPeer : FrameworkElementAutomationPeer
    {
        public BcMenuItemPeer(BcMenuItem owner) : base(owner) { }

        protected override string GetNameCore()
        {
            var header = ((MenuItem)Owner).Header as string ?? "";
            var plain = header.Replace("_", "");
            // '&&' is a literal ampersand; single '&' marks the access key
            plain = plain.Replace("&&", "\\u0000").Replace("&", "").Replace("\\u0000", "&");
            var gesture = ((MenuItem)Owner).InputGestureText;
            return string.IsNullOrEmpty(gesture) ? plain : plain + "\\t" + gesture;
        }

        protected override string GetAccessKeyCore()
        {
            var item = (BcMenuItem)Owner;
            if (!string.IsNullOrEmpty(item.AccessLetter)) return item.AccessLetter;
            var header = item.Header as string ?? "";
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
s = s.replace(old, new)
# rewire call sites
s = s.replace("var mi = new MenuItem { Header = topName };", "var mi = new BcMenuItem { Header = topName };")
s = s.replace("MenuPeers.SetAccessKey(mi, key);", "mi.AccessLetter = key;")
s = s.replace("var child = new MenuItem", "var child = new BcMenuItem")
s = s.replace("MenuPeers.Attach(child);\n                    ", "")
open(p, 'w', encoding='utf-8').write(s)
print('BcMenuItem + peer wired')
