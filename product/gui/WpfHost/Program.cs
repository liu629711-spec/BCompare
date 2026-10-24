// reacmp-gui WPF host: data-driven form renderer (ADR-7) + fidelity dumper.
//
// Contract: the form descriptor JSON shape {name, cls, props, children} is the
// SAME as extracted/guibaseline/forms-en.json (tools/dfm-baseline.py output).
// Build(descriptor) -> WPF visual tree. Dump re-walks the ACTUAL visual tree:
//   - every model node must be attached (renderer kept it);
//   - actual Canvas.Left/Top/Width/Height must equal model geometry;
//   - control text (TextBlock/CheckBox/TextBox) must equal Translate(Caption).
// Fidelity violations go to stderr with exit code 1 (they are failures, not noise).
// The emitted descriptor then passes ui-structure-check.py 'full' vs the golden.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Automation.Peers;
using System.Windows.Media;

namespace ReaCompare.Gui
{
    internal sealed class Node
    {
        public string Name = "";
        public string Cls = "";
        public Dictionary<string, JsonElement> Props = new();
        public List<Node> Children = new();

        public string Str(string k) => Props.TryGetValue(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
        public bool? Bool(string k) => Props.TryGetValue(k, out var v) ? (v.ValueKind == JsonValueKind.True ? true : v.ValueKind == JsonValueKind.False ? false : (bool?)null) : null;
        public int? Int(string k) => Props.TryGetValue(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetInt32() : null;
    }

    internal static class Program
    {
        [STAThread]
        private static int Main(string[] args)
        {
            // ---- menu mode: reacmp-gui --menu-spec spec.json (--view "Text Compare" | --dispatch L R)
            //      [--dump ledger.json] [--show]
            if (args.Length > 0 && args[0] == "--menu-spec")
            {
                string specPath = null, view = null, ledgerPath = null; bool showM = false;
                string dLeft = null, dRight = null, enginePath = null, colorsPath = null, filterOpt = null, theme = null;
                string mLeft = null, mRight = null, mCenter = null, mOut = null; bool mergeMode = false;
                for (int i = 1; i < args.Length; i++)
                    switch (args[i])
                    {
                        case "--view": view = args[++i]; break;
                        case "--dump": ledgerPath = args[++i]; break;
                        case "--show": showM = true; break;
                        case "--dispatch": dLeft = args[++i]; dRight = args[++i]; break;
                        // Text Merge view (D4): BC's own positional order
                        // Left Right Center [Output] (verified
                        // command_line_reference.html; the 4th file is the
                        // SAVE TARGET — measured §6.17: never loaded, written
                        // only on explicit Ctrl+S).
                        case "--merge":
                            mergeMode = true; mLeft = args[++i]; mRight = args[++i]; mCenter = args[++i];
                            if (i + 1 < args.Length && !args[i + 1].StartsWith("--") && args[i + 1] != "--show" && args[i + 1] != "--dump")
                                mOut = args[++i];
                            break;
                        case "--engine": enginePath = args[++i]; break;
                        case "--colors": colorsPath = args[++i]; break;
                        case "--display": filterOpt = args[++i]; break;
                        case "--theme": theme = args[++i]; break;
                        default: specPath = args[i]; break;
                    }
                if (mergeMode)
                    return MergeMode.Run(specPath, mLeft, mRight, mCenter, mOut, ledgerPath, showM, enginePath, colorsPath, theme);
                return MenuMode.Run(specPath, view, ledgerPath, showM, dLeft, dRight, enginePath, colorsPath, filterOpt, theme);
            }

            string descriptor = null, dumpTo = null, formName = null; bool show = false;
            for (int i = 0; i < args.Length; i++)
                switch (args[i])
                {
                    case "--dump": dumpTo = args[++i]; break;
                    case "--form": formName = args[++i]; break;
                    case "--show": show = true; break;
                    default: descriptor = args[i]; break;
                }
            if (descriptor == null || !File.Exists(descriptor))
            {
                Console.Error.WriteLine("usage: reacmp-gui <descriptor.json> [--form NAME] [--dump out.json] [--show]\n" +
                                        "   or: reacmp-gui --menu-spec spec.json --view NAME [--dump ledger.json] [--show]");
                return 2;
            }
            var root = Loader.Load(descriptor, formName);
            var tree = Renderer.Build(root);

            if (dumpTo != null)
            {
                var (json, problems) = Dumper.Dump(root, tree);
                foreach (var p in problems) Console.Error.WriteLine("FIDELITY: " + p);
                File.WriteAllText(dumpTo, json);
                Console.WriteLine($"dumped -> {dumpTo} (problems={problems.Count})");
                if (!show) return problems.Count == 0 ? 0 : 1;
            }
            if (show)
            {
                var app = new Application();
                if (tree is Window w) { w.Show(); app.Run(w); }
                else app.Run();
                return 0;
            }
            Console.WriteLine($"built tree for {root.Name}: {tree.GetType().Name}");
            return 0;
        }
    }

    internal static class Loader
    {
        public static Node Load(string path, string formFilter)
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            JsonElement e = doc.RootElement;
            if (!e.TryGetProperty("cls", out _))
            {
                if (formFilter != null)
                {
                    if (!e.TryGetProperty(formFilter, out e)) throw new Exception($"form {formFilter} not in {path}");
                }
                else foreach (var p in e.EnumerateObject()) { e = p.Value; break; }
            }
            return Parse(e);
        }

        private static Node Parse(JsonElement e)
        {
            var n = new Node
            {
                Name = e.TryGetProperty("name", out var nm) ? nm.GetString() : "",
                Cls = e.TryGetProperty("cls", out var c) ? c.GetString() : "",
            };
            if (e.TryGetProperty("props", out var p) && p.ValueKind == JsonValueKind.Object)
                foreach (var kv in p.EnumerateObject()) n.Props[kv.Name] = kv.Value.Clone();
            if (e.TryGetProperty("children", out var ch) && ch.ValueKind == JsonValueKind.Array)
                foreach (var kid in ch.EnumerateArray()) n.Children.Add(Parse(kid));
            return n;
        }
    }

