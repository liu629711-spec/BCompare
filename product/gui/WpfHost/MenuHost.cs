// Data-driven menu system for the WPF host (docs/19 §6.6).
//
// The BC menu is a runtime projection of the ActionList by Category (docs/19
// §3.1/§3.4): every menu item = one TUiAction. The two authoritative inputs:
//   actions-*.json      caption(&accesskey)/shortcut/hint|tooltip/category
//   presence-matrix     which items exist in which view (TMenuPopulator output)
// This builder takes a view name + those two inputs and produces a WPF Menu
// whose items carry the same contract the Oracle live baseline shows:
//   UIA Name  = "<label with & resolved to AccessKey>\t<shortcut>"
//   InputGestureText = shortcut; AccessKey from '&'.
//
// UIA Name fidelity: WPF composes MenuItem.Name from Header + InputGestureText
// as "Header\tGesture" — which is exactly the Oracle format (measured).

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Automation.Peers;
using System.Windows.Input;

namespace ReaCompare.Gui
{
    internal sealed class MenuAction
    {
        public string Key = "";        // action object name (SessionNewListAction)
        public string Caption = "";    // '&New Session' (& = access key)
        public string Shortcut = "";   // 'Ctrl+T' ('' = none)
        public string Category = "";
        public string Form = "";       // originating ACTIONS form (per-view variant)
        public string Hint = "";       // 'Title|Tooltip'
    }

    // One entry of presence-matrix.json: item -> present_in [views]
    internal sealed class PresenceRow
    {
        public string Menu = "";
        public string Item = "";   // label WITHOUT '&', WITHOUT '\t...'
        public List<string> PresentIn = new();
    }

    internal sealed class MenuSpec
    {
        public string View = "";                  // "Text Compare" ...
        public List<string> TopMenus = new();     // order from live baseline
        public List<string> ViewForms = new();   // ACTIONS forms mounted in this view
        public Dictionary<string, List<string>> ItemOrder = new();  // "view|menu" -> labels in live order
        /// <summary>Per-view top-menu access keys ("view" -> {menu: letter}).
        /// Measured rule: BC assigns each top menu the access key of its FIRST
        /// submenu item (Session->n from 'New Session', Search->t/c/n by view).</summary>
        public Dictionary<string, Dictionary<string, string>> TopAccess = new();
        public List<MenuAction> Actions = new();
        public List<PresenceRow> Presence = new();
        public List<ChromeRow> Toolbars = new();    // live chrome rows (U-gui-4)
        public List<ChromeRow> Statusbars = new();
        public List<SkelNode> Skeleton = new();     // content-view tree (live home_tree)
        /// <summary>Live gray-state rows (TMenuUpdater input, enabled-matrix.json).
        /// 'always-enabled' => enabled wherever present; 'view-capability' =>
        /// statically disabled in the listed views; 'state-dependent' => disabled
        /// only in the captured (empty-session) views — matches the Oracle snapshot.</summary>
        public List<EnabledRow> Enabled = new();
    }

    internal sealed class EnabledRow
    {
        public string Menu = "";
        public string Label = "";   // presence-format label (no '\t' shortcut)
        public string Cls = "";     // always-enabled | state-dependent | view-capability
        public List<string> EnabledIn = new();
        public List<string> DisabledIn = new();
    }

    internal static class MenuBuilder
    {
        /// <summary>D1 brand policy (docs/20 2026-10-22): presentation strings
        /// that embed the Oracle product name are shown as ours. The capability
        /// is inherited unchanged — same item, same place, same shortcut, same
        /// gray state; only the display text differs. Matching against the
        /// reference matrices (presence/enabled/item_order) keeps using the
        /// ORIGINAL Oracle labels; ApplyBrand is only for what the user sees.</summary>
        public static string ApplyBrand(string s) =>
            s == null ? null : s.Replace("Beyond Compare", "LiuCompare");

