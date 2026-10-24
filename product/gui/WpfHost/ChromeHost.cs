// Chrome + content-view replication: live toolbars/statusbars (chrome-matrix.json)
// and the BC-classed widget skeleton (from each view's home_tree) are replayed
// verbatim as UIA elements carrying the exact (control_type, class, name) triple
// the Oracle snapshot shows. Data-driven — no per-view hardcoding.

using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Automation.Peers;
using System.Windows.Controls;
using System.Windows.Media;

namespace ReaCompare.Gui
{
    internal sealed class ChromeItem
    {
        public string Ct = "";      // UIA control type name: Button/Separator/Pane/...
        public string Cls = "";     // BC class (TUiTreeButton, TUiSpecComboBox, ...)
        public string Name = "";    // visible label ('' when none)
        // engine-wired role tag (docs/19 §6.12 tier-1): 'footer-left' /
        // 'footer-right' on the two pane footer cells, set from the measured
        // sb row order BEFORE rows are consumed. Offline paths never set it;
        // the ledgers record only ct/cls/name, so the 410-chrome gate is
        // untouched.
        public string Role = "";
        // dynamic name source for engine-wired cells (footer N:C follows the
        // shared cursor, docs/19 §6.12); null = static measured Name.
        public System.Func<string> LiveName;
    }

    internal sealed class ChromeRow
    {
        public string Section = "tb"; // "tb" toolbar row | "sb" statusbar row
        public int Index;
        public List<ChromeItem> Items = new();
    }

    /// <summary>One content-view skeleton node (spec "skeleton" block): identity
    /// triple + optional consumed chrome row (sec,index) + children.</summary>
    internal sealed class SkelNode
    {
        public ChromeItem Identity = new();
        public string[] Row;                 // null | [sec, idx]
        public List<SkelNode> Children = new();
    }

    internal static class ChromeCt
    {
        // The full control-type vocabulary observed across the 12 live snapshots
        // (chrome-matrix + home_tree). Unmapped => Custom (never silently wrong).
        public static AutomationControlType Map(string ct) => ct switch
        {
            "Button" => AutomationControlType.Button,
            "RadioButton" => AutomationControlType.RadioButton,
            "CheckBox" => AutomationControlType.CheckBox,
            "ComboBox" => AutomationControlType.ComboBox,
            "Edit" => AutomationControlType.Edit,
            "MenuItem" => AutomationControlType.MenuItem,
            "MenuBar" => AutomationControlType.MenuBar,
            "Pane" => AutomationControlType.Pane,
            "Separator" => AutomationControlType.Separator,
            "Text" => AutomationControlType.Text,
            "Custom" => AutomationControlType.Custom,
            "ToolBar" => AutomationControlType.ToolBar,
            "StatusBar" => AutomationControlType.StatusBar,
            "ScrollBar" => AutomationControlType.ScrollBar,
            "Slider" => AutomationControlType.Slider,
            "Spinner" => AutomationControlType.Spinner,
            "ProgressBar" => AutomationControlType.ProgressBar,
            "Tab" => AutomationControlType.Tab,
            "TabItem" => AutomationControlType.TabItem,
            "Tree" => AutomationControlType.Tree,
            "DataGrid" => AutomationControlType.DataGrid,
            "Image" => AutomationControlType.Image,
            _ => AutomationControlType.Custom,
        };
    }