    internal static class Tagged
    {
        public static readonly DependencyProperty DescriptorProperty =
            DependencyProperty.RegisterAttached("Descriptor", typeof(Node), typeof(Tagged), new PropertyMetadata(null));
    }

    // Panels must survive the UIA control view: default peers of layout-only
    // containers get pruned, hiding the tree shape the contract guarantees.
    internal sealed class PanelHost : ContentControl
    {
        protected override AutomationPeer OnCreateAutomationPeer() => new PanelPeer(this);

        private sealed class PanelPeer : FrameworkElementAutomationPeer
        {
            public PanelPeer(PanelHost o) : base(o) { }
            protected override bool IsControlElementCore() => true;
            protected override System.Windows.Automation.Peers.AutomationControlType GetAutomationControlTypeCore()
                => System.Windows.Automation.Peers.AutomationControlType.Pane;
            protected override string GetClassNameCore() => "Pane";
        }
    }

    internal static class Renderer
    {
        public static FrameworkElement Build(Node root)
        {
            if (root.Cls.Contains("Dialog"))
            {
                var win = new Window
                {
                    Title = Translate(Tr(root.Str("Caption")) ?? root.Name),
                    Width = root.Int("ClientWidth") ?? 400,
                    Height = root.Int("ClientHeight") ?? 300,
                    MinHeight = Math.Min(root.Int("ClientHeight") ?? 300, 40),
                    MinWidth = Math.Min(root.Int("ClientWidth") ?? 400, 40),
                    WindowStartupLocation = WindowStartupLocation.CenterScreen,
                    Content = BuildCanvas(root),
                };
                win.SetValue(Tagged.DescriptorProperty, root);
                if (!string.IsNullOrEmpty(root.Name))
                    System.Windows.Automation.AutomationProperties.SetAutomationId(win, root.Name);
                return win;
            }
            // Data-module / resource forms (T*ACTIONS, T*IMAGES): BC never shows
            // them; render them off-screen windows so the descriptor contract
            // (Canvas with exact ClientWidth/Height) is still verifiable.
            var mod = new Window
            {
                Title = root.Name,
                Width = root.Int("Width") ?? root.Int("ClientWidth") ?? 400,
                Height = root.Int("Height") ?? root.Int("ClientHeight") ?? 300,
                MinHeight = 1,
                MinWidth = 1,
                WindowStyle = WindowStyle.None,
                AllowsTransparency = true,
                ShowInTaskbar = false,
                Left = -4000,
                Top = -4000,
                Content = BuildCanvas(root),
            };
            mod.SetValue(Tagged.DescriptorProperty, root);
            if (!string.IsNullOrEmpty(root.Name))
                System.Windows.Automation.AutomationProperties.SetAutomationId(mod, root.Name);
            return mod;
        }

        private static string Tr(string s) => s == "%" ? null : s; // '%' = runtime-filled placeholder in BC DFMs