        /// <summary>
        /// Build the WPF menu bar. Returns the Menu plus a per-view item ledger
        /// (label+shortcut+enabled in Oracle name format) for verification.
        /// </summary>
        public static (Menu, List<(string menu, string label, string shortcut, bool enabled)>) Build(MenuSpec spec)
        {
            var menu = new Menu();
            var ledger = new List<(string, string, string, bool)>();
            foreach (var topName in spec.TopMenus)
            {
                var items = ItemsForMenu(spec, topName);
                if (items.Count == 0) continue;  // menu absent in this view (TMenuPopulator)
                // Top access keys are RUNTIME-assigned (first submenu item's key),
                // often a letter absent from the menu title (File->'o' from
                // 'Open File...'). BC's live UIA Name shows just 'File' with
                // AccessKey='o' — i.e. the key is a property, not header text.
                // WPF parses access keys from Header TEXT ('_' marker; the letter
                // renders underlined). Top keys are runtime-assigned (first submenu
                // item's key) and may be absent from the title (File->'o') — WPF
                // cannot express that in text, so we inject the marker on the first
                // occurrence of the letter, else prefix with an underscore+letter.
                // Top access keys are runtime-assigned (first submenu item's key)
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
                foreach (var (act, label) in items)
                {
                    if (act == null) // separator marker
                    {
                        mi.Items.Add(new Separator());
                        ledger.Add((topName, "", "", true));
                        continue;
                    }
                    var sc = NormalizeShortcut(act.Shortcut);
                    var child = new MenuItem
                    {
                        // DISPLAY text is branded (D1); the ledger below keeps
                        // the Oracle label so matrix-replay audits stay verbatim.
                        Header = ApplyBrand(ResolveAccess(label)),            // label without '&'
                        InputGestureText = string.IsNullOrEmpty(sc) ? null : sc,
                        ToolTip = TooltipOf(act),
                    };
                    // A real KeyBinding (not just InputGestureText) is what makes
                    // WPF merge the gesture into the UIA Name as "Label\tCtrl+T" —
                    // the exact format the Oracle live baseline shows.
                    if (TryKeyGesture(sc, out var gesture, out var gkey))
                        child.InputBindings.Add(new KeyBinding(new RelayCommand(), gkey, gesture));
                    // Gray state: only view-capability rows are STATICally disabled
                    // (TMenuUpdater capability mask). state-dependent items stay
                    // enabled here — they flip only when session content changes,
                    // and the captured Oracle snapshots show enabled=false only in
                    // the exact view list (empty sessions), which our per-view
                    // ledger replay compares against below.
                    child.IsEnabled = IsEnabledIn(spec, topName, label);
                    if (!string.IsNullOrEmpty(act.Key))
                        System.Windows.Automation.AutomationProperties.SetAutomationId(child, act.Key);
                    child.Tag = act;
                    mi.Items.Add(child);
                    ledger.Add((topName, label, sc, child.IsEnabled));
                }
                menu.Items.Add(mi);
            }
            return (menu, ledger);
        }

        // Menu MEMBERSHIP is the live fact (presence matrix); the action catalog
        // supplies shortcut/hint, and per-view forms (TFILEACTIONS + TTEXTACTIONS
        // for a text session) redefine the same action NAME — the view's own form
        // wins. Caption Category is NOT authoritative (measured: 'Show All' is
        // Favorites-category but lives in the View menu).
        private static List<(MenuAction, string)> ItemsForMenu(MenuSpec spec, string menuName)
        {
            var present = spec.Presence.Where(p => p.Menu == menuName &&
                p.PresentIn.Contains(spec.View, StringComparer.Ordinal)).ToList();
            if (present.Count == 0) return new();

            var seq = new List<(MenuAction, string)>();
            foreach (var row in present)
            {
                var label = row.Item;
                MenuAction pick = null;
                foreach (var a in spec.Actions)
                {
                    if (Plain(ExpandFormat(a.Caption, spec.View)) != label) continue;
                    if (spec.ViewForms != null && spec.ViewForms.Count > 0 &&
                        !spec.ViewForms.Contains(a.Form ?? "", StringComparer.Ordinal)) continue;
                    pick = a; break;
                }
                if (pick == null)  // label built at runtime (Info/Report dialogs)
                    pick = new MenuAction { Caption = label, Category = menuName };
                seq.Add((pick, label));
            }
            // Live order is the contract (TMenuPopulator output); presence rows
            // are label-sorted in the matrix, so re-sort by the recorded order.
            var key = spec.View + "|" + menuName;
            if (spec.ItemOrder != null && spec.ItemOrder.TryGetValue(key, out var ord))
            {
                var idx = new Dictionary<string, int>();
                for (int i = 0; i < ord.Count; i++) if (!idx.ContainsKey(ord[i])) idx[ord[i]] = i;
                seq.Sort((a, b) =>
                {
                    int ai = idx.TryGetValue(a.Item2, out var x) ? x : int.MaxValue;
                    int bi = idx.TryGetValue(b.Item2, out var y) ? y : int.MaxValue;
                    return ai.CompareTo(bi);
                });
            }
            return seq;
        }

        // Enabled truth comes from the 12 live snapshots (enabled-matrix.json).
        // Measured semantics (captured_state = freshly-loaded empty sessions):
        //   always-enabled   -> enabled wherever present;
        //   view-capability  -> statically gray in its view list (TMenuUpdater
        //                       capability mask);
        //   state-dependent  -> gray only in the captured empty-session views;
        //                       flips on content — replay uses the same empty-
        //                       session baseline, so identical rule here.
        // A label with no recorded row defaults to enabled (BC shows no gray
        // without evidence).
        private static bool IsEnabledIn(MenuSpec spec, string menu, string label)
        {
            foreach (var r in spec.Enabled)
                if (r.Menu == menu && r.Label == label)
                    return r.Cls == "always-enabled"
                        || !r.DisabledIn.Contains(spec.View, StringComparer.Ordinal);
            return true;
        }

