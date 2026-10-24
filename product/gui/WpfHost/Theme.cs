// Theme mechanism (docs/20 §6 step 3, D5: light+dark in MVP; §3 P5: hue
// semantics inherited from the measured reference, lightness ours).
//
// Design rules this file enforces:
//  - An ADDITIVE overlay: a theme file may set only the keys it wants;
//    every absent key keeps its MEASURED source value (colors.json /
//    filter-map.json). light.json sets nothing, so the light theme is
//    provably a no-op — the existing tint/filter/self-golden gates keep
//    their measured expectations untouched.
//  - Dark values carry their design rule + WCAG math in dark.json itself;
//    the code never hardcodes a color (same "each constant has a source"
//    discipline as PaneStyle.Load).
//  - Geometry is NOT themed: row pitch/gutter/body x stay the measured
//    lattice (docs/20 §3: BC layout knowledge is the reference).

using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Windows.Media;

namespace ReaCompare.Gui
{
    internal sealed class Theme
    {
        public string Name = "light";
        // optional overrides; presence == the theme file set that key
        public Dictionary<string, (Color l, Color r)> StatusTint; // per-side
        public Color? LeftBase, RightBase, LeftInk, RightInk, GutterBg, GutterDigits;
        public Color? LeftHatch, RightHatch;
        public Color? RadioSelected, RadioUnselected, WindowBg;
        // Toolbar text-button face (docs/21 B tier-1). dark.json's "toolbar"
        // key overrides; light.json sets nothing so the light face keeps the
        // ChromeElement defaults (self-design, annotated in docs/19 §6.21).
        public Color? ToolbarText, ToolbarHover, ToolbarPressed, ToolbarDivider;

        /// <summary>Resolve --theme to a file: a direct *.json path, or a bare
        /// name looked up in product/gui/themes/&lt;name&gt;.json (repo source dir;
        /// the csproj also copies themes/ next to the exe as a fallback).</summary>
        static string ResolvePath(string themeArg)
        {
            if (themeArg.EndsWith(".json", StringComparison.OrdinalIgnoreCase) && File.Exists(themeArg))
                return themeArg;
            var direct = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "themes", themeArg + ".json");
            if (File.Exists(direct)) return direct;
            // repo source layout: WpfHost/bin/Debug/net8.0-windows -> WpfHost/themes
            var src = Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,
                "..", "..", "..", "..", "themes", themeArg + ".json"));
            return File.Exists(src) ? src : null;
        }

        public static Theme Load(string themeArg)
        {
            var t = new Theme { Name = themeArg };
            var path = ResolvePath(themeArg);
            if (path == null) throw new Exception($"theme '{themeArg}': no json found");
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var r = doc.RootElement;
            Color C(JsonElement a) => Color.FromRgb(a[0].GetByte(), a[1].GetByte(), a[2].GetByte());

            if (r.TryGetProperty("pane_base", out var pb))
            { t.LeftBase = C(pb.GetProperty("left")); t.RightBase = C(pb.GetProperty("right")); }
            if (r.TryGetProperty("ink", out var ink))
            { t.LeftInk = C(ink.GetProperty("left")); t.RightInk = C(ink.GetProperty("right")); }
            if (r.TryGetProperty("gutter", out var gu))
            { t.GutterBg = C(gu.GetProperty("bg")); t.GutterDigits = C(gu.GetProperty("digits")); }
            if (r.TryGetProperty("status_rows", out var sr))
            {
                t.StatusTint = new Dictionary<string, (Color, Color)>();
                foreach (var kv in sr.EnumerateObject())
                    t.StatusTint[kv.Name] = (C(kv.Value.GetProperty("left")), C(kv.Value.GetProperty("right")));
            }
            if (r.TryGetProperty("hatch", out var ha))
            { t.LeftHatch = C(ha.GetProperty("left_stripe")); t.RightHatch = C(ha.GetProperty("right_stripe")); }
            if (r.TryGetProperty("radio", out var ra))
            { t.RadioSelected = C(ra.GetProperty("selected")); t.RadioUnselected = C(ra.GetProperty("unselected")); }
            if (r.TryGetProperty("window_bg", out var wb)) t.WindowBg = C(wb);
            if (r.TryGetProperty("toolbar", out var tk))
            {
                if (tk.TryGetProperty("text", out var tv)) t.ToolbarText = C(tv);
                if (tk.TryGetProperty("hover", out var hv)) t.ToolbarHover = C(hv);
                if (tk.TryGetProperty("pressed", out var pv)) t.ToolbarPressed = C(pv);
                if (tk.TryGetProperty("divider", out var dv)) t.ToolbarDivider = C(dv);
            }
            return t;
        }

        /// <summary>Overlay onto the MEASURED PaneStyle. Only keys the theme
        /// file declares are replaced; the theme may not invent a status key
        /// the measured file doesn't have (that would be designing blind).</summary>
        public void Apply(PaneStyle s)
        {
            if (LeftBase != null) s.LeftBase = LeftBase.Value;
            if (RightBase != null) s.RightBase = RightBase.Value;
            if (LeftInk != null) s.LeftInk = LeftInk.Value;
            if (RightInk != null) s.RightInk = RightInk.Value;
            if (GutterBg != null) s.GutterBg = GutterBg.Value;
            if (GutterDigits != null) s.GutterDigits = GutterDigits.Value;
            if (LeftHatch != null) s.LeftHatchStripe = LeftHatch.Value;
            if (RightHatch != null) s.RightHatchStripe = RightHatch.Value;
            if (StatusTint != null)
                foreach (var kv in StatusTint)
                    if (s.StatusTint.ContainsKey(kv.Key)) s.StatusTint[kv.Key] = kv.Value;
                    else throw new Exception($"theme '{Name}': status '{kv.Key}' is not in the measured model");
        }

        public void Apply(FilterMap m)
        {
            if (RadioSelected != null) m.Selected = RadioSelected.Value;
            if (RadioUnselected != null) m.Unselected = RadioUnselected.Value;
        }
    }
}