    internal static class ChromeBuilder
    {
        /// <summary>Build one StackPanel row per captured toolbar/statusbar.
        /// Row containers are addressable via AutomationId "chrome:{section}:{i}"
        /// so the live checker can locate them without shape coupling.
        /// decorate (engine-wired mode) can attach selection/click behavior to
        /// named buttons (measured filter bar; see MenuMode).</summary>
        public static List<FrameworkElement> BuildRows(List<ChromeRow> rows,
            out List<Dictionary<string, object>> ledger,
            Action<ChromeElement, ChromeItem> decorate = null)
        {
            ledger = new();
            var built = new List<FrameworkElement>();
            foreach (var row in rows)
            {
                var panel = new StackPanel { Orientation = Orientation.Horizontal };
                var lrow = new Dictionary<string, object>
                {
                    ["section"] = row.Section, ["index"] = row.Index, ["items"] = new List<object>(),
                };
                var items = (List<object>)lrow["items"];
                foreach (var it in row.Items)
                {
                    var el = new ChromeElement(it, row.Section == "tb");
                    decorate?.Invoke(el, it);
                    panel.Children.Add(el);
                    items.Add(new Dictionary<string, object>
                    {
                        ["ct"] = it.Ct, ["cls"] = it.Cls, ["name"] = it.Name,
                    });
                }
                // StackPanel is layout-only (peer pruned from the control view) —
                // wrap it in a PanelHost so the row is addressable by AutomationId
                // while the items stay children.
                var host = new PanelHost { Content = panel };
                AutomationProperties.SetAutomationId(host, $"chrome:{row.Section}:{row.Index}");
                built.Add(host);
                ledger.Add(lrow);
            }
            return built;
        }

