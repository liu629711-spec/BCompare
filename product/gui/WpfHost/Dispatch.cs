// View dispatch (U-gui-5): route a left/right path pair to a session view using
// the measured cell table from spec "dispatch". Every cell cites live evidence;
// unmeasured inputs use the measured fallback (.zqq probe -> Text Compare).
// Task-only views have NO file route by measurement — dispatch must reject them.

using System;
using System.Collections.Generic;
using System.IO;

namespace ReaCompare.Gui
{
    internal sealed class DispatchCell
    {
        public string Kind = "ext";        // ext | dirs
        public List<string> Match = new(); // lowercase extensions for kind=ext
        public string View = "";
        public string Evidence = "";
    }

    internal sealed class DispatchTable
    {
        public List<DispatchCell> Cells = new();
        public DispatchCell Fallback = new();
        public List<string> TaskOnly = new();
        public List<string> HintExtPicture = new();
        // D1 (docs/20, 2026-10-22): the MEASURED BC title structure
        // '{L} <--> {R} - {View} - <product>' is inherited as a capability;
        // the brand token is ours. Load() swaps the Oracle brand out.
        public string TitleRule = "{L} <--> {R} - {View} - LiuCompare";

        public static DispatchTable Load(System.Text.Json.JsonElement r)
        {
            var t = new DispatchTable();
            foreach (var c in r.GetProperty("cells").EnumerateArray())
                t.Cells.Add(ReadCell(c));
            t.Fallback = ReadCell(r.GetProperty("fallback"));
            foreach (var s in r.GetProperty("task_only").EnumerateArray())
                t.TaskOnly.Add(s.GetString());
            if (r.TryGetProperty("hint_ext_picture", out var h))
                foreach (var s in h.EnumerateArray()) t.HintExtPicture.Add(s.GetString());
            if (r.TryGetProperty("title_rule", out var tr))
                // measured template kept; brand token replaced per D1
                t.TitleRule = tr.GetString().Replace("Beyond Compare", "LiuCompare");
            return t;
        }

        private static DispatchCell ReadCell(System.Text.Json.JsonElement c)
        {
            var cell = new DispatchCell
            {
                Kind = c.TryGetProperty("kind", out var kd) ? kd.GetString() ?? "ext" : "ext",
                View = c.GetProperty("view").GetString(),
                Evidence = c.TryGetProperty("evidence", out var e) ? e.GetString() ?? "" : "",
            };
            if (c.TryGetProperty("match", out var mm))
                foreach (var m in mm.EnumerateArray())
                    cell.Match.Add(m.GetString().ToLowerInvariant());
            return cell;
        }

        /// <summary>Measured BC rule: session type depends on the file extension
        /// of the opened pair (or both-dirs); no extension is case-insensitive and
        /// unknown input falls back to Text Compare.</summary>
        public (string view, string via) Dispatch(string left, string right)
        {
            bool lDir = Directory.Exists(left), rDir = Directory.Exists(right);
            if (lDir && rDir)
                foreach (var c in Cells)
                    if (c.Kind == "dirs") return (c.View, "dirs");
            string ext = Path.GetExtension(left).ToLowerInvariant();
            if (!string.IsNullOrEmpty(ext))
                foreach (var c in Cells)
                    if (c.Kind == "ext" && c.Match.Contains(ext)) return (c.View, "ext:" + ext);
            return (Fallback.View, "fallback");
        }

        public string Title(string left, string right, string view)
            => TitleRule.Replace("{L}", Path.GetFileName(left))
                        .Replace("{R}", Path.GetFileName(right))
                        .Replace("{View}", view);
    }
}
