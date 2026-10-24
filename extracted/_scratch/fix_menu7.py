p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()

old = """                    var child = new MenuItem
                    {
                        Header = ResolveAccess(label),                       // label without '&'
                        InputGestureText = string.IsNullOrEmpty(act.Shortcut) ? null : NormalizeShortcut(act.Shortcut),
                        ToolTip = TooltipOf(act),
                    };"""
new = """                    var sc = NormalizeShortcut(act.Shortcut);
                    var child = new MenuItem
                    {
                        Header = ResolveAccess(label),                       // label without '&'
                        InputGestureText = string.IsNullOrEmpty(sc) ? null : sc,
                        ToolTip = TooltipOf(act),
                    };
                    // A real KeyBinding (not just InputGestureText) is what makes
                    // WPF merge the gesture into the UIA Name as "Label\\tCtrl+T" —
                    // the exact format the Oracle live baseline shows.
                    if (TryKeyGesture(sc, out var gesture, out var gkey))
                        child.InputBindings.Add(new KeyBinding(new RelayCommand(), gesture, gkey));"""
assert old in s, 'child anchor missing'
s = s.replace(old, new)

old2 = """        private static string TooltipOf(MenuAction a)"""
new2 = """        public static bool TryKeyGesture(string sc, out ModifierKeys mods, out Key key)
        {
            mods = default; key = default;
            if (string.IsNullOrEmpty(sc)) return false;
            foreach (var p in sc.Split('+'))
            {
                switch (p)
                {
                    case "Ctrl": mods |= ModifierKeys.Control; break;
                    case "Shift": mods |= ModifierKeys.Shift; break;
                    case "Alt": mods |= ModifierKeys.Alt; break;
                    case "Meta": mods |= ModifierKeys.Windows; break;
                    default:
                        if (!Enum.TryParse(p, true, out key)) return false;
                        break;
                }
            }
            return key != default;
        }

        private static string TooltipOf(MenuAction a)"""
assert old2 in s, 'helper anchor missing'
s = s.replace(old2, new2)

if 'class RelayCommand' not in s:
    s = s.rstrip()
    s = s[: s.rindex('}')] + """
    internal sealed class RelayCommand : System.Windows.Input.ICommand
    {
        public event EventHandler CanExecuteChanged;
        public bool CanExecute(object _) => true;
        public void Execute(object _) { }
    }
}
"""
open(p, 'w', encoding='utf-8').write(s)
print('KeyBinding wired')