        /// <summary>Render a content-view skeleton node. ToolBar/StatusBar nodes
        /// embed their consumed chrome row (from the row tables); other nodes are
        /// containers (PanelHost) holding children, or leaves (ChromeElement).
        /// attach (engine-wired mode only) can hand a subtree an owner-drawn
        /// content overlay (e.g. the text diff pane inside TTextEditor): the
        /// overlay is inserted as the FIRST child of the container's StackPanel,
        /// and a plain FrameworkElement carries NO AutomationPeer (base
        /// OnCreateAutomationPeer returns null), so the UIA control view and the
        /// 290-node skeleton check are untouched — matching the measured fact
        /// that BC's TTextEditor exposes no line content to accessibility.</summary>
        public static FrameworkElement BuildSkelNode(SkelNode n, List<ChromeRow> tbs, List<ChromeRow> sbs,
            Func<SkelNode, FrameworkElement> attach = null,
            Action<ChromeElement, ChromeItem> decorate = null)
        {
            // Engine-mode measured root spatial model (docs/19 §6.12B,
            // window-relative rects from textlayout-en step0):
            //   toolbar row on top        TUiDock      [8,58,1440,44]
            //   window status bar bottom  TUiStatusBar [8,831,1440,25]
            //   middle band = [overview strip 52px | pane area]
            //                TUiThumbnail [8,102,52,729]  TUiPanel [60,102,1388,729]
            // UIA order stays the spec PREORDER (children are added in spec
            // order; Grid only moves pixels — same rule as the mirrored panes).
            if (attach != null && n.Children.Count == 4 &&
                n.Children[3].Identity.Cls == "TUiThumbnail")
                return BuildRootArea(n, tbs, sbs, attach, decorate);
            if (attach != null && n.Children.Count == 4 &&
                n.Children[2].Identity.Cls == "TLogFrame" &&
                n.Children[3].Identity.Cls == "TUiPanel")
                return BuildFolderRootArea(n, tbs, sbs, attach, decorate);
            if (n.Row != null && n.Row.Length == 2)
            {
                var rows = n.Row[0] == "tb" ? tbs : sbs;
                int idx = int.Parse(n.Row[1]);
                if (idx < rows.Count)
                {
                    var row = rows[idx];
                    var panel = new StackPanel { Orientation = n.Row[0] == "tb" ? Orientation.Horizontal : Orientation.Horizontal };
                    foreach (var it in row.Items)
                    {
                        var el = new ChromeElement(it, n.Row[0] == "tb");
                        decorate?.Invoke(el, it);
                        panel.Children.Add(el);
                    }
                    var tbHost = new ChromeContainer(n.Identity) { Content = panel };
                    AutomationProperties.SetAutomationId(tbHost, $"chrome:{n.Row[0]}:{idx}");
                    return tbHost;
                }
            }
            if (n.Children.Count > 0 || attach != null)
            {
                Panel sp;
                if (attach != null && n.Children.Count == 2)
                {
                    // Engine-mode measured layout rules (docs/19 §6.12 rects
                    // from textlayout-en step0; the spatial model is the BC
                    // reference = presentation-axis 布局参考, docs/20 §3):
                    //  - container whose two children EACH hold a TTextEditor
                    //    pane: side-by-side (measured: both editors at y=180,
                    //    x=86 w=694 / x=784 w=690 — full width pair);
                    //  - container mixing one editor subtree with one
                    //    details-band subtree: VERTICAL with details at the
                    //    BOTTOM (measured: bands y808/824 below the editors
                    //    ending ~y807; DFM DetailsPanel alBottom). UIA child
                    //    ORDER stays the spec preorder either way.
                    bool aEd = SubtreeHas(n.Children[0], "TTextEditor") ||
                               SubtreeHas(n.Children[0], "THexEditor") ||
                               SubtreeHas(n.Children[0], "TDirTreeView");
                    bool bEd = SubtreeHas(n.Children[1], "TTextEditor") ||
                               SubtreeHas(n.Children[1], "THexEditor") ||
                               SubtreeHas(n.Children[1], "TDirTreeView");
                    bool aDet = SubtreeHas(n.Children[0], "TTextDetailsEditor");
                    bool bDet = SubtreeHas(n.Children[1], "TTextDetailsEditor");
                    bool aTb = SubtreeHas(n.Children[0], "TUiToolbar") ||
                               n.Children[0].Identity.Ct == "ToolBar";
                    bool bTb = SubtreeHas(n.Children[1], "TUiToolbar") ||
                               n.Children[1].Identity.Ct == "ToolBar";
                    if (aEd && bEd)
                    {
                        var gridH = new System.Windows.Controls.Grid();
                        gridH.ColumnDefinitions.Add(new System.Windows.Controls.ColumnDefinition
                        { Width = new System.Windows.GridLength(1, System.Windows.GridUnitType.Star) });
                        gridH.ColumnDefinitions.Add(new System.Windows.Controls.ColumnDefinition
                        { Width = new System.Windows.GridLength(1, System.Windows.GridUnitType.Star) });
                        sp = gridH;
                    }
                    else if ((aEd && bDet) || (bEd && aDet))
                    {
                        var gridV = new System.Windows.Controls.Grid();
                        gridV.RowDefinitions.Add(new System.Windows.Controls.RowDefinition
                        { Height = new System.Windows.GridLength(1, System.Windows.GridUnitType.Star) });
                        gridV.RowDefinitions.Add(new System.Windows.Controls.RowDefinition
                        { Height = System.Windows.GridLength.Auto });
                        sp = gridV;
                    }
                    else if ((aEd && bTb) || (bEd && aTb))
                    {
                        // hex pane (docs/19 §6.19): per-side path TOOLBAR ABOVE
                        // the editor (measured bar ~y102-128, editor y154+) —
                        // tree order is editor-first, so the toolbar subtree
                        // docks the auto row 0 and the editor fills row 1.
                        var gridV = new System.Windows.Controls.Grid();
                        gridV.RowDefinitions.Add(new System.Windows.Controls.RowDefinition
                        { Height = System.Windows.GridLength.Auto });
                        gridV.RowDefinitions.Add(new System.Windows.Controls.RowDefinition
                        { Height = new System.Windows.GridLength(1, System.Windows.GridUnitType.Star) });
                        sp = gridV;
                    }
                    else sp = new StackPanel { Orientation = Orientation.Vertical };
                }
                else sp = new StackPanel { Orientation = Orientation.Vertical };
                var overlay = attach?.Invoke(n);
                if (overlay != null) sp.Children.Add(overlay);
                for (int ci = 0; ci < n.Children.Count; ci++)
                {
                    var child = BuildSkelNode(n.Children[ci], tbs, sbs, attach, decorate);
                    if (sp is System.Windows.Controls.Grid g && n.Children.Count == 2)
                    {
                        if (g.ColumnDefinitions.Count == 2)
                            // measured BC: the TREE-FIRST editor is at screen
                            // RIGHT (x=784, gui-text-session-en rects) — the
                            // visual order is right-file on the right while
                            // the UIA tree enumerates it first. Mirror the
                            // child index into the opposite column.
                            System.Windows.Controls.Grid.SetColumn(child, 1 - ci);
                        else if (g.RowDefinitions.Count == 2)
                        {
                            bool childHasEditors = SubtreeHas(n.Children[ci], "TTextEditor") ||
                                                   SubtreeHas(n.Children[ci], "THexEditor");
                            bool childHasBar = SubtreeHas(n.Children[ci], "TUiToolbar") ||
                                               n.Children[ci].Identity.Ct == "ToolBar";
                            // text: editors fill the star row 0; the details
                            // subtree docks the auto row 1 (measured: bands BELOW).
                            // hex (editor above toolbar in tree): the toolbar
                            // docks the auto row 0, the editor fills the star
                            // row 1 (measured: per-side bar ABOVE the editor).
                            bool barOnTop = g.RowDefinitions[0].Height.IsAuto &&
                                            g.RowDefinitions[1].Height.IsStar;
                            System.Windows.Controls.Grid.SetRow(child,
                                barOnTop ? (childHasEditors ? 1 : 0)
                                         : (childHasEditors ? 0 : (childHasBar ? 1 : 1)));
                        }
                    }
                    sp.Children.Add(child);
                }
                var host = new ChromeContainer(n.Identity) { Content = sp };
                if (n.Children.Count == 1) host.Margin = new Thickness(0);
                return host;
            }
            // Engine-mode overview strip: TUiThumbnail is a leaf slot in the
            // spec; attach paints the whole-file map inside it. The container
            // keeps the measured triple and the overlay is peerless, so the
            // skeleton gate sees the same node as the offline build.
            if (attach != null && n.Identity.Cls == "TUiThumbnail")
            {
                var ov = attach(n);
                if (ov != null) return new ChromeContainer(n.Identity) { Content = ov };
            }
            return new ChromeElement(n.Identity);
        }

