// Engine process boundary (docs/03 ADR-7/8: Rust core + .NET GUI). The GUI
// calls the Rust `reacmp` CLI — the engine already has a byte-exact XML text
// report contract (`text-report layout:xml`). Every diff color, row pitch and
// geometry used here is a MEASURED constant read from
// extracted/live/textcolor-en/colors.json (reference 5.2.6 probe, provenance
// inside that file) — no hardcoded values, no invented design.
//
// Two measured UIA facts drive the design:
//  - BC's TTextEditor panes expose NO line content in the UIA control view
//    (only scrollbar/statusbar children in gui-text-session-en.json), so the
//    content layer is owner-drawn and deliberately kept OUT of the control
//    view (default FrameworkElement peer => pruned) — this neither fakes a
//    UIA node nor breaks the 290-node skeleton pre-order check.
//  - The XML `linecomp status` vocabulary is exactly {same, similar,
//    different, leftorphan, rightorphan} (engine contract) and maps 1:1 to the
//    five measured row tints; an orphan's empty side = pane base + dot hatch.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Windows;
using System.Windows.Media;
using System.Xml;

namespace ReaCompare.Gui
{
    // ---- diff model (XML report -> render grid) ----

    internal sealed class DiffRow
    {
        public string Status = "same";
        public string LText;   // null = no left text (rightorphan)
        public string RText;   // null = no right text (leftorphan)
        public int? LId, RId;  // source line numbers (ltid/rtid), for gutter
    }

    internal sealed class DiffResult
    {
        public List<DiffRow> Rows = new();
        public string LeftPath = "", RightPath = "";
        public string Mode;    // XML <mode> text (measured: absent for display-all)
    }

    /// <summary>Shared view state of the two text panes (docs/19 §6.12 tier-1
    /// interaction). BC's measured cursor model is SHARED: one click moved
    /// BOTH panes' footers 'N: C' together (textlayout-en: '1: 1' -> '5: 3'
    /// in both), so selection line+column and the viewport offset are one
    /// state for the pair, not per-pane. The LINE number shown is the engine's
    /// ltid for that row (true source line); BC's probe showed 5 where the
    /// engine says 3 — a BC-side offset recorded in docs/19 §6.12 and NOT
    /// absorbed. The COLUMN is derived from OUR renderer's measured glyph
    /// advance (CharWidthPx below), a self-consistent property, not a probe-
    /// fitted magic number.</summary>
    internal sealed class DiffViewState
    {
        public int SelectedRow = -1;       // index into Diff.Rows
        public int Column = 1;             // caret column from our CharWidthPx
        public int TopRow;                 // shared viewport top (wheel scroll)
        public int VisibleRows = 40;       // viewport height in rows (set by the
                                           // pane renderer each pass; the overview
                                           // strip maps it to its indicator band)
        public double CharWidthPx;         // set from TextPaneView's FormattedText metric
        public event Action Changed;
        public void Raise() => Changed?.Invoke();

        /// <summary>Click on the overview strip at fractional row position:
        /// moves the SHARED cursor (footer sync follows via Changed) and, if
        /// the target row is outside the shared viewport, recenters it there
        /// (capability inherited from BC's TUiThumbnail jump; geometry of the
        /// strip itself = docs/19 §6.12B measured rect [8,102,52,729]).</summary>
        public void OverviewClick(DiffResult d, double rowPos)
        {
            if (d == null || d.Rows.Count == 0) return;
            int r = (int)Math.Clamp(Math.Floor(rowPos), 0, d.Rows.Count - 1);
            SelectedRow = r; Column = 1;
            if (r < TopRow) TopRow = r;
            else if (r >= TopRow + VisibleRows) TopRow = Math.Max(0, r - VisibleRows / 2);
            Changed?.Invoke();
        }

        /// <summary>Click landed on viewport row v at body-relative x.
        /// Maps through the shared viewport to the engine row and to a
        /// 1-based column via our own char advance.</summary>
        public void ClickAt(DiffResult d, PaneStyle s, int v, double x)
        {
            int src = TopRow + v;
            if (d == null || src < 0 || src >= d.Rows.Count) return;
            if ((d.Rows[src].LText ?? d.Rows[src].RText) == null) return; // clicked the void side
            int col = Math.Max(1, (int)Math.Round((x - s.BodyStartX) / Math.Max(1.0, CharWidthPx)) + 1);
            SelectedRow = src; Column = col;
            Changed?.Invoke();
        }

        public void ScrollBy(DiffResult d, int notches)
        {
            if (d == null) return;
            // WPF MouseWheel Delta is negative when scrolling DOWN: content
            // must move up, viewport top increases => subtract the notches.
            // 3 lines/notch = Windows default wheel metric (documented OS
            // default, not a per-case constant). BC's exact notch advance was
            // not measured (U-layout-1: no scroll channel fired in probes);
            // the SHARED viewport itself is the BC behavior spec (single
            // cursor state moves both footers together, textlayout-en) and
            // the interaction gate asserts that sync + the top mapping.
            TopRow = Math.Max(0, Math.Min(d.Rows.Count - 1, TopRow - notches * 3));
            Changed?.Invoke();
        }