        private static Canvas BuildCanvas(Node form)
        {
            var cv = new Canvas
            {
                Width = form.Int("ClientWidth") ?? form.Int("Width") ?? 400,
                Height = form.Int("ClientHeight") ?? form.Int("Height") ?? 300,
                Background = BrushFromVcl(form.Int("Color")) ?? Brushes.White,
            };
            foreach (var c in form.Children) Place(cv, c);
            cv.SetValue(Tagged.DescriptorProperty, form);
            return cv;
        }

        private static void Place(Canvas cv, Node c)
        {
            var el = BuildControl(c);
            Canvas.SetLeft(el, c.Int("Left") ?? 0);
            Canvas.SetTop(el, c.Int("Top") ?? 0);
            cv.Children.Add(el);
        }

        public static FrameworkElement BuildControl(Node n)
        {
            FrameworkElement el = n.Cls switch
            {
                "TUiLabel" => MakeLabel(n, false),
                "TUiLinkLabel" => MakeLabel(n, true),
                "TUiMemo" => MakeMemo(n),
                "TUiCheckBox" => new CheckBox { Content = Translate(Tr(n.Str("Caption"))) },
                "TUiImage" => new Image(),
                "TUiCloseBtn" => new Button { Content = "X" },
                _ => MakePanel(n),
            };
            if (n.Int("Width") is int w && double.IsNaN(el.Width)) el.Width = w;
            if (n.Int("Height") is int h && double.IsNaN(el.Height)) el.Height = h;
            el.SetValue(Tagged.DescriptorProperty, n);
            if (!string.IsNullOrEmpty(n.Name))
                System.Windows.Automation.AutomationProperties.SetAutomationId(el, n.Name);
            return el;
        }

        private static FrameworkElement MakeLabel(Node n, bool link)
        {
            var text = Translate(Tr(n.Str("Caption"))) ?? "";
            FrameworkElement box = n.Cls == "TUiLinkLabel"
                ? new TextBlock { Text = text, Foreground = Brushes.RoyalBlue, TextDecorations = System.Windows.TextDecorations.Underline }
                : new TextBlock { Text = text, Foreground = BrushFromVcl(n.Int("FontColor")) ?? Brushes.Black };
            if (box is TextBlock tb)
            {
                tb.TextAlignment = n.Str("Alignment") switch
                {
                    "taCenter" => TextAlignment.Center,
                    "taRightJustify" => TextAlignment.Right,
                    _ => TextAlignment.Left,
                };
                tb.TextWrapping = n.Bool("WordWrap") == true ? TextWrapping.Wrap : TextWrapping.NoWrap;
            }
            return box;
        }

        private static TextBox MakeMemo(Node n)
        {
            var lines = new List<string>();
            if (n.Props.TryGetValue("Lines.Strings", out var ls) && ls.ValueKind == JsonValueKind.Array)
                foreach (var l in ls.EnumerateArray()) if (l.ValueKind == JsonValueKind.String) lines.Add(l.GetString());
            return new TextBox
            {
                Text = Translate(string.Join("\n", lines)),
                IsReadOnly = n.Bool("ReadOnly") ?? false,
                AcceptsReturn = n.Bool("WantReturns") ?? true,
                Background = Brushes.Transparent,
            };
        }

        private static FrameworkElement MakePanel(Node n)
        {
            var inner = new Canvas();
            foreach (var c in n.Children) Place(inner, c);
            var border = new Border
            {
                Background = BrushFromVcl(n.Int("Color")) ?? (n.Bool("ParentBackground") == false ? Brushes.LightGray : Brushes.Transparent),
                Child = inner,
            };
            // ContentControl produces a real AutomationPeer, so the container's
            // AutomationId surfaces in the UIA tree (plain Border/Canvas do not).
            var host = new PanelHost { Content = border, Focusable = false };
            if (n.Int("Width") is int w) host.Width = w;
            if (n.Int("Height") is int h) host.Height = h;
            host.SetValue(Tagged.DescriptorProperty, n);
            if (!string.IsNullOrEmpty(n.Name))
                System.Windows.Automation.AutomationProperties.SetAutomationId(host, n.Name);
            // empty ContentControls get pruned from the UIA control view unless
            // they carry a name; captions (when present) are the fidelity target.
            var cap = n.Str("Caption");
            if (cap != null && cap != "%")
                System.Windows.Automation.AutomationProperties.SetName(host, cap);
            else
                System.Windows.Automation.AutomationProperties.SetName(host, n.Name);
            return host;
        }