        /// <summary>Measured root area (engine mode only): 3 rows x 2 columns.
        /// Children are added in SPEC PREORDER so the UIA walk is unchanged;
        /// Grid.Row/Column only moves pixels (docs/19 §6.12 layout rule).</summary>
        static FrameworkElement BuildRootArea(SkelNode n, List<ChromeRow> tbs, List<ChromeRow> sbs,
            Func<SkelNode, FrameworkElement> attach, Action<ChromeElement, ChromeItem> decorate)
        {
            var grid = new System.Windows.Controls.Grid();
            grid.RowDefinitions.Add(new System.Windows.Controls.RowDefinition
            { Height = System.Windows.GridLength.Auto });                       // toolbar
            grid.RowDefinitions.Add(new System.Windows.Controls.RowDefinition
            { Height = new System.Windows.GridLength(1, System.Windows.GridUnitType.Star) });
            grid.RowDefinitions.Add(new System.Windows.Controls.RowDefinition
            { Height = System.Windows.GridLength.Auto });                       // status bar
            grid.ColumnDefinitions.Add(new System.Windows.Controls.ColumnDefinition
            { Width = System.Windows.GridLength.Auto });                        // overview strip
            grid.ColumnDefinitions.Add(new System.Windows.Controls.ColumnDefinition
            { Width = new System.Windows.GridLength(1, System.Windows.GridUnitType.Star) });
            for (int ci = 0; ci < n.Children.Count; ci++)
            {
                var child = BuildSkelNode(n.Children[ci], tbs, sbs, attach, decorate);
                string cls = n.Children[ci].Identity.Cls;
                if (cls == "TUiThumbnail")
                {
                    System.Windows.Controls.Grid.SetRow(child, 1);
                    System.Windows.Controls.Grid.SetColumn(child, 0);
                }
                else if (cls == "TUiDock")
                {
                    System.Windows.Controls.Grid.SetRow(child, 0);
                    System.Windows.Controls.Grid.SetColumnSpan(child, 2);
                }
                else if (n.Children[ci].Identity.Ct == "StatusBar")
                {
                    System.Windows.Controls.Grid.SetRow(child, 2);
                    System.Windows.Controls.Grid.SetColumnSpan(child, 2);
                }
                else
                {
                    System.Windows.Controls.Grid.SetRow(child, 1);
                    System.Windows.Controls.Grid.SetColumn(child, 1);
                }
                grid.Children.Add(child);
            }
            return new ChromeContainer(n.Identity) { Content = grid };
        }