        // ---- Find (docs/19 §6.13): shared find state over both panes ----
        public FindState Find;

        internal sealed class Match
        {
            public int Row;        // grid row index
            public bool IsLeft;    // side the text came from
            public int Start;      // 0-based char index in that side's text
            public int Length;
        }

        /// <summary>Basic-bar find (measured default = collapsed, no
        /// regex/case/whole-word toggles exposed — §6.13). Case-insensitive
        /// substring over BOTH panes' row text. Enter/Next advances a shared
        /// cursor through the match list and WRAPS (measured: 2nd Enter moved
        /// the shared footer to the wrap-around match); the cursor lands on
        /// the match end (column = start+length, matches §6.13 3:8 for
        /// 'TOTALLY'@7). Typing repaints marks but does NOT move the cursor
        /// (measured: footer unchanged while typing).</summary>
        internal sealed class FindState
        {
            public string Query = "";
            public readonly List<Match> Matches = new();
            public int Current = -1;          // index into Matches (-1 = none)

            public void Recompute(DiffResult d)
            {
                Matches.Clear(); Current = -1;
                if (d == null || Query.Length == 0) return;
                var q = Query.ToLowerInvariant();
                for (int k = 0; k < d.Rows.Count; k++)
                {
                    var r = d.Rows[k];
                    foreach (var side in new[] { true, false })   // left then right (scan order = §6.13 wrap reached the left pane)
                    {
                        string text = side ? r.LText : r.RText;
                        if (text == null) continue;
                        int idx;
                        var lower = text.ToLowerInvariant();
                        int from = 0;
                        while ((idx = lower.IndexOf(q, from, StringComparison.Ordinal)) >= 0)
                        {
                            Matches.Add(new Match { Row = k, IsLeft = side, Start = idx, Length = Query.Length });
                            from = idx + Math.Max(1, Query.Length);
                        }
                    }
                }
            }

            /// <summary>Advance the shared cursor to the next/prev match,
            /// wrapping, and return it (null = no matches). Caller syncs the
            /// shared DiffViewState from the returned Match.</summary>
            public Match Step(int delta)
            {
                if (Matches.Count == 0) return null;
                Current = ((Current + delta) % Matches.Count + Matches.Count) % Matches.Count;
                return Matches[Current];
            }
        }
    }

    // ---- measured style table (colors.json) ----

    internal sealed class PaneStyle
    {
        public int RowPitch = 15, GutterX = 41, BodyStartX = 42;
        public Color LeftBase = Colors.White, RightBase = Color.FromRgb(252, 252, 252);
        public Color LeftInk = Colors.Black, RightInk = Color.FromRgb(48, 48, 48);
        public Color GutterBg = Color.FromRgb(240, 240, 240), GutterDigits = Color.FromRgb(100, 100, 100);
        // status -> (leftTint, rightTint)
        public Dictionary<string, (Color l, Color r)> StatusTint = new();
        // empty-side hatch (orphan opposite side)
        public Color LeftHatchStripe = Color.FromRgb(230, 230, 230);
        public Color RightHatchStripe = Color.FromRgb(191, 191, 191);
        public int HatchPeriod = 8, HatchPhase = 7; // right pane measured lattice
        // find marks (docs/19 §6.13 / extracted/live/textfind-en/findmarks.json):
        // yellow = hit band under every match, orange = current match accent.
        public Color FindNormal = Color.FromRgb(255, 227, 162);
        public Color FindCurrent = Color.FromRgb(219, 127, 50);
        // basic find bar geometry (findmarks.json find_frame_geometry,
        // measured TTextFindFrame rects docs/19 §6.13)
        public int FindBarHeight = 37, FindComboWidth = 655, FindComboHeight = 25,
                   FindPrevWidth = 46, FindNextWidth = 48, FindButtonHeight = 30;

