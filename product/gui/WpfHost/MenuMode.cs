// --menu-spec mode: build a data-driven menu bar and optionally dump the ledger
// (menu, label, shortcut) that the UIA self-check compares against the Oracle
// presence/menu matrices.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;

namespace ReaCompare.Gui
{
    internal static class MenuMode
    {
        public static int Run(string specPath, string view, string ledgerPath, bool show,
                              string dLeft = null, string dRight = null,
                              string enginePath = null, string colorsPath = null,
                              string displayOpt = null, string themeArg = null)
        {
            if (specPath == null || !File.Exists(specPath) ||
                (view == null && !(dLeft != null && dRight != null)))
            {
                Console.Error.WriteLine("usage: reacmp-gui --menu-spec spec.json (--view NAME | --dispatch L R) [--dump ledger.json] [--show]");
                return 2;
            }
            using var doc = JsonDocument.Parse(File.ReadAllText(specPath));
            var r = doc.RootElement;
            // --dispatch resolves the view from the measured cell table, exactly
            // like BC opening a file pair (U-gui-5): task-only views reject,
            // unknown extensions fall back (measured: .zqq -> Text Compare).
            // the LIVE session pair (mutable for Session Settings OK, docs/21 C
            // / docs/19 §6.22 measured: apply in place, title follows the pair
            // in the text view). Every engine channel reads THIS, never the
            // raw argv, so one re-point + re-run replaces the session.
            // dispTab/opt0/sessionSlot are the supporting mutable state the
            // live pair needs for re-runs and the title template.
            string sessLeft = null, sessRight = null;
            string opt0 = "";
            DispatchTable dispTab = null;
            var sessionSlot = new Action<Window>[1];
            string dispatchVia = null;
            if (dLeft != null)
            {
                var dt = DispatchTable.Load(r.GetProperty("dispatch"));
                var (dv, via) = dt.Dispatch(dLeft, dRight);
                if (dt.TaskOnly.Contains(dv, StringComparer.Ordinal))
                {
                    Console.Error.WriteLine($"DISPATCH-REJECT: {dv} is task-only (measured: no file route)");
                    return 3;
                }
                view = dv;
                dispatchVia = via;
                dispTab = dt;
                sessLeft = Path.GetFullPath(dLeft); sessRight = Path.GetFullPath(dRight);
                Console.WriteLine($"DISPATCH: {dLeft} {dRight} -> {dv} ({via})");
                Console.WriteLine("DISPATCH-TITLE: " + dt.Title(dLeft, dRight, dv));
            }
            var spec = new MenuSpec { View = view };
            // Top menus and mounted ACTIONS forms are per-view (measured: the four
            // top-menu variants differ by view, e.g. Folder family swaps File->Actions).
            foreach (var t in r.GetProperty("top_menus_per_view").GetProperty(view).EnumerateArray())
                spec.TopMenus.Add(t.GetString());
            foreach (var a in r.GetProperty("actions").EnumerateArray())
            {
                spec.Actions.Add(new MenuAction
                {
                    Key = a.TryGetProperty("key", out var n) ? n.GetString() : "",
                    Caption = a.TryGetProperty("caption", out var c) ? c.GetString() : "",
                    Shortcut = a.TryGetProperty("shortcut", out var s) ? s.GetString() : "",
                    Category = a.TryGetProperty("category", out var k) ? k.GetString() : "",
                    Hint = a.TryGetProperty("hint", out var h) ? h.GetString() : "",
                    Form = a.TryGetProperty("form", out var f) ? f.GetString() : "",
                });
            }
            if (r.TryGetProperty("view_forms", out var vf)
                && vf.TryGetProperty(view, out var vfv))
                foreach (var f in vfv.EnumerateArray()) spec.ViewForms.Add(f.GetString());
            if (r.TryGetProperty("top_access", out var ta))
                foreach (var viewKv in ta.EnumerateObject())
                {
                    var d = new Dictionary<string, string>();
                    foreach (var mk in viewKv.Value.EnumerateObject()) d[mk.Name] = mk.Value.GetString() ?? "";
                    spec.TopAccess[viewKv.Name] = d;
                }
            if (r.TryGetProperty("item_order", out var io))
                foreach (var kv in io.EnumerateObject())
                {
                    var list = new List<string>();
                    foreach (var x in kv.Value.EnumerateArray()) list.Add(x.GetString());
                    spec.ItemOrder[kv.Name] = list;
                }
            foreach (var p in r.GetProperty("presence").EnumerateArray())
            {
                var list = new List<string>();
                foreach (var x in p.GetProperty("present_in").EnumerateArray()) list.Add(x.GetString());
                spec.Presence.Add(new PresenceRow
                {
                    Menu = p.GetProperty("menu").GetString(),
                    Item = p.GetProperty("item").GetString(),
                    PresentIn = list,
                });
            }
            if (r.TryGetProperty("enabled", out var en))
                foreach (var x in en.EnumerateArray())
                {
                    var e = new EnabledRow
                    {
                        Menu = x.GetProperty("menu").GetString(),
                        Label = x.GetProperty("label").GetString(),
                        Cls = x.GetProperty("cls").GetString(),
                    };
                    foreach (var v in x.GetProperty("enabled_in").EnumerateArray()) e.EnabledIn.Add(v.GetString());
                    if (x.TryGetProperty("disabled_in", out var di))
                        foreach (var v in di.EnumerateArray()) e.DisabledIn.Add(v.GetString());
                    spec.Enabled.Add(e);
                }
            if (r.TryGetProperty("chrome", out var ch)
                && ch.TryGetProperty(view, out var cv))
            {
                if (cv.TryGetProperty("toolbars", out var tbs))
                    LoadChromeRows(spec.Toolbars, "tb", tbs);
                if (cv.TryGetProperty("statusbars", out var sbs))
                    LoadChromeRows(spec.Statusbars, "sb", sbs);
            }
            if (r.TryGetProperty("skeleton", out var sk)
                && sk.TryGetProperty(view, out var skv))
                foreach (var node in skv.EnumerateArray())
                    spec.Skeleton.Add(LoadSkelNode(node));

            // sessionSlot is only wired for dispatched sessions (the live
            // engine views own a Session Settings apply); the offline ledger
            // path (gui-self-check / menu-offline) never passes it — its menu
            // items have NO Click handler at all (UIA tree unchanged).
            var (menu, ledger) = MenuBuilder.Build(spec, dLeft != null ? sessionSlot : null);
            ChromeBuilder.BuildRows(spec.Toolbars, out var tbLedger);
            ChromeBuilder.BuildRows(spec.Statusbars, out var sbLedger);
            var skelLedger = new List<Dictionary<string, object>>();
            foreach (var s in spec.Skeleton) ChromeBuilder.SkelLedger(s, skelLedger);

            // Theme (docs/20 D5): --theme NAME|path loads an ADDITIVE overlay
            // from themes/<name>.json. light is the no-op default (no theme
            // loaded, every color stays at its measured source); unknown names
            // fail closed at exit 4 like the engine boundary — never silently
            // fall back, silently rendering the wrong palette is a fidelity bug.
            Theme theme = null;
            if (themeArg != null)
            {
                try { theme = Theme.Load(themeArg); }
                catch (Exception e) { Console.Error.WriteLine("THEME-FAIL: " + e.Message); return 4; }
                Console.WriteLine($"THEME: {theme.Name}");
                // toolbar text-button face reads the theme overlay (dark.json
                // "toolbar" key); light keeps the ChromeElement defaults
                ChromeElement.Current = theme;
            }

            // ---- engine wiring (dispatch + Text Compare only, first cut) ----
            // The Rust CLI already has the byte-exact text-report XML contract
            // (exit 0 or a typed failure code); the GUI never invents results.
            // Content colors/geometry come ONLY from the measured colors.json.
            DiffResult diff = null;
            PaneStyle style = null;
            ReacmpEngine engine = null;
            FilterMap fmap = null;
            if (dLeft != null && view == "Text Compare")
            {
                string colors = colorsPath ?? DefaultColorsPath();
                if (!File.Exists(colors))
                { Console.Error.WriteLine($"ENGINE: colors.json not found: {colors}"); return 4; }
                try
                {
                    style = PaneStyle.Load(colors);
                    string marks = DefaultFindMarksPath();
                    if (!File.Exists(marks))
                    { Console.Error.WriteLine($"ENGINE: findmarks.json not found: {marks}"); return 4; }
                    style.LoadFindMarks(marks);
                    theme?.Apply(style);
                    engine = new ReacmpEngine(enginePath ?? ReacmpEngine.DefaultExe());
                    // --display NAME selects the initial filter (measured radio
                    // trio All/Diffs/Same; unknown names are the engine's error,
                    // never the GUI's invention — Compare() fails closed as 4).
                    if (displayOpt != null)
                    {
                        var fm0 = File.Exists(DefaultFilterMapPath()) ? FilterMap.Load(DefaultFilterMapPath()) : null;
                        if (fm0 == null || !fm0.ButtonToOption.TryGetValue(displayOpt, out opt0))
                        { Console.Error.WriteLine($"FILTER: unknown display button '{displayOpt}'"); return 4; }
                    }
                    diff = engine.Compare(sessLeft, sessRight, opt0);
                    Console.WriteLine($"ENGINE: {diff.Rows.Count} rows from {engine.ExePath}");
                }
                catch (Exception e)
                {
                    Console.Error.WriteLine("ENGINE-FAIL: " + e.Message);
                    return 4;
                }
                var fmPath = DefaultFilterMapPath();
                if (File.Exists(fmPath)) { fmap = FilterMap.Load(fmPath); theme?.Apply(fmap); }
                else Console.Error.WriteLine($"FILTER: map not found at {fmPath} (buttons inert)");
            }

            // ---- hex engine wiring (dispatch + Hex Compare) ----
            // `--hex3` data channel (LiuCompare-native verb, help-marked):
            // the GUI renders the FLAT slot stream; it never re-classifies.
            HexModel hexModel = null;
            HexViewState hexState = null;
            Func<string, string, HexModel> runHex3 = (hl, hr) =>
            {
                string hexExe = enginePath ?? ReacmpEngine.DefaultExe();
                if (hexExe == null || !File.Exists(hexExe))
                    throw new InvalidOperationException("reacmp.exe not found (set --engine or REACMP)");
                string jsonOut = Path.Combine(Path.GetTempPath(), $"reacmp-hex-{Guid.NewGuid():N}.json");
                var psi = new System.Diagnostics.ProcessStartInfo(hexExe,
                    $"--hex3 \"{hl}\" \"{hr}\" \"{jsonOut}\"")
                { UseShellExecute = false, RedirectStandardError = true, CreateNoWindow = true };
                int code; string err;
                using (var p = System.Diagnostics.Process.Start(psi))
                {
                    err = p.StandardError.ReadToEnd();
                    p.WaitForExit();
                    code = p.ExitCode;
                }
                try
                {
                    if (code != 0 || !File.Exists(jsonOut))
                        throw new InvalidOperationException($"reacmp --hex3 exit {code}: {(err ?? "").Trim()}");
                    return HexModel.Load(jsonOut);
                }
                finally { try { File.Delete(jsonOut); } catch { } }
            };
            if (dLeft != null && view == "Hex Compare")
            {
                string colors = colorsPath ?? DefaultColorsPath();
                if (!File.Exists(colors))
                { Console.Error.WriteLine($"ENGINE: colors.json not found: {colors}"); return 4; }
                try
                {
                    style = PaneStyle.Load(colors);
                    theme?.Apply(style);
                    hexModel = runHex3(sessLeft, sessRight);
                    hexState = new HexViewState(hexModel);
                    Console.WriteLine($"ENGINE: {hexModel.Slots.Count} hex slots " +
                        $"(same={hexModel.Same} l-orphan={hexModel.LeftOrphan} " +
                        $"r-orphan={hexModel.RightOrphan} diff={hexModel.Difference})");
                }
                catch (Exception e)
                {
                    Console.Error.WriteLine("ENGINE-FAIL: " + e.Message);
                    return 4;
                }
            }

            // ---- folder engine wiring (dispatch + Folder Compare) ----
            // `--dir3` data channel (LiuCompare-native verb, help-marked):
            // the view renders the engine's visible rows; it never re-sorts
            // or re-classifies.
            FolderModel folderModel = null;
            FolderViewState folderState = null;
            Func<string, string, FolderModel> runDir3 = (dl, dr) =>
            {
                string dirExe = enginePath ?? ReacmpEngine.DefaultExe();
                if (dirExe == null || !File.Exists(dirExe))
                    throw new InvalidOperationException("reacmp.exe not found (set --engine or REACMP)");
                string jsonOut = Path.Combine(Path.GetTempPath(), $"reacmp-dir-{Guid.NewGuid():N}.json");
                var psi = new System.Diagnostics.ProcessStartInfo(dirExe,
                    $"--dir3 \"{dl}\" \"{dr}\" \"{jsonOut}\"")
                { UseShellExecute = false, RedirectStandardError = true, CreateNoWindow = true };
                int code; string err;
                using (var p = System.Diagnostics.Process.Start(psi))
                {
                    err = p.StandardError.ReadToEnd();
                    p.WaitForExit();
                    code = p.ExitCode;
                }
                try
                {
                    if (code != 0 || !File.Exists(jsonOut))
                        throw new InvalidOperationException($"reacmp --dir3 exit {code}: {(err ?? "").Trim()}");
                    return FolderModel.Load(jsonOut);
                }
                finally { try { File.Delete(jsonOut); } catch { } }
            };
            if (dLeft != null && view == "Folder Compare")
            {
                string colors = colorsPath ?? DefaultColorsPath();
                if (!File.Exists(colors))
                { Console.Error.WriteLine($"ENGINE: colors.json not found: {colors}"); return 4; }
                try
                {
                    style = PaneStyle.Load(colors);
                    theme?.Apply(style);
                    folderModel = runDir3(sessLeft, sessRight);
                    folderState = new FolderViewState(folderModel);
                    Console.WriteLine($"ENGINE: {folderState.Rows.Count} folder rows");
                }
                catch (Exception e)
                {
                    Console.Error.WriteLine("ENGINE-FAIL: " + e.Message);
                    return 4;
                }
            }

            if (ledgerPath != null)
            {
                var opts = new JsonSerializerOptions { WriteIndented = true };
                var rows = ledger.ConvertAll(l => new Dictionary<string, object>
                {
                    ["menu"] = l.menu, ["label"] = l.label, ["shortcut"] = l.shortcut ?? "",
                    ["enabled"] = l.enabled,
                    // D1 (docs/20): what the user SEES — Oracle labels stay for
                    // matrix replay, the display axis proves the brand swap is
                    // single-point (MenuBuilder.ApplyBrand) and complete.
                    ["display"] = MenuBuilder.ApplyBrand(l.label),
                });
                var bundle = new Dictionary<string, object>
                {
                    ["view"] = view, ["items"] = rows,
                    ["toolbars"] = tbLedger, ["statusbars"] = sbLedger,
                    ["skeleton"] = skelLedger,
                };
                if (diff != null)
                    bundle["content"] = new Dictionary<string, object>
                    {
                        ["left"] = diff.LeftPath, ["right"] = diff.RightPath,
                        ["mode"] = diff.Mode, ["display_button"] = displayOpt ?? "All",
                        // audit face: which palette the live pixels must match
                        ["theme"] = theme?.Name ?? "light",
                        ["rows"] = diff.Rows.ConvertAll(d => new Dictionary<string, object>
                        {
                            ["status"] = d.Status,
                            ["ltext"] = d.LText, ["rtext"] = d.RText,
                            ["ltid"] = d.LId, ["rtid"] = d.RId,
                        }),
                    };
                File.WriteAllText(ledgerPath, JsonSerializer.Serialize(bundle, opts));
                Console.WriteLine($"menu ledger -> {ledgerPath} (items={rows.Count}, tops={spec.TopMenus.Count}, " +
                    $"chrome-rows={tbLedger.Count + sbLedger.Count}, skeleton={skelLedger.Count}" +
                    (diff != null ? $", content-rows={diff.Rows.Count}" : "") + ")");
            }
            if (show)
            {
                var body = new DockPanel { LastChildFill = true };
                // Menu docks top (measured: BC keeps the menu bar inside
                // TUiMainDock at window level); the content-view skeleton owns
                // everything below — its embedded ToolBar/StatusBar nodes render
                // their chrome rows, so no separate row docking (that would
                // duplicate AutomationIds).
                DockPanel.SetDock(menu, Dock.Top);
                body.Children.Add(menu);
                // DOCKPANEL, not a vertical StackPanel: a StackPanel measures
                // its children with INFINITE height, so the chrome root's Grid
                // star rows degrade to content height — the engine panes'
                // desired height (rows × pitch, TextPaneView.MeasureOverride)
                // then stretches the whole view past the window and the
                // overview strip's slot detaches from its 729px paint (caught
                // live by uia-overview-check: a strip click landed on the
                // wrong row). DockPanel gives the LAST child the remaining
                // bounded space; earlier children (find bar, extra roots)
                // dock top. UIA preorder = child add order, unchanged.
                var content = new DockPanel { LastChildFill = true };                // Engine-wired Text Compare: attach the owner-draw diff pane to
                // each TTextEditor skeleton slot. BC's tree order is RIGHT-first
                // (gui-text-session-en.json rects: editor#0 x=784, editor#1 x=86),
                // so slot index parity picks the side — the measured order is
                // preserved rather than a guessed left-first layout.
                // The measured radio trio All/Diffs/Same (filter-map.json)
                // repaints with the tint on click and re-queries the FILTERING
                // three-path channel with the mapped option — the GUI never
                // reimplements the filter predicate. BC's initial selection is
                // All (step0-initial: All=SEL).
                Func<SkelNode, FrameworkElement> attach = null;
                Action<ChromeElement, ChromeItem> decorate = null;
                // shared engine-view objects (hoisted to show-scope so the
                // find-bar block below the skeleton loop can drive them too)
                // Session Settings apply holder + window holder: each engine
                // view below installs its own in-place re-run closure (capturing
                // its local state objects); the menu slot fires after the
                // window exists. Holders avoid disturbing the existing
                // per-block variable scoping (the closures capture block locals).
                var applyHolder = new Action<string, string>[1];
                var winHolder = new Window[1];
                var panes = new List<TextPaneView>();
                var bands = new List<DetailsBandView>();
                var overviews = new List<OverviewStripView>();
                var state = new DiffResult[] { diff };
                var viewState = new DiffViewState();
                if (diff != null)
                {
                    int slot = 0;
                    string selectedButton = displayOpt ?? "All";
                    var radioEls = new List<ChromeElement>();
                    // footer chrome cells: sb1 = RIGHT pane (measured x=785),
                    // sb2 = LEFT (x=87) — textlayout-en: the click moved BOTH
                    // footers in lockstep (shared cursor), format 'N: C'.
                    // REACMP_INTERACT_NEG=1 is a TEST-INJECTION ONLY: the right
                    // footer keeps its static initial name — simulating the
                    // wiring fault "right pane not bound to the shared state"
                    // so the interaction gate's sync assertion is proven to
                    // have teeth (it must go red). Never set in product use.
                    bool negInjection =
                        Environment.GetEnvironmentVariable("REACMP_INTERACT_NEG") == "1";
                    void TagFooter(ChromeRow r, bool isRight)
                    {
                        if (r.Items.Count == 0 || r.Items[0].Ct != "Text") return;
                        var it = r.Items[0];
                        it.LiveName = () =>
                        {
                            if (isRight && negInjection) return it.Name; // stale by injection
                            var d = state[0];
                            if (d == null || d.Rows.Count == 0) return it.Name;
                            int k = viewState.SelectedRow >= 0 ? viewState.SelectedRow : 0;
                            int? id = isRight ? d.Rows[k].RId : d.Rows[k].LId;
                            return $"{id}: {viewState.Column}";
                        };
                    }
                    if (spec.Statusbars.Count > 1) TagFooter(spec.Statusbars[1], true);
                    if (spec.Statusbars.Count > 2) TagFooter(spec.Statusbars[2], false);
                    // MEASURED initial cursor (docs/19 §6.13): a fresh BC
                    // compare shows footer '3: 1' = the FIRST DIFFERENT row
                    // (textlayout-en step0 AND textfind-en step0 both read
                    // 3:1; 149-line corpus read 40:1 = its first different).
                    // NOT row 1, NOT first non-same (similar rows do not
                    // count). Falls back: first non-same, then row 0.
                    {
                        int first = diff.Rows.FindIndex(r => r.Status == "different");
                        if (first < 0) first = diff.Rows.FindIndex(r => r.Status != "same");
                        if (first < 0) first = 0;
                        viewState.SelectedRow = first;
                        viewState.Column = 1;
                    }
                    attach = n =>
                    {
                        if (n.Identity.Cls == "TUiThumbnail")
                        {
                            // measured TUiThumbnail slot (docs/19 §6.12B): left
                            // 52px full-height column. Capability inherited from
                            // BC (whole-file map + viewport + jump); presentation
                            // self-designed (docs/20 §3).
                            var ov = new OverviewStripView
                            { Diff = state[0], View = viewState, Colors = style };
                            overviews.Add(ov);
                            return ov;
                        }
                        if (n.Identity.Cls == "TTextDetailsEditor")
                        {
                            // measured tree order: band WITH a scrollbar (h32)
                            // comes first, thin band (h15) second
                            var band = new DetailsBandView
                            {
                                Diff = state[0], View = viewState, Colors = style,
                                IsTallBand = bands.Count == 0,
                            };
                            bands.Add(band);
                            return band;
                        }
                        if (n.Identity.Cls != "TTextEditor") return null;
                        var pane = new TextPaneView
                        {
                            Diff = state[0],
                            // measured tree order: 0th TTextEditor = screen-right
                            IsLeft = (slot++ % 2) == 1,
                            Colors = style,
                            View = viewState,
                        };
                        panes.Add(pane);
                        return pane;
                    };
                    // shared state -> repaint + UIA name events everywhere
                    var footerEls = new List<ChromeElement>();
                    viewState.Changed += () =>
                    {
                        foreach (var p in panes) p.InvalidateVisual();
                        foreach (var b in bands) b.InvalidateVisual();
                        foreach (var o in overviews) o.InvalidateVisual();
                        foreach (var f in footerEls) f.Peer?.RaiseNameChanged();
                    };
                    // decorate runs for EVERY chrome element: footer cells
                    // (LiveName != null) register for UIA name refresh; the
                    // measured radio trio additionally wires selection tint +
                    // click-to-refilter (the engine's FILTERING three-path
                    // channel — the GUI never reimplements the predicate).
                    decorate = (el, it) =>
                    {
                        if (it.LiveName != null) { footerEls.Add(el); return; }
                        if (fmap == null || !fmap.RadioGroup.Contains(it.Name)) return;
                        // measured UIA button rect size 59x39 (probe4,
                        // filter-map.json button_size_px) — the strip-check
                        // needs the product's buttons to be the same size
                        // BC's toolbar buttons are.
                        el.Width = fmap.ButtonWidth; el.Height = fmap.ButtonHeight;
                        el.SelectedColor = fmap.Selected;
                        el.UnselectedColor = fmap.Unselected;
                        radioEls.Add(el);
                        el.Selected = () => it.Name == selectedButton;
                        el.Clicked = () =>
                        {
                            if (it.Name == selectedButton) return;
                            DiffResult nd;
                            try
                            {
                                nd = engine.Compare(sessLeft, sessRight, fmap.ButtonToOption[it.Name]);
                            }
                            catch (Exception e)
                            {
                                Console.Error.WriteLine("ENGINE-FAIL: " + e.Message);
                                return; // keep current view; never fake a result
                            }
                            state[0] = nd;
                            selectedButton = it.Name;
                            // refilter changes the ROW SET: the shared cursor
                            // resets (rows renumber); panes/bands re-read
                            // state[0] through Diff = nd.
                            foreach (var p in panes) { p.Diff = nd; p.InvalidateVisual(); }
                            foreach (var b in bands) { b.Diff = nd; b.InvalidateVisual(); }
                            foreach (var o in overviews) { o.Diff = nd; o.InvalidateVisual(); }
                            foreach (var f in footerEls) f.Peer?.RaiseNameChanged();
                            foreach (var r in radioEls) r.InvalidateVisual();
                        };
                    };
                    // Session Settings (text): re-point the pair, re-run the
                    // SAME engine channel with the CURRENT filter option, swap
                    // state IN PLACE (measured ring docs/19 §6.22: window
                    // survives, panes re-compare, and the TITLE follows the
                    // new pair in the text view). Fresh cursor rule = first
                    // different row (same measured initial rule as view open,
                    // §6.13). A find bar left OPEN is an unmeasured BC edge —
                    // documented, the bar recomputes on its next keystroke.
                    applyHolder[0] = (nl, nr) =>
                    {
                        sessLeft = nl; sessRight = nr;
                        DiffResult nd;
                        try { nd = engine.Compare(sessLeft, sessRight, opt0); }
                        catch (Exception e)
                        {
                            Console.Error.WriteLine("ENGINE-FAIL: " + e.Message);
                            return; // keep the old session; never fake results
                        }
                        state[0] = nd;
                        int first = nd.Rows.FindIndex(r => r.Status == "different");
                        if (first < 0) first = nd.Rows.FindIndex(r => r.Status != "same");
                        if (first < 0) first = 0;
                        viewState.SelectedRow = first;
                        viewState.Column = 1;
                        viewState.TopRow = 0;
                        foreach (var p in panes) { p.Diff = nd; p.InvalidateVisual(); }
                        foreach (var b in bands) { b.Diff = nd; b.InvalidateVisual(); }
                        foreach (var o in overviews) { o.Diff = nd; o.InvalidateVisual(); }
                        foreach (var f in footerEls) f.Peer?.RaiseNameChanged();
                        if (winHolder[0] != null)
                            winHolder[0].Title = dispTab?.Title(sessLeft, sessRight, view);
                    };
                }

                if (diff == null && hexState != null)
                {
                    // Hex Compare attach: tree-first THexEditor = screen-right
                    // (measured preorder pane3 [758,...] before pane5 [60,...],
                    // same mirror rule as the text view's editors).
                    int hslot = 0;
                    var hexPanes = new List<HexPaneView>();
                    attach = n =>
                    {
                        if (n.Identity.Cls != "THexEditor") return null;
                        var pane = new HexPaneView(hexState, (hslot++ % 2) == 1, style);
                        hexPanes.Add(pane);
                        return pane;
                    };
                    hexState.Changed += () =>
                    {
                        foreach (var p in hexPanes) p.InvalidateVisual();
                    };
                    // Session Settings (hex): re-point the pair, re-run --hex3
                    // IN PLACE, swap the model into the stable hexState the
                    // panes already hold (measured ring docs/19 §6.22).
                    applyHolder[0] = (nl, nr) =>
                    {
                        sessLeft = nl; sessRight = nr;
                        try { hexState.ApplyNewModel(runHex3(sessLeft, sessRight)); }
                        catch (Exception e)
                        {
                            Console.Error.WriteLine("ENGINE-FAIL: " + e.Message);
                            return;
                        }
                        foreach (var p in hexPanes) p.InvalidateVisual();
                        if (winHolder[0] != null)
                            winHolder[0].Title = dispTab?.Title(sessLeft, sessRight, view);
                    };
                }

                if (diff == null && hexState == null && folderState != null)
                {
                    var folderViews = new List<FolderListView>();
                    attach = n =>
                    {
                        if (n.Identity.Cls != "TDirTreeView") return null;
                        var view = new FolderListView(folderState, style);
                        folderViews.Add(view);
                        return view;
                    };
                    folderState.Changed += () =>
                    {
                        foreach (var v in folderViews) v.InvalidateVisual();
                    };
                    // Session Settings (folder): re-point the pair, re-run
                    // --dir3 IN PLACE, swap the model into the live folderState
                    // (the status-bar census closures Counts()/Free() read
                    // folderState + sessLeft/sessRight BY REFERENCE, so the
                    // numbers refresh; folderViews repaint; title recomputes —
                    // measured ring docs/19 §6.22).
                    applyHolder[0] = (nl, nr) =>
                    {
                        sessLeft = nl; sessRight = nr;
                        FolderModel fm;
                        try { fm = runDir3(sessLeft, sessRight); }
                        catch (Exception e)
                        {
                            Console.Error.WriteLine("ENGINE-FAIL: " + e.Message);
                            return;
                        }
                        folderState.ApplyNewModel(fm);
                        foreach (var v in folderViews) v.InvalidateVisual();
                        if (winHolder[0] != null)
                            winHolder[0].Title = dispTab?.Title(sessLeft, sessRight, view);
                    };
                }

                if (folderState != null && spec.Statusbars.Count > 0 &&
                    spec.Statusbars[0].Items.Count >= 8)
                {
                    // Status-bar census wiring (docs/21 A): items 1/3 = LEFT
                    // counts/free, 5/7 = RIGHT (measured position order). The
                    // static captured names stay on every path that does not
                    // dispatch an engine (12-golden offline runs unchanged).
                    // Free space = DriveInfo (biaoxian self-design; BC's
                    // '{N} GB free on {drive}' text shape kept).
                    // REACMP_FOLDER_SB_NEG=1 is a TEST-INJECTION ONLY: the
                    // census reports garbage so the gate's equality assertion
                    // is proven to have teeth. Never set in product use.
                    bool sbNeg =
                        Environment.GetEnvironmentVariable("REACMP_FOLDER_SB_NEG") == "1";
                    var sbRow = spec.Statusbars[0];
                    string Counts(bool left)
                    {
                        if (sbNeg) return "999 file(s), 999 bytes";
                        var (files, bytes) = folderState.SideTotals(left);
                        return $"{files} file(s), {bytes} bytes";
                    }
                    string Free(bool left)
                    {
                        try
                        {
                            string root = Path.GetPathRoot(
                                Path.GetFullPath(left ? sessLeft : sessRight)) ?? "C:\\";
                            var di = new System.IO.DriveInfo(root);
                            return $"{di.AvailableFreeSpace / (1L << 30)} GB free on {di.Name}";
                        }
                        catch
                        {
                            return "";
                        }
                    }
                    sbRow.Items[1].LiveName = () => Counts(true);
                    sbRow.Items[3].LiveName = () => Free(true);
                    sbRow.Items[5].LiveName = () => Counts(false);
                    sbRow.Items[7].LiveName = () => Free(false);
                }
                foreach (var s in spec.Skeleton)
                    content.Children.Add(ChromeBuilder.BuildSkelNode(s, spec.Toolbars, spec.Statusbars, attach, decorate));
                // ---- basic find bar (docs/19 §6.13 tier-1) ----
                // MEASURED shape: TTextFindFrame inserted at the top of the
                // pane area on Ctrl+F (frame h=37, full content width; combo
                // 655x25 + Prev 46x30 + Next 48x30; Esc removes the frame —
                // closed tree had frame-node count 0). Initially COLLAPSED, so
                // the structural gates (which never press Ctrl+F) see exactly
                // the measured closed-state tree. Controls carry BC-measured
                // UIA names 'Prev'/'Next' (find-open tree); the combo is a
                // WPF ComboBox (IsEditable) = BC's TUiComboBox counterpart.
                Window findBarWindow = null;
                Action<Window> wireFindKeys = null;
                if (diff != null)
                {
                    var bar = new StackPanel { Orientation = Orientation.Horizontal, Visibility = Visibility.Collapsed };
                    var combo = new ComboBox {
                        IsEditable = true,
                        Width = style?.FindComboWidth ?? 655,
                        Height = style?.FindComboHeight ?? 25,
                        Margin = new Thickness(4, 6, 0, 6),
                    };
                    // UIA name for automation (the live gate drives typing via
                    // this element instead of global keypost, which races the
                    // combo's Win32 focus). Bar is collapsed until Ctrl+F, so
                    // the 24-node closed skeleton gate is unaffected.
                    System.Windows.Automation.AutomationProperties.SetName(combo, "FindWhat");
                    var prevBtn = new Button { Content = "Prev", Width = style?.FindPrevWidth ?? 46, Height = style?.FindButtonHeight ?? 30, Margin = new Thickness(2, 4, 0, 4) };
                    var nextBtn = new Button { Content = "Next", Width = style?.FindNextWidth ?? 48, Height = style?.FindButtonHeight ?? 30, Margin = new Thickness(2, 4, 0, 4) };
                    System.Windows.Automation.AutomationProperties.SetName(prevBtn, "Prev");
                    System.Windows.Automation.AutomationProperties.SetName(nextBtn, "Next");
                    bar.Children.Add(combo); bar.Children.Add(prevBtn); bar.Children.Add(nextBtn);
                    var find = viewState.Find ?? (viewState.Find = new DiffViewState.FindState());
                    void ApplyMatch(DiffViewState.Match m, bool scroll)
                    {
                        if (m == null) return;
                        viewState.SelectedRow = m.Row;
                        viewState.Column = m.Start + m.Length + 1;  // cursor lands at match END: measured '3: 8' for 'TOTALLY'@7 (docs/19 §6.13)
                        if (scroll)
                        {
                            // keep the current match visible in the shared viewport
                            int visible = Math.Max(1, (int)(panes.Count > 0 ? panes[0].ActualHeight / Math.Max(1, style?.RowPitch ?? 15) : 40));
                            if (viewState.TopRow > m.Row) viewState.TopRow = m.Row;
                            else if (m.Row >= viewState.TopRow + visible) viewState.TopRow = m.Row - visible + 1;
                        }
                        viewState.Raise();
                    }
                    // editable-part text changes bubble as the routed
                    // TextBoxBase.TextChanged (ComboBox has no CLR event)
                    combo.AddHandler(System.Windows.Controls.Primitives.TextBoxBase.TextChangedEvent,
                        new System.Windows.Controls.TextChangedEventHandler((s, e) =>
                        {
                            // typing repaints marks WITHOUT moving the cursor
                            // (measured: footer unchanged while typing, §6.13)
                            find.Query = combo.Text ?? "";
                            find.Recompute(state[0]);
                            viewState.Raise();
                        }));
                    Action<int> step = d =>
                    {
                        // TEST-INJECTION ONLY (uia-text-find-check negative):
                        // Next/Prev repaint marks but fail to move the shared
                        // cursor — simulating the wiring fault so the gate's
                        // footer-step assertion is proven to have teeth.
                        if (Environment.GetEnvironmentVariable("REACMP_FIND_NEG") == "1")
                            return;
                        ApplyMatch(find.Step(d), scroll: true);
                    };
                    nextBtn.Click += (s, e) => step(+1);
                    prevBtn.Click += (s, e) => step(-1);
                    combo.KeyDown += (s, e) =>
                    {
                        if (e.Key == System.Windows.Input.Key.Enter) step(+1);
                        else if (e.Key == System.Windows.Input.Key.Escape) bar.Visibility = Visibility.Collapsed;
                    };
                    content.Children.Insert(0, bar);   // BC-measured: frame ABOVE the pane area (y=128)
                    wireFindKeys = w =>
                    {
                        // Ctrl+F opens the bar and focuses the combo: measured
                        // shortcut from the menu ledger (TFILEACTIONS.FindAction
                        // Ctrl+F, §6.13). Esc closes (measured closed-state:
                        // frame removed, cursor value KEPT — footer stayed 3:8).
                        w.PreviewKeyDown += (s, e) =>
                        {
                            if (e.Key == System.Windows.Input.Key.F &&
                                (System.Windows.Input.Keyboard.Modifiers & System.Windows.Input.ModifierKeys.Control) != 0)
                            {
                                bar.Visibility = Visibility.Visible;
                                combo.Focus();
                                e.Handled = true;
                            }
                            else if (e.Key == System.Windows.Input.Key.Escape &&
                                     bar.Visibility == Visibility.Visible)
                            {
                                bar.Visibility = Visibility.Collapsed;
                                e.Handled = true;
                            }
                        };
                    };
                }
                // DockPanel default dock is LEFT: every child except the
                // LAST must be docked top explicitly (find bar inserted at 0
                // included), or the layout collapses sideways.
                for (int ci = 0; ci < content.Children.Count - 1; ci++)
                    DockPanel.SetDock(content.Children[ci], Dock.Top);
                body.Children.Add(content);
                var win = new Window
                {
                    // When dispatched, the window title uses the MEASURED BC
                    // structure '{L} <--> {R} - {View} - <brand>' with our brand
                    // token (D1, docs/20) — DispatchTable.Load swaps the Oracle
                    // name to 'LiuCompare', so a live Win32 read cross-checks
                    // the structure verbatim. sessLeft/sessRight are the LIVE
                    // pair: Session Settings OK recomputes the title with the
                    // new values (measured text-view ring: title follows the
                    // pair — docs/19 §6.22).
                    Title = dLeft != null
                        ? dispTab.Title(sessLeft, sessRight, view)
                        : "menu-check: " + view,
                    // D2 (docs/20): default size follows BC — the measured
                    // session window rect is 1456x864 (gui-text-session-en.json
                    // TViewForm); remembering the last size comes with the
                    // session feature (P1).
                    Width = dLeft != null ? 1456 : 800,
                    Height = dLeft != null ? 864 : 480,
                    Content = body,
                };
                // Theme window base (dark.json window_bg): only the area the
                // skeleton panes don't cover; light (no key) keeps the default.
                if (theme?.WindowBg is System.Windows.Media.Color wbCol)
                    win.Background = new System.Windows.Media.SolidColorBrush(wbCol);
                winHolder[0] = win;
                // Session Settings (docs/21 C): the menu slot fires the Specs
                // dialog (2 fields — the dispatched views here are the two-sided
                // Text/Hex/Folder; the merge window has no menu bar in tier-1,
                // in案). Only wired when an engine view installed a handler
                // (applyHolder[0]); non-engine dispatched views leave the item
                // inert, never faking a session it did not build.
                // REACMP_SSET_NEG=1 is a TEST-INJECTION ONLY: the dialog still
                // opens and OK still closes it, but the re-run is NOT applied
                // — simulating the fault "OK not bound to the engine channel"
                // so the gate's title/rows assertions are proven to have
                // teeth. Never set in product use.
                sessionSlot[0] = owner =>
                {
                    if (applyHolder[0] == null) return;
                    var res = SessionSettingsDialog.Show(owner ?? win, view, sessLeft, sessRight);
                    if (res.Applied &&
                        Environment.GetEnvironmentVariable("REACMP_SSET_NEG") != "1")
                        applyHolder[0](res.Left, res.Right);
                };
                wireFindKeys?.Invoke(win);
                var app = new Application();
                win.Show();
                app.Run(win);
            }
            return 0;
        }