        /// <summary>Folder Compare root (docs/19 §6.20): the skeleton order is
        /// [TUiDock, TUiStatusBar, TLogFrame, TUiPanel(tree)] but the measured
        /// spatial model is toolbar top, TREE middle (star), LOG bottom
        /// (auto), status bar bottom — the log frame renders BELOW the tree
        /// while sitting BEFORE it in the UIA preorder (same tree-order≠visual
        /// rule as the mirrored panes). Children are added in spec preorder;
        /// Grid.Row only moves pixels.</summary>
        static FrameworkElement BuildFolderRootArea(SkelNode n, List<ChromeRow> tbs, List<ChromeRow> sbs,
            Func<SkelNode, FrameworkElement> attach, Action<ChromeElement, ChromeItem> decorate)
        {
            var grid = new System.Windows.Controls.Grid();
            grid.RowDefinitions.Add(new System.Windows.Controls.RowDefinition
            { Height = System.Windows.GridLength.Auto });                       // toolbar
            grid.RowDefinitions.Add(new System.Windows.Controls.RowDefinition
            { Height = new System.Windows.GridLength(1, System.Windows.GridUnitType.Star) });
            grid.RowDefinitions.Add(new System.Windows.Controls.RowDefinition
            { Height = System.Windows.GridLength.Auto });                       // log frame
            grid.RowDefinitions.Add(new System.Windows.Controls.RowDefinition
            { Height = System.Windows.GridLength.Auto });                       // status bar
            for (int ci = 0; ci < n.Children.Count; ci++)
            {
                var child = BuildSkelNode(n.Children[ci], tbs, sbs, attach, decorate);
                string cls = n.Children[ci].Identity.Cls;
                if (cls == "TUiDock")
                    System.Windows.Controls.Grid.SetRow(child, 0);
                else if (cls == "TLogFrame")
                    System.Windows.Controls.Grid.SetRow(child, 2);
                else if (n.Children[ci].Identity.Ct == "StatusBar")
                    System.Windows.Controls.Grid.SetRow(child, 3);
                else
                    System.Windows.Controls.Grid.SetRow(child, 1);
                grid.Children.Add(child);
            }
            return new ChromeContainer(n.Identity) { Content = grid };
        }

        public static bool SubtreeHas(SkelNode n, string cls)
        {
            if (n.Identity.Cls == cls) return true;
            foreach (var c in n.Children)
                if (SubtreeHas(c, cls)) return true;
            return false;
        }

        /// <summary>Serialize a skeleton subtree into ledger triples (ct,cls,name),
        /// pre-order, with row counts folded in via the chrome ledgers.</summary>
        public static void SkelLedger(SkelNode n, List<Dictionary<string, object>> outRows)
        {
            outRows.Add(new Dictionary<string, object>
            {
                ["ct"] = n.Identity.Ct, ["cls"] = n.Identity.Cls, ["name"] = n.Identity.Name,
                ["row"] = n.Row == null ? null : string.Join(":", n.Row),
            });
            foreach (var c in n.Children) SkelLedger(c, outRows);
        }
    }

    /// <summary>Leaf element whose UIA identity is exactly the captured triple.
    /// Same peer lessons as BcMenuItem: IsControlElementCore must be true or the
    /// whole element disappears from the control view; ControlType/Class/Name come
    /// from the data, not from the CLR type. When Selected/clicked are set (engine-
    /// wired filter bar), the element paints its MEASURED selection tint
    /// (filter-map.json: sel (194,220,245) / unsel (240,240,240)) and fires the
    /// click; selection state is deliberately NOT exposed via UIA (measured: BC's
    /// buttons expose no Toggle/legacy pressed state — pixel-only).</summary>
    internal sealed class ChromeElement : Control
    {
        private readonly ChromeItem _it;
        private readonly bool _toolbarFace;
        private bool _hover, _pressed;
        public Func<bool> Selected;
        public Action Clicked;
        public Color SelectedColor = Color.FromRgb(194, 220, 245);
        public Color UnselectedColor = Color.FromRgb(240, 240, 240);

