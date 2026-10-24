// Folder Compare view, tier 1 (docs/20 feature 3 GUI; measured model
// docs/19 §6.20, extracted/live/folderview-en/folderview-findings.json).
//
// Data channel: `reacmp --dir3 <L> <R> <out.json>` (LiuCompare-NATIVE verb,
// same status as --merge3/--hex3 — BC's folder-report renders the M5 text
// report, a different contract). The JSON carries the engine's visible walk
// (name/rel/depth/status/dir + per-side byte sizes + unix-millis times).
//
// Measured fidelity contract (folderview-findings.json):
//   ONE full-width list drawing BOTH sides: per side Name | Size | Modified
//   columns, a thin center gap; aligned band rows — an orphan row renders on
//   its side only, the other side blank; row pitch ~20.5px; dirs first.
//   colors: same = black; diff = RED (255,0,0); orphans = PURPLE (106,0,213);
//   newer = GRAY (128,128,128) with the newer side's timestamp in RED;
//   zebra = odd data rows (248,250,249); cursor = light blue (168,205,241)
//   following the click; folder size = subtree aggregate (engine-side).
//   Timestamps render slash-date with no zero padding (measured
//   '2026/10/24 2:19:13', '2020/2/1 8:00:00').
//
// Tier-1 scope (recorded): depth-0 rows only (BC default = dirs collapsed
// with computed aggregates — the JSON still carries deeper levels); no
// expand/collapse interaction, no log frame content, status bar counts are
// chrome-shell follow-ups.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;

namespace ReaCompare.Gui
{
    /// <summary>Engine row (parsed from --dir3 JSON; the GUI never
    /// re-classifies).</summary>
    internal sealed class FolderRow
    {
        public string Name = "", Rel = "", Status = "";
        public int Depth;
        public bool IsDir;
        public long? LSize, RSize, LTime, RTime;

        /// <summary>Measured column text color per status token.</summary>
        public Color TextColor
        {
            get
            {
                var p = FolderPalette.C;
                switch (Status)
                {
                    case "diff": return p.DiffText;
                    case "ltonly":
                    case "rtonly": return p.OrphanText;
                    case "ltnewer":
                    case "rtnewer": return p.NewerText;
                    default: return p.Ink;
                }
            }
        }
    }

    internal sealed class FolderModel
    {
        public List<FolderRow> All = new();