        /// <summary>
        /// Expand Pascal-style format strings measured in the DFMs:
        ///   '%s' / '%0:s' + view name  -> 'About %s' => 'About Beyond Compare',
        ///                                  '%0:s &Info' => 'Text Compare Info'
        /// </summary>
        public static string ExpandFormat(string caption, string view = "")
        {
            if (string.IsNullOrEmpty(caption)) return "";
            if (!caption.Contains('%')) return caption;
            var subject = !string.IsNullOrEmpty(view) ? view : "Beyond Compare";
            var result = System.Text.RegularExpressions.Regex.Replace(
                caption, @"%\d*:?s", subject);
            return result;
        }

        /// <summary>
        /// Normalize shortcut modifier order to Win32 display order (Ctrl+Shift+Alt),
        /// which is what the live UIA baseline shows ('Ctrl+Shift+O'), while DFM
        /// ActionList uses Pascal order ('Shift+Ctrl+O').
        /// </summary>
        public static string NormalizeShortcut(string sc)
        {
            if (string.IsNullOrEmpty(sc)) return "";
            var order = new[] { "Ctrl", "Alt", "Shift", "Meta" }; // measured live order
            var parts = sc.Split('+');
            var mods = parts.Where(p => order.Contains(p, StringComparer.Ordinal)).ToList();
            var key = parts.Where(p => !order.Contains(p, StringComparer.Ordinal)).ToList();
            var ordered = order.Where(o => mods.Contains(o, StringComparer.Ordinal)).ToList();
            ordered.AddRange(key);
            return string.Join("+", ordered);
        }

        /// <summary>Strip '&' (access-key marker) — WPF consumes it differently.</summary>
        public static string Plain(string caption)
        {
            if (string.IsNullOrEmpty(caption)) return "";
            return caption.Replace("&", "");
        }

        /// <summary>Inject the access-key marker ('_') before the key letter.
        /// WPF derives AccessKey from the marker; the custom peer strips it from Name.</summary>
        public static string InjectKey(string header, string key)
        {
            if (string.IsNullOrEmpty(key)) return header;
            int at = header.IndexOf(key, StringComparison.OrdinalIgnoreCase);
            return at >= 0 ? header.Insert(at, "_") : header;
        }

        /// <summary>WPF Header honors '_'/'&' doubling; convert VCL single & to WPF double.</summary>
        public static string ResolveAccess(string caption)
        {
            if (string.IsNullOrEmpty(caption)) return "";
            return caption;  // VCL and WPF share the same '&' access-key marker
        }

        public static bool TryKeyGesture(string sc, out ModifierKeys mods, out Key key)
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

        private static string TooltipOf(MenuAction a)
        {
            if (string.IsNullOrEmpty(a.Hint)) return null;
            var parts = a.Hint.Split('|');
            return parts.Length > 1 ? parts[1] : parts[0];
        }
    }

    internal sealed class RelayCommand : System.Windows.Input.ICommand
    {
        public event EventHandler CanExecuteChanged;
        public bool CanExecute(object _) => true;
        public void Execute(object _) { }
    }

    /// <summary>
    /// BC's UIA contract for menu items (measured in the live baseline):
    ///   Name       = "<label with access marker removed>\t<gesture>"
    ///   AccessKey  = single letter ('' when none)
    /// WPF's stock MenuItem peer reports only the header text, so we override.
    /// </summary>
    /// <summary>
    /// BC's UIA contract for menu items (measured in the live baseline):
    ///   Name       = "<label, access marker removed>\t<gesture>"
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

        // FrameworkElementAutomationPeer defaults these from the owner; state them
        // explicitly so the item stays in the control view (a peer that reports
        // IsControlElement=false is pruned — that is what dropped our items).
        protected override bool IsControlElementCore() => true;
        protected override AutomationControlType GetAutomationControlTypeCore()
            => AutomationControlType.MenuItem;
        protected override string GetClassNameCore() => "MenuItem";

        protected override string GetNameCore()
        {
            var header = ((MenuItem)Owner).Header as string ?? "";
            var plain = header.Replace("_", "");
            // '&&' is a literal ampersand; single '&' marks the access key
            plain = plain.Replace("&&", "\u0000").Replace("&", "").Replace("\u0000", "&");
            var gesture = ((MenuItem)Owner).InputGestureText;
            return string.IsNullOrEmpty(gesture) ? plain : plain + "\t" + gesture;
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