        // ---- toolbar text-button face (docs/21 B tier-1) ----
        // Geometry WITH provenance: button height 39 and margins top 2 / bottom
        // 3 (row totals 44 = the measured text-view TUiDock; buttons 39 tall at
        // y=86 inside toolbar y=84 — textlayout-en/tree-step0.json rects).
        // Presentation self-design (annotated docs/19 §6.21): we draw TEXT,
        // not icons (own icon set = follow-on; BC's toolbar face is icon-only,
        // so no measured text face exists), width = glyph run + 16px padding,
        // 3px corner radius, Segoe UI 13, hover/pressed/divider greys from the
        // Fluent family. Unnamed buttons and statusbar cells stay shells.
        // Current is the --theme overlay (light keeps the defaults below —
        // light.json sets nothing by the additive-overlay rule).
        public static Theme Current;
        // TEST-INJECTION ONLY (uia-toolbar-check negative): the face draws
        // nothing while sizes/layout stay identical — simulating the fault
        // "buttons render empty" so the gate's ink assertion is proven to have
        // teeth. Never set in product use.
        internal static readonly bool NegRender =
            Environment.GetEnvironmentVariable("REACMP_TB_NEG") == "1";
        static readonly Typeface Face = new Typeface("Segoe UI");
        const double FontSize = 13, PadX = 16, Radius = 3;
        static readonly Color LightText = Color.FromRgb(32, 31, 30);
        static readonly Color LightHover = Color.FromRgb(245, 245, 245);
        static readonly Color LightPressed = Color.FromRgb(231, 231, 231);
        static readonly Color LightDivider = Color.FromRgb(217, 217, 217);
        static FormattedText Label(string s) => new FormattedText(s,
            System.Globalization.CultureInfo.CurrentCulture,
            FlowDirection.LeftToRight, Face, FontSize, null, 1.0);

