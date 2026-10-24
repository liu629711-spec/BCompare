// Hex Compare view (docs/20 feature 5 GUI tier; measured model docs/19 §6.19,
// extracted/live/hexview-en/hexview-findings.json).
//
// Data channel: `reacmp --hex3 <L> <R> <out.json>` (LiuCompare-NATIVE verb,
// same status as --merge3 — the BC scripting reference has no hex data verb;
// the M7 `hex-report` script verb renders the text report, a different
// contract). The JSON carries the FLAT alignment slot stream (byte values +
// matched flag + counts); this view regroups it into the VIEW's measured
// 16-byte rows (two 8-byte groups), unlike the report's 8-slot rows.
//
// Measured fidelity contract (hexview-findings.json):
//   row = offset(8 hex digits, gray) + 16 bytes in 2x8 groups (black ink) +
//         16-char ascii zone; row pitch ~17.5px
//   changed/orphan byte = RED text + pink band behind hex slots AND ascii
//   char (per BYTE — same row mixes red and black)
//   slots where the side has no byte = diagonal hatch (230,230,230)
//   caret = cyan block (0,255,255) on the current byte's ascii cell
//   pane content stays OUT of UIA (BC-measured; D3 row exposure = follow-up)
//
// Colors load STRICTLY from the measured findings artifact; geometry derives
// from our own face metrics (biaoxian-axis self-design, structure inherited).

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
    /// <summary>Engine slot stream (parsed from --hex3 JSON; the GUI never
    /// re-classifies).</summary>
    internal sealed class HexModel
    {
        public List<(byte? l, byte? r, bool matched)> Slots = new();
        public int LeftSize, RightSize;
        public int Same, LeftOrphan, RightOrphan, Difference;

        public int RowCount => (Slots.Count + 15) / 16;

        public static HexModel Load(string jsonPath)
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(jsonPath));
            var r = doc.RootElement;
            if (r.GetProperty("kind").GetString() != "reacmp-hex3/1")
                throw new InvalidOperationException("unexpected hex document kind");
            var m = new HexModel();
            m.LeftSize = r.GetProperty("sizes").GetProperty("left").GetInt32();
            m.RightSize = r.GetProperty("sizes").GetProperty("right").GetInt32();
            var c = r.GetProperty("counts");
            m.Same = c.GetProperty("same").GetInt32();
            m.LeftOrphan = c.GetProperty("left_orphan").GetInt32();
            m.RightOrphan = c.GetProperty("right_orphan").GetInt32();
            m.Difference = c.GetProperty("difference").GetInt32();
            foreach (var s in r.GetProperty("slots").EnumerateArray())
            {
                byte? L = s[0].ValueKind == JsonValueKind.Null ? null : s[0].GetByte();
                byte? R = s[1].ValueKind == JsonValueKind.Null ? null : s[1].GetByte();
                m.Slots.Add((L, R, s[2].GetBoolean()));
            }
            return m;
        }
    }

    /// <summary>Measured palette, loaded STRICT from the probe artifact
    /// (extracted/live/hexview-en/hexview-findings.json, docs/19 §6.19).</summary>
    internal static class HexPalette
    {
        public static readonly Color Ink = From("ink_normal");
        public static readonly Color OffsetInk = From("ink_offset");
        public static readonly Color ChangedText = From("changed_byte_text");
        public static readonly Color ChangedBand = From("changed_byte_band");
        public static readonly Color Hatch = From("empty_slot_hatch");
        public static readonly Color Caret = From("caret");

        static Color From(string key)
        {
            string path = Path.Combine(MenuMode.RepoRoot(),
                "extracted", "live", "hexview-en", "hexview-findings.json");
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var t = doc.RootElement.GetProperty("colors_measured").GetProperty(key);
            var s = t.GetString() ?? "";
            // "black (0,0,0) ..." / "RED (255,0,0) ..." -> first triple
            int a = s.IndexOf('(');
            int b = s.IndexOf(')');
            var parts = s.Substring(a + 1, b - a - 1).Split(',');
            return Color.FromRgb(byte.Parse(parts[0].Trim()), byte.Parse(parts[1].Trim()),
                byte.Parse(parts[2].Trim()));
        }
    }

    /// <summary>Shared hex view state: one cursor (slot index) + one viewport
    /// for BOTH panes (the text-view shared model; BC's caret sits on the
    /// same alignment slot in both editors — measured cyan blocks on row 0
    /// char 0 in both panes).</summary>
    internal sealed class HexViewState
    {
        public readonly HexModel Model;
        public int TopRow;
        public int SelectedSlot = -1;
        public int VisibleRows = 40;

        public event Action Changed;
        public void Raise() => Changed?.Invoke();

        public HexViewState(HexModel m)
        {
            Model = m;
            // fresh view: cursor at the first changed byte (the text view's
            // "first actionable row" rule, same family)
            SelectedSlot = m.Slots.FindIndex(s => !s.matched);
            if (SelectedSlot < 0 && m.Slots.Count > 0) SelectedSlot = 0;
        }

        public void ClickSlot(int slot)
        {
            slot = Math.Clamp(slot, 0, Math.Max(0, Model.Slots.Count - 1));
            if (slot == SelectedSlot) return;
            // TEST-INJECTION ONLY (uia-hex-check negative): the click is
            // accepted but the cursor never moves — proves the caret
            // assertions have teeth. Never set in product use.
            if (Environment.GetEnvironmentVariable("REACMP_HEX_NEG") == "1") return;
            SelectedSlot = slot;
            int row = slot / 16;
            if (row < TopRow) TopRow = row;
            else if (row >= TopRow + VisibleRows) TopRow = Math.Max(0, row - VisibleRows / 2);
            Raise();
        }

        public void Scroll(int notches)
        {
            int max = Math.Max(0, Model.RowCount - 1);
            TopRow = Math.Clamp(TopRow - notches * 3, 0, max);
            Raise();
        }
    }

    /// <summary>Owner-draw hex editor pane (left/right). No UIA peer: the
    /// skeleton's THexEditor container keeps the tree identical and the pane
    /// content stays out of the control view (BC-measured; D3 hex rows are a
    /// recorded follow-up).</summary>
    internal sealed class HexPaneView : FrameworkElement
    {
        readonly HexViewState V;
        readonly bool IsLeft;
        readonly PaneStyle S;
        static readonly Typeface Face = TextPaneView.DiffFace;
        const double FontSizePx = 11;
        double CharW = -1;
        // per-byte cell metrics derived from our own face (biaoxian self-design;
        // the STRUCTURE — 2x8 groups + ascii — is the measured contract)
        double ByteW;      // "XX " advance
        double GroupGap;   // extra after byte 8
        double AsciiPitch; // ascii char advance

        public HexPaneView(HexViewState v, bool isLeft, PaneStyle s)
        { V = v; IsLeft = isLeft; S = s; v.Changed += () => InvalidateVisual(); Focusable = true; }

        byte? ByteAt(int slot) => IsLeft ? V.Model.Slots[slot].l : V.Model.Slots[slot].r;

        /// <summary>The side's own byte offset shown in the offset column:
        /// count of this side's bytes before the row (measured: per-side
        /// offsets; blank when the row is fully empty for this side —
        /// unmeasured edge, self-design).</summary>
        int SideOffset(int row)
        {
            int n = 0;
            for (int k = 0; k < row * 16 && k < V.Model.Slots.Count; k++)
                if (ByteAt(k) != null) n++;
            return n;
        }

        // same unbounded-desired model as TextPaneView: the pane lays out the
        // whole document (rows x measured pitch) and paints the shared
        // viewport into its surface top; the editor slot clips it.
        protected override Size MeasureOverride(Size availableSize)
        {
            double w = double.IsInfinity(availableSize.Width) ? 400 : availableSize.Width;
            double h = V.Model.RowCount * 17.5;
            return new Size(w, h);
        }

        protected override void OnRender(DrawingContext dc)
        {
            double pitch = 17.5;                 // measured row pitch (§6.19)
            double w = ActualWidth, h = ActualHeight;
            if (w <= 0 || h <= 0) return;
            if (CharW < 0)
            {
                CharW = new FormattedText("00000000", CultureInfo.CurrentCulture,
                    FlowDirection.LeftToRight, Face, FontSizePx,
                    new SolidColorBrush(HexPalette.Ink), 1.0).WidthIncludingTrailingWhitespace / 8.0;
                ByteW = 2 * CharW + 4;
                GroupGap = 10;
                AsciiPitch = CharW + 0.6;
            }
            V.VisibleRows = Math.Max(1, (int)(h / pitch));
            dc.DrawRectangle(new SolidColorBrush(S.LeftBase), null, new Rect(0, 0, w, h));
            double offX = 6;
            double hexX = offX + 8 * CharW + 14;
            double asciiX = hexX + 8 * ByteW + GroupGap + 8 * ByteW + GroupGap;
            var inkOff = new SolidColorBrush(HexPalette.OffsetInk);
            var ink = new SolidColorBrush(HexPalette.Ink);
            var red = new SolidColorBrush(HexPalette.ChangedText);
            var band = new SolidColorBrush(HexPalette.ChangedBand);
            var hatchPen = new Pen(new SolidColorBrush(HexPalette.Hatch), 1);
            var caret = new SolidColorBrush(HexPalette.Caret);
            int top = Math.Max(0, V.TopRow);
            for (int j = 0; j < V.VisibleRows + 1; j++)
            {
                int row = top + j;
                double y = j * pitch;
                if (y >= h) break;
                int s0 = row * 16;
                bool sideHasAny = Enumerable.Range(s0, Math.Min(16, V.Model.Slots.Count - s0))
                    .Any(k => k >= 0 && ByteAt(k) != null);
                if (s0 >= V.Model.Slots.Count || !sideHasAny)
                {
                    // beyond this side's data: full-width hatch band (the
                    // measured partial-row hatch, extended to whole rows)
                    if (s0 < 16 * V.Model.RowCount || !sideHasAny)
                        DrawHatch(dc, hatchPen, 0, y, w, pitch);
                    continue;
                }
                // offset (side's own byte index, 8 hex digits, gray)
                var off = new FormattedText(SideOffset(row).ToString("X8"),
                    CultureInfo.CurrentCulture, FlowDirection.LeftToRight, Face,
                    FontSizePx, inkOff, 1.0);
                dc.DrawText(off, new Point(offX, y + (pitch - off.Height) / 2));
                // hex zone: 2 x 8 groups
                for (int g = 0; g < 2; g++)
                {
                    for (int i = 0; i < 8; i++)
                    {
                        int slot = s0 + g * 8 + i;
                        double x = hexX + g * GroupGap + g * 8 * ByteW + i * ByteW;
                        if (slot >= V.Model.Slots.Count) { DrawHatch(dc, hatchPen, x, y, ByteW, pitch); continue; }
                        var b = ByteAt(slot);
                        if (b == null) { DrawHatch(dc, hatchPen, x, y, ByteW, pitch); continue; }
                        bool bad = !V.Model.Slots[slot].matched;
                        if (bad)
                            dc.DrawRectangle(band, null, new Rect(x - 1, y + 1, ByteW - 1, pitch - 2));
                        var ft = new FormattedText(b.Value.ToString("X2"),
                            CultureInfo.CurrentCulture, FlowDirection.LeftToRight, Face,
                            FontSizePx, bad ? red : ink, 1.0);
                        dc.DrawText(ft, new Point(x, y + (pitch - ft.Height) / 2));
                    }
                }
                // ascii zone: 16 chars, 2 x 8 groups
                for (int g = 0; g < 2; g++)
                {
                    for (int i = 0; i < 8; i++)
                    {
                        int slot = s0 + g * 8 + i;
                        double x = asciiX + g * GroupGap + g * 8 * AsciiPitch + i * AsciiPitch;
                        if (slot >= V.Model.Slots.Count) { DrawHatch(dc, hatchPen, x, y, AsciiPitch, pitch); continue; }
                        var b = ByteAt(slot);
                        if (b == null) { DrawHatch(dc, hatchPen, x, y, AsciiPitch, pitch); continue; }
                        bool bad = !V.Model.Slots[slot].matched;
                        if (bad)
                            dc.DrawRectangle(band, null, new Rect(x - 1, y + 1, AsciiPitch, pitch - 2));
                        char ch = b >= 0x20 && b <= 0x7E ? (char)b : '.';
                        var ft = new FormattedText(ch.ToString(),
                            CultureInfo.CurrentCulture, FlowDirection.LeftToRight, Face,
                            FontSizePx, bad ? red : ink, 1.0);
                        dc.DrawText(ft, new Point(x, y + (pitch - ft.Height) / 2));
                        // caret = cyan block on the selected slot's ascii cell
                        if (slot == V.SelectedSlot)
                            dc.DrawRectangle(caret, null, new Rect(x - 1, y + 1, 3, pitch - 2));
                    }
                }
            }
        }

        static void DrawHatch(DrawingContext dc, Pen pen, double x, double y, double w, double hh)
        {
            // measured: diagonal light-gray lines on the pane base (same
            // dianzhen/hatch semantics as the text view's empty side)
            dc.PushClip(new RectangleGeometry(new Rect(x, y, w, hh)));
            for (double d = -hh; d < w; d += 6)
                dc.DrawLine(pen, new Point(x + d, y + hh), new Point(x + d + hh, y));
            dc.Pop();
        }

        protected override void OnMouseLeftButtonDown(MouseButtonEventArgs e)
        {
            base.OnMouseLeftButtonDown(e);
            double pitch = 17.5;
            var p = e.GetPosition(this);
            if (CharW < 0) return;
            double offX = 6;
            double hexX = offX + 8 * CharW + 14;
            double asciiX = hexX + 8 * ByteW + GroupGap + 8 * ByteW + GroupGap;
            int row = V.TopRow + (int)(p.Y / pitch);
            int idx = -1;
            if (p.X >= hexX && p.X < asciiX)
            {
                double rx = p.X - hexX;
                int g = (int)(rx / (8 * ByteW + GroupGap));
                if (g > 1) g = 1;
                int i = (int)((rx - g * (8 * ByteW + GroupGap)) / ByteW);
                if (i >= 0 && i < 8) idx = g * 8 + i;
            }
            else if (p.X >= asciiX)
            {
                double rx = p.X - asciiX;
                int g = (int)(rx / (8 * AsciiPitch + GroupGap));
                if (g > 1) g = 1;
                int i = (int)((rx - g * (8 * AsciiPitch + GroupGap)) / AsciiPitch);
                if (i >= 0 && i < 8) idx = g * 8 + i;
            }
            if (idx >= 0)
            {
                int slot = row * 16 + idx;
                if (slot < V.Model.Slots.Count) V.ClickSlot(slot);
            }
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
            if (V.SelectedSlot < 0) return;
            int s = V.SelectedSlot;
            switch (e.Key)
            {
                case Key.Right: s = Math.Min(V.Model.Slots.Count - 1, s + 1); break;
                case Key.Left: s = Math.Max(0, s - 1); break;
                case Key.Down: s = Math.Min(V.Model.Slots.Count - 1, s + 16); break;
                case Key.Up: s = Math.Max(0, s - 16); break;
                default: return;
            }
            V.ClickSlot(s);
            e.Handled = true;
        }
    }

}