        // identity translation table hook (localization later, docs/19 U-gui-3).
        // D1 (docs/20): brand swap flows through this single point, so dialog/
        // form DISPLAY text says LiuCompare while the descriptor contract (the
        // emitted dump JSON copies model props verbatim) stays the DFM golden —
        // ui-structure-check compares descriptors, not pixels, and remains green.
        public static string Translate(string s) => MenuBuilder.ApplyBrand(s);

        public static Brush BrushFromVcl(int? tcolor)
        {
            if (tcolor == null) return null;
            int c = tcolor.Value;
            return new SolidColorBrush(Color.FromRgb((byte)((c >> 16) & 0xFF), (byte)((c >> 8) & 0xFF), (byte)(c & 0xFF)));
        }
    }

    internal static class Dumper
    {
        // Re-walks model vs ACTUAL visual tree; emits descriptor JSON only with
        // fidelity verified. Returns (json, problems).
        public static (string, List<string>) Dump(Node model, FrameworkElement built)
        {
            var problems = new List<string>();
            FrameworkElement rootScope = built;
            bool isRoot = true;
            string SerializeNode(Node n, DependencyObject scope)
            {
                var el = FindIn(scope, n, out bool viaParent);
                if (el == null) { problems.Add($"node not attached: {n.Cls}/{n.Name}"); }
                else
                {
                    // geometry fidelity. Root's Left/Top are window placement, not
                    // contract data (BC stores the form's screen position there);
                    // only child coordinates inside the canvas are contractual.
                    if (!isRoot)
                    {
                        Check(n, "Left", Canvas.GetLeft(el), problems);
                        Check(n, "Top", Canvas.GetTop(el), problems);
                    }
                    if (n.Int("Width") is int w && !double.IsNaN(el.Width) && Math.Abs(w - el.Width) > 0.5)
                        problems.Add($"Width mismatch {n.Name}: model={w} actual={el.Width}");
                    if (n.Int("Height") is int h && !double.IsNaN(el.Height) && Math.Abs(h - el.Height) > 0.5)
                        problems.Add($"Height mismatch {n.Name}: model={h} actual={el.Height}");
                    // text fidelity
                    string actualText = el switch
                    {
                        TextBlock tb => tb.Text,
                        CheckBox cb => cb.Content as string,
                        TextBox tbb => tbb.Text,
                        Button b => b.Content as string,
                        _ => null,
                    };
                    if (actualText != null)
                    {
                        string expect = Renderer.Translate(Ph(n.Str("Caption")));
                        if (n.Str("Caption") != null && expect != actualText && actualText != "%")
                            problems.Add($"caption mismatch {n.Name}: model={expect} actual={actualText}");
                    }
                }
                var props = new Dictionary<string, object>();
                foreach (var kv in n.Props) props[kv.Key] = kv.Value;
                var obj = new Dictionary<string, object> { ["name"] = n.Name, ["cls"] = n.Cls, ["props"] = props };
                if (n.Children.Count > 0)
                {
                    var kids = new List<JsonElement>();
                    bool wasRoot = isRoot; isRoot = false;
                    foreach (var c in n.Children) kids.Add(JsonSerializer.Deserialize<JsonElement>(SerializeNode(c, el ?? scope)));
                    isRoot = wasRoot;
                    obj["children"] = kids;
                }
                return JsonSerializer.Serialize(obj);
            }

            string outJson = SerializeNode(model, rootScope);
            return (outJson, problems);

            static string Ph(string s) => s == "%" ? "" : s;

            static void Check(Node n, string key, double actual, List<string> problems)
            {
                if (n.Int(key) is int m && Math.Abs(m - actual) > 0.5)
                    problems.Add($"{key} mismatch {n.Name}: model={m} actual={actual}");
            }
        }

        private static FrameworkElement FindIn(DependencyObject scope, Node n, out bool _)
        {
            var found = FindCore(scope, n);
            _ = found != null;
            return found;
        }

        private static FrameworkElement FindCore(DependencyObject scope, Node n)
        {
            if (scope == null) return null;
            if (ReferenceEquals(scope.GetValue(Tagged.DescriptorProperty), n)) return scope as FrameworkElement;
            int cnt = VisualTreeHelper.GetChildrenCount(scope);
            for (int i = 0; i < cnt; i++)
            {
                var r = FindCore(VisualTreeHelper.GetChild(scope, i), n);
                if (r != null) return r;
            }
            if (scope is ContentControl cc && cc.Content is DependencyObject ce) return FindCore(ce, n);
            if (scope is Window wn && wn.Content is DependencyObject wc) return FindCore(wc, n);
            return null;
        }
    }
}