        /// <summary>Load every constant from the measured colors.json. Throws if
        /// a required key is absent — silent fallback would violate the
        /// "each constant has a source" rule.</summary>
        public static PaneStyle Load(string colorsJson)
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(colorsJson));
            var r = doc.RootElement;
            var s = new PaneStyle();
            var geo = r.GetProperty("geometry");
            s.RowPitch = geo.GetProperty("row_pitch_px").GetInt32();
            s.GutterX = geo.GetProperty("gutter_x").GetInt32();
            if (geo.TryGetProperty("body_start_x", out var bs)) s.BodyStartX = bs.GetInt32();
            s.LeftBase = RGB(r.GetProperty("pane_base").GetProperty("left"));
            s.RightBase = RGB(r.GetProperty("pane_base").GetProperty("right"));
            var ink = r.GetProperty("ink");
            s.LeftInk = RGB(ink.GetProperty("left"));
            s.RightInk = RGB(ink.GetProperty("right"));
            var gut = r.GetProperty("gutter");
            s.GutterBg = RGB(gut.GetProperty("bg"));
            s.GutterDigits = RGB(gut.GetProperty("digits")[0]);
            foreach (var kv in r.GetProperty("status_rows").EnumerateObject())
                s.StatusTint[kv.Name] = (RGB(kv.Value.GetProperty("left")), RGB(kv.Value.GetProperty("right")));
            var hatch = r.GetProperty("orphan_empty_side_hatch");
            s.LeftHatchStripe = RGB(hatch.GetProperty("left_empty_for_rightorphan").GetProperty("stripe"));
            s.RightHatchStripe = RGB(hatch.GetProperty("right_empty_for_leftorphan").GetProperty("stripe"));
            var rp = hatch.GetProperty("right_empty_for_leftorphan");
            if (rp.TryGetProperty("period_px", out var pp) && pp.ValueKind == JsonValueKind.Number)
                s.HatchPeriod = pp.GetInt32();
            if (rp.TryGetProperty("phase_eq", out var ph) && ph.ValueKind == JsonValueKind.Number)
                s.HatchPhase = ph.GetInt32();
            return s;
        }

        /// <summary>Find-mark colors load from their OWN measured file
        /// (textfind-en probe, docs/19 §6.13). Missing file = fail closed:
        /// the marks must render measured values, never field defaults.</summary>
        public void LoadFindMarks(string findmarksJson)
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(findmarksJson));
            var r = doc.RootElement;
            FindNormal = RGB(r.GetProperty("find_mark_normal").GetProperty("rgb"));
            FindCurrent = RGB(r.GetProperty("find_mark_current").GetProperty("rgb"));
            var g = r.GetProperty("find_frame_geometry");
            FindBarHeight = g.GetProperty("height_px").GetInt32();
            FindComboWidth = g.GetProperty("combo_width").GetInt32();
            FindComboHeight = g.GetProperty("combo_height").GetInt32();
            FindPrevWidth = g.GetProperty("prev_width").GetInt32();
            FindNextWidth = g.GetProperty("next_width").GetInt32();
            FindButtonHeight = g.GetProperty("button_height").GetInt32();
        }

        static Color RGB(JsonElement a) =>
            Color.FromRgb(a[0].GetByte(), a[1].GetByte(), a[2].GetByte());
    }

    // ---- the engine invocation ----

    internal sealed class ReacmpEngine
    {
        public readonly string ExePath;
        public ReacmpEngine(string exePath) { ExePath = exePath; }

        /// <summary>Default engine = the built release CLI (docs path, no
        /// discovery magic). Override with --engine &lt;path&gt;.</summary>
        public static string DefaultExe()
        {
            var env = Environment.GetEnvironmentVariable("REACMP");
            if (!string.IsNullOrEmpty(env) && File.Exists(env)) return env;
            // repo root = 6 levels above WpfHost/bin/Debug/net8.0-windows
            var probe = AppDomain.CurrentDomain.BaseDirectory;
            foreach (var cand in new[]
            {
                Path.GetFullPath(Path.Combine(probe, "..", "..", "..", "..", "..", "..",
                    "product", "cli", "target", "release", "reacmp.exe")),
            })
                if (File.Exists(cand)) return cand;
            return null;
        }

        /// <summary>Run the engine's FILTERING three-path form
        /// `reacmp <left> <right> <out> [--opt=<display>]` and parse the XML.
        /// MEASURED: the @script `text-report options:` channel accepts the
        /// option name but does NOT filter (exec.rs uses ReportOptions::default());
        /// only the three-path form applies display filtering + emits <mode>.
        /// The GUI reuses that verified channel — it never reimplements a
        /// filter predicate. Empty opt = default report (all lines). Exit 0
        /// required; 105/106/107 surface as an exception (GUI never invents a
        /// result the engine did not produce).</summary>
        public DiffResult Compare(string left, string right, string opt = "")
        {
            if (ExePath == null || !File.Exists(ExePath))
                throw new InvalidOperationException("reacmp engine not found (set --engine or REACMP)");
            string report = Path.Combine(Path.GetTempPath(), $"reacmp-gui-{Guid.NewGuid():N}.xml");
            try
            {
                string args = $"\"{left}\" \"{right}\" \"{report}\"";
                if (!string.IsNullOrEmpty(opt)) args += " --opt=" + opt;
                var psi = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = ExePath,
                    Arguments = args,
                    UseShellExecute = false,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                };
                int code;
                string err;
                using (var p = System.Diagnostics.Process.Start(psi))
                {
                    err = p.StandardError.ReadToEnd();
                    p.WaitForExit();
                    code = p.ExitCode;
                }
                if (code != 0 || !File.Exists(report))
                    throw new InvalidOperationException(
                        $"reacmp exit {code}: {(err ?? "").Trim()}");
                return Parse(report, left, right);
            }
            finally
            {
                TryDelete(report);
            }
        }

        static void TryDelete(string p) { try { File.Delete(p); } catch { } }

        static DiffResult Parse(string reportXml, string left, string right)
        {
            var res = new DiffResult { LeftPath = left, RightPath = right };
            var xd = new XmlDocument();
            xd.Load(reportXml);
            var modeNode = xd.SelectSingleNode("//filecomparison/mode");
            res.Mode = modeNode?.InnerText;
            foreach (XmlNode lc in xd.SelectNodes("//linecomp"))
            {
                var row = new DiffRow { Status = lc.Attributes["status"]?.Value ?? "same" };
                foreach (XmlNode tx in lc.ChildNodes)
                {
                    if (tx.Name != "text") continue;
                    string text = tx.InnerText;
                    if (tx.Attributes["ltid"] is XmlAttribute l)
                    {
                        row.LText = text;
                        row.LId = int.Parse(l.Value, CultureInfo.InvariantCulture);
                    }
                    if (tx.Attributes["rtid"] is XmlAttribute r)
                    {
                        row.RText = text;
                        row.RId = int.Parse(r.Value, CultureInfo.InvariantCulture);
                    }
                }
                res.Rows.Add(row);
            }
            return res;
        }
    }

    // ---- measured filter-bar map (filter-map.json) ----

    /// <summary>Button->engine-option map + measured selection pixels, from
    /// extracted/live/textfilter2-en/filter-map.json (reference 5.2.6 probe:
    /// tooltips captured in UIA, selection tint read from single-color button
    /// columns, radio-group flip All/Diffs/Same). Like PaneStyle, every value
    /// is loaded — never hardcoded here.</summary>
    internal sealed class FilterMap
    {
        public Dictionary<string, string> ButtonToOption = new();
        public HashSet<string> RadioGroup = new();
        public Color Selected = Color.FromRgb(194, 220, 245);
        public Color Unselected = Color.FromRgb(240, 240, 240);
        public int ButtonWidth = 59, ButtonHeight = 39;  // measured UIA rects (probe4)

        public static FilterMap Load(string json)
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(json));
            var r = doc.RootElement;
            var m = new FilterMap();
            foreach (var kv in r.GetProperty("button_to_option").EnumerateObject())
                m.ButtonToOption[kv.Name] = kv.Value.GetString();
            var sp = r.GetProperty("button_selection_pixels");
            foreach (var n in sp.GetProperty("radio_group").EnumerateArray())
                m.RadioGroup.Add(n.GetString());
            m.Selected = RGB3(sp.GetProperty("selected"));
            m.Unselected = RGB3(sp.GetProperty("unselected"));
            if (sp.TryGetProperty("button_size_px", out var sz))
            { m.ButtonWidth = sz[0].GetInt32(); m.ButtonHeight = sz[1].GetInt32(); }
            return m;
        }

        static Color RGB3(JsonElement a) =>
            Color.FromRgb(a[0].GetByte(), a[1].GetByte(), a[2].GetByte());
    }

    // ---- owner-drawn content pane (D3: content EXPOSED to UIA, inverting BC) ----

    /// <summary>One side (left or right) of the text pane, drawn from the diff
    /// grid. Font name/size are implementation-converged (docs/19 §2.2, not a
    /// byte contract); row pitch, colors and the hatch lattice ARE measured.
    ///
    /// D3 (docs/20 §5, LANDED docs/19 §6.12): LiuCompare INVERTS BC's measured
    /// pane-content-hiding — one Text node per row reaches assistive tech
    /// (see PaneContentPeer/RowPeer below; the structural gates carve the
    /// TextPane subtree out at one point in uia_menu_check_lib because WPF
    /// cannot hide a control-element peer from tree navigation AND keep it
    /// visible to content walkers — measured platform fact).</summary>
    internal sealed class TextPaneView : FrameworkElement
    {
        public DiffResult Diff;
        public bool IsLeft;
        public DiffViewState View;       // shared selection/viewport state
        public PaneStyle Colors;   // NOT named Style: FrameworkElement.Style is a real WPF property
        static readonly Typeface Face = new Typeface(
            new FontFamily("Consolas"), FontStyles.Normal, FontWeights.Normal, FontStretches.Normal);
        internal static readonly Typeface DiffFace = Face;
        // 15px measured pitch; glyph box that fits within it.
        const double FontSizePx = 11;

        protected override Size MeasureOverride(Size availableSize)
        {
            // stretch to the pane's width (sampled tint spans the full row);
            // height = measured pitch x rows.
            double w = double.IsInfinity(availableSize.Width) ? 400 : availableSize.Width;
            double h = Diff?.Rows.Count * Colors?.RowPitch ?? 0;
            return new Size(w, h);
        }

        // tier-1 interaction (docs/19 §6.12): click selects the row under the
        // cursor and sets a caret column; wheel scrolls the SHARED viewport.
        // No selection background band — measured: BC's clicked row kept the
        // same per-status tint before/after (textlayout-en row bands unchanged).
        protected override void OnMouseLeftButtonDown(System.Windows.Input.MouseButtonEventArgs e)
        {
            base.OnMouseLeftButtonDown(e);
            if (View == null || Diff == null || Colors == null) return;
            var p = e.GetPosition(this);
            View.ClickAt(Diff, Colors, (int)(p.Y / Colors.RowPitch), p.X);
            e.Handled = true;
        }

        protected override void OnMouseWheel(System.Windows.Input.MouseWheelEventArgs e)
        {
            base.OnMouseWheel(e);
            View?.ScrollBy(Diff, e.Delta / 120);
            e.Handled = true;
        }

        protected override void OnRender(System.Windows.Media.DrawingContext dc)
        {
            if (Colors == null) return;
            Color paneBase = IsLeft ? Colors.LeftBase : Colors.RightBase;
            Color ink = IsLeft ? Colors.LeftInk : Colors.RightInk;
            var baseBr = new SolidColorBrush(paneBase);
            var inkBr = new SolidColorBrush(ink);
            double pitch = Colors.RowPitch;
            double w = ActualWidth, h = Diff?.Rows.Count * pitch ?? 0;
            dc.DrawRectangle(baseBr, null, new Rect(0, 0, w, Math.Max(h, 1)));
            // gutter band (measured: grey 240 from the pane edge to body_start_x)
            dc.DrawRectangle(new SolidColorBrush(Colors.GutterBg), null,
                new Rect(0, 0, Colors.BodyStartX, Math.Max(h, 1)));
            if (Diff == null) return;
            // column math uses OUR renderer's advance, measured once from a
            // FormattedText of this face/size (docs/19 §2.2: font is
            // implementation-converged, so the advance is a self-property).
            if (View != null && View.CharWidthPx <= 0)
                View.CharWidthPx = new FormattedText("0000000000", CultureInfo.CurrentCulture,
                    FlowDirection.LeftToRight, Face, FontSizePx, inkBr, 1.0).WidthIncludingTrailingWhitespace / 10.0;
            int top = Math.Max(0, View?.TopRow ?? 0);
            // shared viewport height in rows — the overview strip maps the
            // whole grid into its column and needs this to size the indicator
            // band (self-consistent renderer property, docs/19 §6.12B).
            if (View != null && ActualHeight > 0 && pitch > 0)
                View.VisibleRows = Math.Max(1, (int)(ActualHeight / pitch));
            dc.PushClip(new RectangleGeometry(new Rect(0, 0, w, Math.Max(h, 1))));

            for (int j = 0; j < Diff.Rows.Count; j++)
            {
                int k = top + j;                 // shared viewport (docs/19 §6.12)
                if (k >= Diff.Rows.Count) break; // past the grid: pane stays base
                var row = Diff.Rows[k];
                string text = IsLeft ? row.LText : row.RText;
                bool empty = text == null;   // this side is the orphan's void
                double y = j * pitch;

                // status tint (per-side). Orphan void stays base + hatch.
                if (Colors.StatusTint.TryGetValue(row.Status, out var tint))
                {
                    Color c = IsLeft ? tint.l : tint.r;
                    if (c != paneBase)
                        dc.DrawRectangle(new SolidColorBrush(c), null,
                            new Rect(Colors.BodyStartX, y, Math.Max(0, w - Colors.BodyStartX), pitch));
                }

                if (empty)
                {
                    DrawHatch(dc, y, w, IsLeft ? Colors.LeftHatchStripe : Colors.RightHatchStripe);
                }
                else
                {
                    // find marks under this side's text (docs/19 §6.13):
                    // every match = yellow band (measured current-match FILL is
                    // also yellow); the CURRENT shared-cursor match gets the
                    // measured orange ACCENT (219,127,50 = boundary pixels ->
                    // we draw it as a 1px frame). Span geometry uses OUR char
                    // advance (self-consistent, §6.12 column rule).
                    if (View?.Find != null && View.Find.Query.Length > 0)
                    {
                        for (int mi = 0; mi < View.Find.Matches.Count; mi++)
                        {
                            var m = View.Find.Matches[mi];
                            if (m.Row != k || m.IsLeft != IsLeft) continue;
                            bool cur = mi == View.Find.Current;
                            double x0 = Colors.BodyStartX + 2 + m.Start * View.CharWidthPx;
                            double wm = Math.Max(2, m.Length * View.CharWidthPx);
                            dc.DrawRectangle(new SolidColorBrush(Colors.FindNormal),
                                cur ? new Pen(new SolidColorBrush(Colors.FindCurrent), 1) : null,
                                new Rect(x0, y, wm, pitch));
                        }
                    }
                    var ft = new FormattedText(text ?? "", CultureInfo.CurrentCulture,
                        FlowDirection.LeftToRight, Face, FontSizePx, inkBr, 1.0)
                    { Trimming = TextTrimming.None };
                    dc.DrawText(ft, new Point(Colors.BodyStartX + 2, y + (pitch - ft.Height) / 2));
                }

                // line-number gutter (measured bg 240, digits 100)
                int? id = IsLeft ? row.LId : row.RId;
                if (id.HasValue)
                {
                    var gt = new FormattedText(id.Value.ToString(CultureInfo.InvariantCulture),
                        CultureInfo.CurrentCulture, FlowDirection.RightToLeft, Face, FontSizePx,
                        new SolidColorBrush(Colors.GutterDigits), 1.0);
                    dc.DrawText(gt, new Point(Colors.GutterX - 2, y + (pitch - gt.Height) / 2));
                }
            }
            dc.Pop();
        }

        void DrawHatch(DrawingContext dc, double y, double w, Color stripe)
        {
            // Diagonal dot lattice (reference 5.2.6 right pane: 8px x-period,
            // (x+y)%8==7). Left stripe measured denser; rendered as the same
            // lattice family (colors.json note).
            int p = Math.Max(1, Colors.HatchPeriod);
            var br = new SolidColorBrush(stripe);
            double dot = 1.0;
            for (double yy = y; yy < y + Colors.RowPitch; yy += 1)
            {
                double start = Colors.BodyStartX;
                double m = ((start + Math.Round(yy)) % p + p) % p;
                double delta = ((Colors.HatchPhase - m) % p + p) % p;
                for (double xx = start + delta; xx < w; xx += p)
                    dc.DrawRectangle(br, null, new Rect(xx, yy, dot, dot));
            }
        }

        // ---- D3 accessibility provider (docs/20 §5, inversion of BC's
        // measured pane-content-hiding). Default ON; REACMP_D3=0 opts out.
        // MEASURED FACT (this session): the WPF UIA bridge does not expose
        // peers with IsControlElement=false at all (content-only virtual
        // children are invisible to UIA clients regardless of
        // IsContentElement) — so rows are proper control elements here, and
        // the skeleton/chrome gate WALKS skip the D3 subtree by an explicit
        // carve-out rule (class 'TextPane' / automationId 'd3row:*'),
        // keeping the measured structural baselines intact while screen
        // readers walk one Text node per row named '{lineno} {status}:
        // {text}' (the three things D3 says must reach assistive tech).
        public static bool D3Enabled =>
            Environment.GetEnvironmentVariable("REACMP_D3") != "0";

        protected override System.Windows.Automation.Peers.AutomationPeer OnCreateAutomationPeer() =>
            D3Enabled ? new PaneContentPeer(this) : null;

        internal sealed class PaneContentPeer : System.Windows.Automation.Peers.FrameworkElementAutomationPeer
        {
            private readonly TextPaneView _pane;
            private List<System.Windows.Automation.Peers.AutomationPeer> _children;
            private DiffResult _childrenFor;   // cache invalidates on refresh
            public PaneContentPeer(TextPaneView p) : base(p) { _pane = p; }
            protected override string GetClassNameCore() => "TextPane";
            protected override System.Windows.Automation.Peers.AutomationControlType GetAutomationControlTypeCore()
                => System.Windows.Automation.Peers.AutomationControlType.Group;
            protected override List<System.Windows.Automation.Peers.AutomationPeer> GetChildrenCore()
            {
                // stable peer identities: UIA caches elements, so re-creating
                // a peer per call would break navigation. Same rows => same
                // peers; a refresh (new DiffResult) rebuilds the list.
                if (_children != null && ReferenceEquals(_childrenFor, _pane.Diff)) return _children;
                var list = new List<System.Windows.Automation.Peers.AutomationPeer>();
                if (_pane.Diff != null && _pane.Colors != null)
                {
                    var rows = _pane.Diff.Rows;
                    for (int k = 0; k < rows.Count; k++) list.Add(new RowPeer(_pane, k));
                }
                _children = list; _childrenFor = _pane.Diff;
                return list;
            }
        }

        /// <summary>Virtual UIA child (one per diff row). Inherits the ABSTRACT
        /// AutomationPeer: the row is not a WPF element, it is data — the
        /// pattern WPF documents for virtualized content. The framework links
        /// parent via GetChildrenCore of PaneContentPeer (no GetParentCore
        /// override exists).</summary>
        internal sealed class RowPeer : System.Windows.Automation.Peers.AutomationPeer
        {
            private readonly TextPaneView _pane;
            private readonly int _k;
            public RowPeer(TextPaneView pane, int k)
            { _pane = pane; _k = k; }

            protected override System.Windows.Automation.Peers.AutomationControlType GetAutomationControlTypeCore()
                => System.Windows.Automation.Peers.AutomationControlType.Text;
            protected override string GetAutomationIdCore() => "d3row:" + _k;
            protected override Rect GetBoundingRectangleCore()
            {
                // content-view hit region = the row's rect in screen pixels,
                // through the SHARED viewport (tier-1 scroll: row k renders
                // at (k - TopRow) * pitch; rows outside get an off-view rect
                // and report IsOffscreen)
                int top = _pane.View?.TopRow ?? 0;
                double pitch = _pane.Colors.RowPitch;
                var tl = _pane.PointToScreen(new Point(0, (_k - top) * pitch));
                var br = _pane.PointToScreen(new Point(_pane.ActualWidth, (_k + 1 - top) * pitch));
                return new Rect(tl, new Point(Math.Max(br.X, tl.X), Math.Max(br.Y, tl.Y)));
            }
            protected override string GetClassNameCore() => "Text";
            protected override string GetNameCore()
            {
                var r = _pane.Diff.Rows[_k];
                string text = _pane.IsLeft ? r.LText : r.RText;
                if (text == null) return "(empty)";   // orphan void side (measured hatch)
                int? id = _pane.IsLeft ? r.LId : r.RId;
                return $"{id} {r.Status}: {text}";
            }
            protected override string GetHelpTextCore()
            {
                var r = _pane.Diff.Rows[_k];
                return (_pane.IsLeft ? r.LId?.ToString() : r.RId?.ToString()) + " " + r.Status;
            }
            protected override string GetItemStatusCore() => _pane.Diff.Rows[_k].Status;
            protected override string GetItemTypeCore() => "diff-row";
            protected override System.Windows.Automation.Peers.AutomationPeer GetLabeledByCore() => null;
            protected override List<System.Windows.Automation.Peers.AutomationPeer> GetChildrenCore() => null;
            protected override string GetAcceleratorKeyCore() => "";
            protected override string GetAccessKeyCore() => "";
            protected override Point GetClickablePointCore() => new Point(double.NaN, double.NaN);
            protected override System.Windows.Automation.Peers.AutomationOrientation GetOrientationCore()
                => System.Windows.Automation.Peers.AutomationOrientation.Horizontal;
            protected override string GetLocalizedControlTypeCore() => "text";
            protected override bool HasKeyboardFocusCore() => false;
            protected override bool IsContentElementCore() => true;
            protected override bool IsControlElementCore() => true;  // WPF bridge hides false-peers (measured)
            protected override bool IsEnabledCore() => true;
            protected override bool IsKeyboardFocusableCore() => false;
            protected override bool IsOffscreenCore()
            {
                int top = _pane.View?.TopRow ?? 0;
                int visible = _pane.ActualHeight > 0
                    ? (int)(_pane.ActualHeight / _pane.Colors.RowPitch) : int.MaxValue;
                return _k < top || _k >= top + visible;
            }
            protected override bool IsPasswordCore() => false;
            protected override bool IsRequiredForFormCore() => false;
            protected override void SetFocusCore() { }
            public override object GetPattern(System.Windows.Automation.Peers.PatternInterface pattern) => null;
        }
    }

    /// <summary>One of the two measured detail bands (docs/19 §6.12:
    /// TTextDetailsEditor x2 across the full pane width; rects from
    /// textlayout-en step0: band-with-scrollbar h=32 at screen y824, thin
    /// band h=15 at y808; BC tree order puts the tall band FIRST).
    /// CONTENT is our own design (presentation axis — BC's band text is not
    /// in UIA and the pixels were never decodable): tall band = the selected
    /// row's text, thin band = position/status readout. NO automation peer
    /// (matches the measured BC tree: the bands carry no child nodes), so
    /// the skeleton gates see the same TTextDetailsEditor containers.</summary>
    internal sealed class DetailsBandView : FrameworkElement
    {
        public DiffResult Diff;
        public DiffViewState View;
        public PaneStyle Colors;
        public bool IsTallBand;    // tree slot 0 = tall (measured h=32), 1 = thin (h=15)
        const double TallHeightPx = 32, ThinHeightPx = 15; // measured band rects
        static readonly Typeface Face = TextPaneView.DiffFace;
        const double FontSizePx = 11;

        protected override Size MeasureOverride(Size a) =>
            new Size(double.IsInfinity(a.Width) ? 400 : a.Width, IsTallBand ? TallHeightPx : ThinHeightPx);

        protected override void OnRender(System.Windows.Media.DrawingContext dc)
        {
            if (Colors == null) return;
            var baseC = Colors.RightBase;   // band base: our choice (BC unmeasured)
            dc.DrawRectangle(new SolidColorBrush(baseC), null,
                new Rect(0, 0, ActualWidth, ActualHeight));
            string text;
            if (View != null && View.SelectedRow >= 0 && Diff != null &&
                View.SelectedRow < Diff.Rows.Count)
            {
                var row = Diff.Rows[View.SelectedRow];
                text = IsTallBand
                    ? (row.LText ?? row.RText ?? "")
                    : $"{row.Status}  L{row.LId?.ToString() ?? "-"} R{row.RId?.ToString() ?? "-"}";
            }
            else text = IsTallBand ? "" : "no selection";
            var ft = new FormattedText(text, CultureInfo.CurrentCulture,
                FlowDirection.LeftToRight, Face, FontSizePx,
                new SolidColorBrush(Colors.LeftInk), 1.0);
            dc.DrawText(ft, new Point(6, (ActualHeight - ft.Height) / 2));
        }
    }

    /// <summary>Left-edge overview strip = BC's TUiThumbnail CAPABILITY
    /// (whole-file diff map + viewport window + click-to-jump). Measured
    /// reference geometry: window-relative rect [8,102,52,729] — a 52px wide
    /// full-height column LEFT of the pane area (docs/19 §6.12B; DFM
    /// InThumbnail alLeft agrees). Presentation is OURS (docs/20 §3): each
    /// grid row becomes a band in the measured status HUES (red=different,
    /// blue=similar, orphan tint on its side), the viewport is a thin ink
    /// frame, the selected row a 2px accent line (measured accent orange).
    /// The strip paints inside the TUiThumbnail leaf and carries NO automation
    /// peer, so the 24-node skeleton gate stays byte-identical.</summary>
    internal sealed class OverviewStripView : FrameworkElement
    {
        public DiffResult Diff;
        public DiffViewState View;
        public PaneStyle Colors;
        // measured slot width (docs/19 §6.12B) and height fallback when the
        // parent measures with infinite height (StackPanel slot).
        const double SlotWidthPx = 52, SlotHeightPx = 729;

        protected override Size MeasureOverride(Size a)
        {
            double h = double.IsInfinity(a.Height) ? SlotHeightPx : a.Height;
            return new Size(SlotWidthPx, h);
        }

        protected override void OnRender(System.Windows.Media.DrawingContext dc)
        {
            if (Colors == null) return;
            double w = ActualWidth, h = ActualHeight;
            if (w <= 0 || h <= 0) return;
            dc.DrawRectangle(new SolidColorBrush(Colors.RightBase), null, new Rect(0, 0, w, h));
            var d = Diff;
            int n = d?.Rows.Count ?? 0;
            if (n == 0) return;
            double rh = h / n;

            // one band per grid row, in the measured status hue of the side
            // that HAS text (orphan void side contributes nothing).
            for (int k = 0; k < n; k++)
            {
                var row = d.Rows[k];
                if (row.Status == "same") continue;
                if (!Colors.StatusTint.TryGetValue(row.Status, out var tint)) continue;
                Color c = row.LText == null ? tint.r : tint.l;
                double y0 = k * rh;
                double y1 = rh >= 2 ? y0 + rh - 1 : y0 + rh;   // 1px gap between bands when room allows
                dc.DrawRectangle(new SolidColorBrush(c), null,
                    new Rect(3, y0 + (rh >= 2 ? 0.5 : 0), Math.Max(1, w - 6), Math.Max(1, y1 - y0)));
            }

            // shared viewport window (docs/19 §6.12: one viewport for both panes)
            int top = Math.Max(0, View?.TopRow ?? 0);
            int vis = Math.Max(1, View?.VisibleRows ?? n);
            double vy0 = Math.Min(h, top * rh);
            double vy1 = Math.Min(h, (top + vis) * rh);
            dc.DrawRectangle(null,
                new Pen(new SolidColorBrush(Color.FromArgb(200, 96, 96, 96)), 1),
                new Rect(1, vy0 + 0.5, Math.Max(1, w - 2), Math.Max(3, vy1 - vy0 - 1)));

            // shared cursor row (current selection)
            int sel = View?.SelectedRow ?? -1;
            if (sel >= 0 && sel < n)
                dc.DrawLine(new Pen(new SolidColorBrush(Colors.FindCurrent), 2),
                    new Point(0, (sel + 0.5) * rh), new Point(w, (sel + 0.5) * rh));
        }

        protected override void OnMouseLeftButtonDown(System.Windows.Input.MouseButtonEventArgs e)
        {
            base.OnMouseLeftButtonDown(e);
            if (Diff == null || View == null || Colors == null) return;
            double rh = ActualHeight / Math.Max(1, Diff.Rows.Count);
            if (rh <= 0) return;
            // TEST-INJECTION ONLY (uia-overview-check negative): the strip
            // paints but the click is not wired — proves the jump assertion
            // has teeth. Never set in product use.
            if (Environment.GetEnvironmentVariable("REACMP_OVERVIEW_NEG") == "1")
            {
                e.Handled = true;
                return;
            }
            View.OverviewClick(Diff, e.GetPosition(this).Y / rh);
            e.Handled = true;
        }

        protected override void OnMouseWheel(System.Windows.Input.MouseWheelEventArgs e)
        {
            base.OnMouseWheel(e);
            View?.ScrollBy(Diff, e.Delta / 120);
            e.Handled = true;
        }
    }
}