        public static FolderModel Load(string jsonPath)
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(jsonPath));
            var r = doc.RootElement;
            if (r.GetProperty("kind").GetString() != "reacmp-dir3/1")
                throw new InvalidOperationException("unexpected dir document kind");
            var m = new FolderModel();
            foreach (var e in r.GetProperty("rows").EnumerateArray())
            {
                var row = new FolderRow
                {
                    Name = e.GetProperty("name").GetString() ?? "",
                    Rel = e.GetProperty("rel").GetString() ?? "",
                    Depth = e.GetProperty("depth").GetInt32(),
                    IsDir = e.GetProperty("dir").GetBoolean(),
                    Status = e.GetProperty("status").GetString() ?? "",
                };
                row.LSize = Num(e.GetProperty("lsize"));
                row.RSize = Num(e.GetProperty("rsize"));
                row.LTime = NumI(e.GetProperty("ltime"));
                row.RTime = NumI(e.GetProperty("rtime"));
                m.All.Add(row);
            }
            return m;
        }

        static long? Num(JsonElement e) =>
            e.ValueKind == JsonValueKind.Null ? null : e.GetInt64();
        static long? NumI(JsonElement e) =>
            e.ValueKind == JsonValueKind.Null ? null : e.GetInt64();

        /// <summary>The top-level rows = BC's default view (directories
        /// collapsed with computed aggregates; measured folderview-en).</summary>
        public IEnumerable<FolderRow> Visible => All.Where(r => r.Depth == 0);
    }

    /// <summary>Measured palette, loaded STRICT from the probe artifact
    /// (extracted/live/folderview-en/folderview-findings.json, docs/19 §6.20).
    /// Color parsing: "black (0,0,0)"-style prose -> first RGB triple.</summary>
    internal static class FolderPalette
    {
        public sealed class Cols
        {
            public Color Ink, DiffText, OrphanText, NewerText, Zebra, Cursor,
                NewerStamp;
        }

        public static readonly Cols C = Load();

        static Color Parse(string s)
        {
            int a = s.IndexOf('(');
            int b = s.IndexOf(')');
            var parts = s.Substring(a + 1, b - a - 1).Split(',');
            return Color.FromRgb(byte.Parse(parts[0].Trim()), byte.Parse(parts[1].Trim()),
                byte.Parse(parts[2].Trim()));
        }

        static Cols Load()
        {
            string path = Path.Combine(MenuMode.RepoRoot(),
                "extracted", "live", "folderview-en", "folderview-findings.json");
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var c = doc.RootElement.GetProperty("status_colors_measured");
            var z = doc.RootElement.GetProperty("row_model");
            string Zebra() => z.GetProperty("zebra").GetString() ?? "";
            string Cursor() => z.GetProperty("selection_cursor").GetString() ?? "";
            return new Cols
            {
                Ink = Parse(c.GetProperty("same").GetString() ?? ""),
                DiffText = Parse(c.GetProperty("diff").GetString() ?? ""),
                OrphanText = Parse(c.GetProperty("left_only").GetString() ?? ""),
                NewerText = Parse(c.GetProperty("newer").GetString() ?? ""),
                NewerStamp = Parse(c.GetProperty("newer").GetString() ?? ""),
                Zebra = Parse(Zebra().Substring(Zebra().IndexOf('('))),
                Cursor = Parse(Cursor().Substring(Cursor().IndexOf('('))),
            };
        }
    }

    /// <summary>Shared folder view state: one cursor row (visible index) —
    /// BC's measured cursor tint follows the click; wheel scrolls the
    /// aligned list.</summary>
    internal sealed class FolderViewState
    {
        public readonly FolderModel Model;
        public readonly List<FolderRow> Rows;
        public int TopRow;
        public int SelectedRow = -1;
        public int VisibleRows = 20;

        public event Action Changed;
        public void Raise() => Changed?.Invoke();

        public FolderViewState(FolderModel m)
        {
            Model = m;
            Rows = m.Visible.ToList();
            SelectedRow = Rows.Count > 0 ? 0 : -1;
        }

        public void ClickRow(int row)
        {
            row = Math.Clamp(row, 0, Math.Max(0, Rows.Count - 1));
            if (row == SelectedRow) return;
            // TEST-INJECTION ONLY (uia-folder-check negative): the click is
            // accepted but the cursor never moves — proves the selection
            // assertions have teeth. Never set in product use.
            if (Environment.GetEnvironmentVariable("REACMP_FOLDER_NEG") == "1") return;
            SelectedRow = row;
            if (row < TopRow) TopRow = row;
            else if (row >= TopRow + VisibleRows) TopRow = Math.Max(0, row - VisibleRows / 2);
            Raise();
        }

        public void Scroll(int notches)
        {
            int max = Math.Max(0, Rows.Count - 1);
            TopRow = Math.Clamp(TopRow - notches * 3, 0, max);
            Raise();
        }

        /// <summary>Status-bar census over the DISPLAYED rows (the measured
        /// BC semantics: collapsed directories contribute nothing — the probe
        /// read '4 file(s), 24 bytes' with sub collapsed, s.txt not counted).
        /// Files only; the byte total sums the side's own sizes. The GUI
        /// never re-classifies: statuses come from the engine rows.</summary>
        public (int files, long bytes) SideTotals(bool left)
        {
            int files = 0;
            long bytes = 0;
            foreach (var r in Rows)
            {
                var sz = left ? r.LSize : r.RSize;
                if (!r.IsDir && sz != null)
                {
                    files++;
                    bytes += sz.Value;
                }
            }
            return (files, bytes);
        }
    }

    /// <summary>Owner-draw full-width folder list drawing BOTH sides (the
    /// measured TDirTreeView model). No UIA peer: the skeleton's TDirTreeView
    /// container keeps the tree unchanged (BC's own list exposes no row
    /// content; D3 rows = recorded follow-up).</summary>
    internal sealed class FolderListView : FrameworkElement
    {
        readonly FolderViewState V;
        readonly PaneStyle S;
        static readonly Typeface Face = TextPaneView.DiffFace;
        const double FontSizePx = 11;
        const double Pitch = 20.5;             // measured row pitch (§6.20)
        double CharW = -1;

        public FolderListView(FolderViewState v, PaneStyle s)
        { V = v; S = s; v.Changed += () => InvalidateVisual(); Focusable = true; }

        // column metrics derived from our own face (biaoxian self-design; the
        // per-side Name|Size|Modified structure + center gap is the contract)
        double NameX, SizeRightL, ModXL, LeftW, GapW, NameXR, SizeRightR, ModXR;

        void Metrics(double w)
        {
            if (CharW < 0)
                CharW = new FormattedText("00000000", CultureInfo.CurrentCulture,
                    FlowDirection.LeftToRight, Face, FontSizePx,
                    new SolidColorBrush(Colors.Black), 1.0)
                    .WidthIncludingTrailingWhitespace / 8.0;
            // measured split: left pane ~0..48% of the list, gap to ~51%,
            // right pane to the end (TDirTreeView [8,172,1440,555]: left
            // Modified ends 690, right Name starts 737)
            LeftW = w * 0.48;
            GapW = w * 0.03;
            NameX = 6;
            SizeRightL = LeftW - 8 * CharW - 12;
            ModXL = LeftW - 8 * CharW - 6;
            NameXR = LeftW + GapW + 6;
            SizeRightR = w - 8 * CharW - 12;
            ModXR = w - 8 * CharW - 6;
        }

        /// <summary>Measured timestamp format: '2026/10/24 2:19:13' — slash
        /// date, no zero padding on month/day/hour, local wall clock.</summary>
        static string Stamp(long unixMillis)
        {
            var t = DateTimeOffset.FromUnixTimeMilliseconds(unixMillis).LocalDateTime;
            return $"{t.Year}/{t.Month}/{t.Day} {t.Hour}:{t.Minute}:{t.Second}";
        }

        // same unbounded-desired model as TextPaneView/HexPaneView: the list
        // lays out all rows and paints the viewport into its surface top.
        protected override Size MeasureOverride(Size availableSize)
        {
            double w = double.IsInfinity(availableSize.Width) ? 400 : availableSize.Width;
            return new Size(w, V.Rows.Count * Pitch);
        }

        protected override void OnRender(DrawingContext dc)
        {
            double w = ActualWidth, h = ActualHeight;
            if (w <= 0 || h <= 0) return;
            Metrics(w);
            V.VisibleRows = Math.Max(1, (int)(h / Pitch));
            var p = FolderPalette.C;
            dc.DrawRectangle(new SolidColorBrush(Colors.White), null, new Rect(0, 0, w, h));
            var ink = new SolidColorBrush(p.Ink);
            var zebra = new SolidColorBrush(p.Zebra);
            var cursor = new SolidColorBrush(p.Cursor);
            var gray = new SolidColorBrush(Color.FromRgb(150, 150, 150));
            var newerRed = new SolidColorBrush(p.NewerStamp);
            int top = Math.Max(0, V.TopRow);
            for (int j = 0; j < V.VisibleRows + 1; j++)
            {
                int idx = top + j;
                double y = j * Pitch;
                if (y >= h) break;
                if (idx >= V.Rows.Count)
                    continue;
                var row = V.Rows[idx];
                bool cursorRow = idx == V.SelectedRow;
                if (cursorRow)
                    dc.DrawRectangle(cursor, null, new Rect(0, y, w, Pitch));
                else if (idx % 2 == 1)
                    dc.DrawRectangle(zebra, null, new Rect(0, y, w, Pitch));
                // per-side fields; an orphan renders on its side only
                DrawSide(dc, row, cursorRow, y, false, ink, gray, newerRed);
                DrawSide(dc, row, cursorRow, y, true, ink, gray, newerRed);
            }
        }

        void DrawSide(DrawingContext dc, FolderRow row, bool cursorRow, double y,
                      bool right, SolidColorBrush ink, SolidColorBrush gray,
                      SolidColorBrush newerRed)
        {
            bool left = !right;
            long? size = left ? row.LSize : row.RSize;
            long? time = left ? row.LTime : row.RTime;
            if (size == null && time == null)
                return; // orphan side: blank (measured)
            double nameX = left ? NameX : NameXR;
            double sizeRight = left ? SizeRightL : SizeRightR;
            double modX = left ? ModXL : ModXR;
            var inkBrush = new SolidColorBrush(row.TextColor);
            // name (folder rows keep engine order; tier-1 depth 0 has no indent)
            var ft = new FormattedText(row.Name, CultureInfo.CurrentCulture,
                FlowDirection.LeftToRight, Face, FontSizePx, inkBrush, 1.0);
            dc.DrawText(ft, new Point(nameX, y + (Pitch - ft.Height) / 2));
            // size, right-aligned in its column (gray like the measured
            // non-cursor secondary text? measured: sizes render in the row's
            // status color family — keep the row color; folder aggregate too)
            if (size != null)
            {
                var sf = new FormattedText(size.Value.ToString(),
                    CultureInfo.CurrentCulture, FlowDirection.LeftToRight, Face,
                    FontSizePx, inkBrush, 1.0);
                dc.DrawText(sf, new Point(sizeRight - sf.Width, y + (Pitch - sf.Height) / 2));
            }
            // modified (measured: the NEWER side's stamp is red on a newer row,
            // the older side's stamp renders gray-ish; the probe measured the
            // older stamp in the row's gray and the newer in red)
            if (time != null)
            {
                bool newerStamp = row.Status is "ltnewer" or "rtnewer" &&
                    ((row.Status == "ltnewer") == left);
                var stampBrush = row.Status is "ltnewer" or "rtnewer"
                    ? (newerStamp ? newerRed : gray) : inkBrush;
                var tf = new FormattedText(Stamp(time.Value),
                    CultureInfo.CurrentCulture, FlowDirection.LeftToRight, Face,
                    FontSizePx, stampBrush, 1.0);
                dc.DrawText(tf, new Point(modX, y + (Pitch - tf.Height) / 2));
            }
        }

        protected override void OnMouseLeftButtonDown(MouseButtonEventArgs e)
        {
            base.OnMouseLeftButtonDown(e);
            var pos = e.GetPosition(this);
            V.ClickRow(V.TopRow + (int)(pos.Y / Pitch));
            e.Handled = true;
        }

        protected override void OnMouseWheel(MouseWheelEventArgs e)
        {
            base.OnMouseWheel(e);
            V.Scroll(e.Delta / 120);
            e.Handled = true;
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);
            if (V.Rows.Count == 0) return;
            int r = Math.Max(0, V.SelectedRow);
            switch (e.Key)
            {
                case Key.Down: r = Math.Min(V.Rows.Count - 1, r + 1); break;
                case Key.Up: r = Math.Max(0, r - 1); break;
                case Key.PageDown: r = Math.Min(V.Rows.Count - 1, r + V.VisibleRows); break;
                case Key.PageUp: r = Math.Max(0, r - V.VisibleRows); break;
                default: return;
            }
            V.ClickRow(r);
            e.Handled = true;
        }
    }
}