        public ChromeElement(ChromeItem it, bool toolbarFace = false)
        {
            _it = it;
            _toolbarFace = toolbarFace;
            Focusable = false;
            MinWidth = 2; MinHeight = 2;
            Width = it.Ct == "Separator" ? 8 : double.NaN;
            ToolTip = it.Name.Length > 0 ? it.Name : null;
            if (_toolbarFace && it.Ct == "Separator")
            {
                // docs/21 B: 1px group divider (self-design; BC measured 6px
                // wide separators we do not copy)
                Width = 1;
                Height = 39;
                Margin = new Thickness(0, 2, 0, 3);
            }
            else if (_toolbarFace && it.Name.Length > 0 &&
                     (it.Ct == "Button" || it.Ct == "MenuItem"))
            {
                Height = 39;
                Margin = new Thickness(0, 2, 0, 3);
                Width = Math.Ceiling(Label(it.Name).Width) + PadX;
            }
        }
        protected override void OnMouseEnter(System.Windows.Input.MouseEventArgs e)
        {
            base.OnMouseEnter(e);
            if (_toolbarFace) { _hover = true; InvalidateVisual(); }
        }
        protected override void OnMouseLeave(System.Windows.Input.MouseEventArgs e)
        {
            base.OnMouseLeave(e);
            if (_toolbarFace) { _hover = false; _pressed = false; InvalidateVisual(); }
        }
        protected override void OnMouseLeftButtonDown(System.Windows.Input.MouseButtonEventArgs e)
        {
            base.OnMouseLeftButtonDown(e);
            if (_toolbarFace)
            {
                // press visual for every named button — commands stay tier 2
                // (docs/21 B: buttons without implemented commands honestly
                // bounce; a button existing is not a command existing)
                _pressed = true; CaptureMouse(); InvalidateVisual();
            }
            if (Clicked != null) { Clicked(); e.Handled = true; }
        }
        protected override void OnMouseLeftButtonUp(System.Windows.Input.MouseButtonEventArgs e)
        {
            base.OnMouseLeftButtonUp(e);
            if (_toolbarFace && _pressed) { _pressed = false; InvalidateVisual(); }
            if (IsMouseCaptured) ReleaseMouseCapture();
        }
        protected override void OnRender(System.Windows.Media.DrawingContext dc)
        {
            if (_toolbarFace)
            {
                if (!NegRender)
                {
                    var rect = new Rect(0, 0, ActualWidth, ActualHeight);
                    var theme = Current;
                    if (Selected != null)
                    {
                        // measured radio strip (filter-map.json): full-rect
                        // tint, kept pixel-identical; the label rides on top.
                        dc.DrawRectangle(new SolidColorBrush(Selected() ? SelectedColor : UnselectedColor),
                            null, rect);
                    }
                    else if (_it.Ct == "Separator")
                    {
                        dc.DrawRectangle(new SolidColorBrush(theme?.ToolbarDivider ?? LightDivider),
                            null, new Rect((ActualWidth - 1) / 2, 0, 1, ActualHeight));
                    }
                    else if (_it.Name.Length > 0)
                    {
                        Brush bg = _pressed ? new SolidColorBrush(theme?.ToolbarPressed ?? LightPressed)
                                 : _hover ? new SolidColorBrush(theme?.ToolbarHover ?? LightHover)
                                 : null;
                        if (bg != null)
                            dc.DrawRoundedRectangle(bg, null, rect, Radius, Radius);
                    }
                    if (_it.Name.Length > 0)
                    {
                        var ft = Label(_it.Name);
                        ft.SetForegroundBrush(new SolidColorBrush(theme?.ToolbarText ?? LightText));
                        dc.DrawText(ft, new Point((ActualWidth - ft.Width) / 2,
                                                  (ActualHeight - ft.Height) / 2));
                    }
                }
                base.OnRender(dc);
                return;
            }
            if (Selected != null)
                dc.DrawRectangle(new SolidColorBrush(Selected() ? SelectedColor : UnselectedColor),
                    null, new Rect(0, 0, ActualWidth, ActualHeight));
            base.OnRender(dc);
        }
        protected override AutomationPeer OnCreateAutomationPeer()
        {
            var p = new ChromePeer(this, _it);
            Peer = p;   // remembered so state changes can raise UIA events
            return p;
        }
        public ChromePeer Peer;   // engine-wired footer refresh hook
    }

    /// <summary>Container whose UIA identity is also exactly the captured triple
    /// (content-view Panes/toolbars/statusbars). Children stay visible.</summary>
    internal sealed class ChromeContainer : ContentControl
    {
        private readonly ChromeItem _it;
        public ChromeContainer(ChromeItem it) { _it = it; Focusable = false; }
        protected override AutomationPeer OnCreateAutomationPeer() => new ChromePeer(this, _it);
    }

    internal sealed class ChromePeer : FrameworkElementAutomationPeer
    {
        private readonly ChromeItem _it;
        public ChromePeer(FrameworkElement o, ChromeItem it) : base(o) { _it = it; }
        protected override bool IsControlElementCore() => true;
        protected override string GetClassNameCore() => _it.Cls;
        // engine-wired cells (footer N:C) report their LIVE name; static cells
        // keep the measured captured name (410-chrome gate expectation).
        protected override string GetNameCore() => _it.LiveName?.Invoke() ?? _it.Name;
        protected override AutomationControlType GetAutomationControlTypeCore() => ChromeCt.Map(_it.Ct);
        /// <summary>Raise the UIA Name-changed event so assistive tech sees a
        /// cursor move (docs/19 §6.12: footer follows the shared cursor).</summary>
        public void RaiseNameChanged() =>
            RaisePropertyChangedEvent(System.Windows.Automation.AutomationElementIdentifiers.NameProperty,
                "", GetNameCore());
    }
}