        static string DefaultFindMarksPath()
        {
            var env = Environment.GetEnvironmentVariable("REACMP_FINDMARKS");
            if (!string.IsNullOrEmpty(env)) return env;
            return Path.GetFullPath(Path.Combine(RepoRoot(),
                "extracted", "live", "textfind-en", "findmarks.json"));
        }

        /// <summary>Repo root = 6 levels above WpfHost/bin/Config/net8.0-windows.
        /// Single source for every default data path (colors.json, findmarks,
        /// merge-palette) so the merge view and the text view agree on it.</summary>
        public static string RepoRoot()
        {
            return Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,
                "..", "..", "..", "..", "..", ".."));
        }

        /// <summary>Public wrapper so MergeMode reuses exactly the same colors.json
        /// resolution (measured geometry/tints stay one source of truth).</summary>
        public static string DefaultColorsPathPublic() => DefaultColorsPath();

        static string DefaultColorsPath()
        {
            var env = Environment.GetEnvironmentVariable("REACMP_COLORS");
            if (!string.IsNullOrEmpty(env)) return env;
            // repo root = 6 levels above WpfHost/bin/Debug/net8.0-windows
            return Path.GetFullPath(Path.Combine(RepoRoot(),
                "extracted", "live", "textcolor-en", "colors.json"));
        }

        static string DefaultFilterMapPath()
        {
            var env = Environment.GetEnvironmentVariable("REACMP_FILTER_MAP");
            if (!string.IsNullOrEmpty(env)) return env;
            return Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,
                "..", "..", "..", "..", "..", "..", "extracted", "live", "textfilter2-en", "filter-map.json"));
        }

        private static SkelNode LoadSkelNode(JsonElement x)
        {
            var n = new SkelNode
            {
                Identity = new ChromeItem
                {
                    Ct = x.TryGetProperty("ct", out var c) ? c.GetString() ?? "" : "",
                    Cls = x.TryGetProperty("cls", out var k) ? k.GetString() ?? "" : "",
                    Name = x.TryGetProperty("name", out var nm) ? nm.GetString() ?? "" : "",
                },
            };
            if (x.TryGetProperty("row", out var rw) && rw.ValueKind == JsonValueKind.Array)
            {
                n.Row = new string[2];
                int i = 0;
                // row = [section:string, index:number] — GetRawText works for both
                foreach (var part in rw.EnumerateArray()) n.Row[i++] = part.GetRawText().Trim('"');
            }
            if (x.TryGetProperty("children", out var chs))
                foreach (var kid in chs.EnumerateArray()) n.Children.Add(LoadSkelNode(kid));
            return n;
        }

        // chrome rows in the spec are arrays of {ct,cls,name} arrays; mirror that
        // shape into ChromeRow without inventing per-view structure.
        private static void LoadChromeRows(List<ChromeRow> target, string section, JsonElement rows)
        {
            int i = 0;
            foreach (var row in rows.EnumerateArray())
            {
                var cr = new ChromeRow { Section = section, Index = i++ };
                foreach (var x in row.EnumerateArray())
                    cr.Items.Add(new ChromeItem
                    {
                        Ct = x.TryGetProperty("ct", out var c) ? c.GetString() ?? "" : "",
                        Cls = x.TryGetProperty("cls", out var k) ? k.GetString() ?? "" : "",
                        Name = x.TryGetProperty("name", out var n) ? n.GetString() ?? "" : "",
                    });
                target.Add(cr);
            }
        }
    }
}
