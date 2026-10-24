// Text Merge view (docs/20 §6 feature 2; measured model docs/19 §6.15,
// edit/save semantics docs/19 §6.17 / extracted/live/textmerge-edit-en/
// merge-edit-findings.json, merge-to destination semantics docs/19 §6.18 /
// extracted/live/textmerge-to-en/merge-to-findings.json).
//
// Entry:
//   reacmp-gui --menu-spec spec.json --merge <Left> <Right> <Center> [<Out>] [--show]
// Positional order = BC's own merge command line (verified,
// help/command_line_reference.html); center = merge base. The 4th positional
// is the SAVE TARGET (measured Q1: its disk content is NEVER loaded — the
// output pane shows the auto-merge; measured Q2: nothing writes until an
// explicit save).
//
// Merge-to destination (measured §6.18): the radio row picks the Ctrl+S
// target — Left -> the left file, Right -> the right file, Other: -> the 4th
// arg (direct write) or, when unnamed (3-file form), a save dialog. The
// window title follows the destination file name; the path field next to
// 'Other:' shows the CURRENT destination path. 'Swap' exchanges the side
// files and re-materializes the output (band attribution swaps).
//
// Pane model (all measured):
//   Take toolbar: Conflict / Left / Center / Right / Next Conflict /
//   Prev Conflict (UIA names verbatim)
//   three SOURCE panes side by side, READ-ONLY ('Editing disabled' footer is
//   drawn; exactly one editor lacks it = the output, §6.17 editable_pane_rule)
//   'Merge to:' radio row (Left/Right/Other:, default Other)
//   OUTPUT pane below: a COMPACT editable document (not band-aligned):
//     initial content = per-section materialization (equal/take -> that
//     side's lines; unresolved conflict -> CENTER lines — measured: the saved
//     file = base's 8 lines + the typed marker, PRESETPANE_* never appeared)
//     resolution bands: took-left (213,255,255) / took-right (248,227,255) /
//     unresolved conflict red (255,227,227), all from merge-palette.json
//   status line: engine counts ('# N conflict section(s)' / 'N difference
//     section(s)') — the GUI NEVER re-classifies
//
// Save bytes (measured): UTF-8 no BOM, '\n'-joined, NO forced trailing
// newline (OUT_after_ctrl_s was '...eight\nZZEDITMARKER7' verbatim).
//
// Source-pane shared cursor/viewport stays as tier-1 (docs/19 §6.12 family);
// the output document has its own caret + scroll (measured: each pane footer
// is independent, '1: 1').

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace ReaCompare.Gui
{
    internal static class MergeMode
    {
        public static int Run(string specPath, string mLeft, string mRight, string mCenter,
                              string mOut, string ledgerPath, bool show, string enginePath,
                              string colorsPath, string themeArg)
        {
            if (mLeft == null || mRight == null || mCenter == null)
            {
                Console.Error.WriteLine("usage: reacmp-gui --menu-spec spec.json --merge <Left> <Right> <Center> [<Out>] [--dump ledger.json] [--show]");
                return 2;
            }
            string colors = colorsPath ?? MenuMode.DefaultColorsPathPublic();
            if (!File.Exists(colors))
            { Console.Error.WriteLine($"ENGINE: colors.json not found: {colors}"); return 4; }
            PaneStyle style;
            Theme theme = null;
            try { style = PaneStyle.Load(colors); }
            catch (Exception e) { Console.Error.WriteLine("STYLE-FAIL: " + e.Message); return 4; }
            if (themeArg != null)
            {
                try { theme = Theme.Load(themeArg); }
                catch (Exception e) { Console.Error.WriteLine("THEME-FAIL: " + e.Message); return 4; }
                theme?.Apply(style);
            }

            string exe = enginePath ?? ReacmpEngine.DefaultExe();
            if (exe == null || !File.Exists(exe))
            { Console.Error.WriteLine("ENGINE: reacmp.exe not found (set --engine or REACMP)"); return 4; }
            string jsonOut = Path.Combine(Path.GetTempPath(), $"reacmp-merge-{Guid.NewGuid():N}.json");
            MergeModel model;
            try
            {
                var psi = new System.Diagnostics.ProcessStartInfo(exe,
                    $"--merge3 \"{Path.GetFullPath(mLeft)}\" \"{Path.GetFullPath(mRight)}\" \"{Path.GetFullPath(mCenter)}\" \"{jsonOut}\"")
                {
                    UseShellExecute = false, RedirectStandardError = true, CreateNoWindow = true,
                };
                int code; string err;
                using (var p = System.Diagnostics.Process.Start(psi))
                {
                    err = p.StandardError.ReadToEnd();
                    p.WaitForExit();
                    code = p.ExitCode;
                }
                if (code != 0 || !File.Exists(jsonOut))
                    throw new InvalidOperationException($"reacmp --merge3 exit {code}: {(err ?? "").Trim()}");
                model = MergeModel.Load(jsonOut, mLeft, mRight, mCenter);
            }
            catch (Exception e)
            {
                Console.Error.WriteLine("ENGINE-FAIL: " + e.Message);
                return 4;
            }
            finally { try { File.Delete(jsonOut); } catch { } }

            Console.WriteLine($"MERGE: {model.Sections.Count} sections, " +
                $"{model.DifferenceSections} difference, {model.ConflictSections} conflict (engine)");

            var bandRows = MergeGrid.BuildSourceRows(model);
            var state = new MergeState(model, bandRows) { OtherPath = mOut };

            if (ledgerPath != null)
            {
                var opts = new JsonSerializerOptions { WriteIndented = true };
                File.WriteAllText(ledgerPath, JsonSerializer.Serialize(new Dictionary<string, object>
                {
                    ["view"] = "Text Merge",
                    ["counts"] = new Dictionary<string, object>
                    {
                        ["difference_sections"] = model.DifferenceSections,
                        ["conflict_sections"] = model.ConflictSections,
                    },
                    ["sections"] = model.Sections.Select(s => new Dictionary<string, object>
                    {
                        ["kind"] = s.KindStr, ["base"] = new[] { s.B0, s.B1 },
                        ["left"] = new[] { s.L0, s.L1 }, ["right"] = new[] { s.R0, s.R1 },
                        ["output_source"] = s.OutputSource,
                    }).ToList(),
                    ["output_document_initial"] = state.Doc,
                }, opts));
                Console.WriteLine($"merge ledger -> {ledgerPath}");
            }

            if (show)
            {
                var win = BuildWindow(state, style, mCenter, mOut);
                var app = new Application();
                win.Show();
                app.Run(win);
            }
            return 0;
        }

        static Window BuildWindow(MergeState state, PaneStyle style, string center, string outTarget)
        {
            var dock = new DockPanel { LastChildFill = true };

            // ---- toolbar band: Take group (measured UIA names + widths) ----
            // Swap joins the bar (measured: the merge toolbar carries Swap;
            // menu Session > Swap Sides is the same action, docs/19 §6.18).
            var bar = new StackPanel { Orientation = Orientation.Horizontal };
            Button Mk(string name, Action act, int width)
            {
                var b = new Button { Content = name, Width = width, Height = 30, Margin = new Thickness(2, 4, 0, 4) };
                AutomationProperties.SetName(b, name);
                b.Click += (s, e) => act();
                return b;
            }
            bar.Children.Add(Mk("Conflict", () => state.Take("conflict"), 59));
            bar.Children.Add(Mk("Left", () => state.Take("left"), 59));
            bar.Children.Add(Mk("Center", () => state.Take("center"), 59));
            bar.Children.Add(Mk("Right", () => state.Take("right"), 59));
            bar.Children.Add(Mk("Next Conflict", () => state.StepConflict(+1), 86));
            bar.Children.Add(Mk("Prev Conflict", () => state.StepConflict(-1), 84));
            bar.Children.Add(Mk("Swap", () => state.SwapSides(), 59));
            DockPanel.SetDock(bar, Dock.Top);
            dock.Children.Add(bar);

            // ---- status line (measured position: bottom; counts engine-side) ----
            // direct event subscription, NOT a WPF Binding (the §6.16 lesson:
            // a Binding on a non-INPC source freezes the text).
            var status = new TextBlock
            {
                Margin = new Thickness(8, 4, 8, 4),
                Foreground = new SolidColorBrush(style.LeftInk),
                Text = state.StatusText,
            };
            state.Changed += () => status.Text = state.StatusText;
            DockPanel.SetDock(status, Dock.Bottom);
            dock.Children.Add(status);

            // ---- center: 3 source panes / merge-to row / output doc ----
            var outer = new Grid();
            outer.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
            outer.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            outer.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });

            var srcRow = new Grid();
            for (int i = 0; i < 3; i++)
                srcRow.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            var pvLeft = new MergePaneView(state, "left", style);
            var pvCenter = new MergePaneView(state, "center", style);
            var pvRight = new MergePaneView(state, "right", style);
            Grid.SetColumn(pvLeft, 0); Grid.SetColumn(pvCenter, 1); Grid.SetColumn(pvRight, 2);
            srcRow.Children.Add(pvLeft); srcRow.Children.Add(pvCenter); srcRow.Children.Add(pvRight);
            Grid.SetRow(srcRow, 0);
            outer.Children.Add(srcRow);

            // ---- measured radio trio + destination path field ----
            // §6.18: 'Merge to: [Left] [Right] [Other:] <path>' — the field
            // shows the CURRENT destination path (switching to Left rewrites
            // it to the left file path); the radio picks the Ctrl+S target.
            // Read-only display + field editability per side unprobed
            // (表现自设计 note in docs/19 §6.18).
            var radioRow = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(4, 2, 0, 2) };
            radioRow.Children.Add(new TextBlock { Text = "Merge to:", Margin = new Thickness(4, 0, 6, 0), VerticalAlignment = VerticalAlignment.Center });
            var destField = new TextBlock
            {
                Margin = new Thickness(8, 0, 4, 0),
                VerticalAlignment = VerticalAlignment.Center,
                Foreground = new SolidColorBrush(style.GutterDigits),
                Text = state.DestPath() ?? "",
            };
            // no explicit AutomationProperties.Name: the path TEXT is the UIA
            // name (the merge-to gate asserts on the exact destination path)
            foreach (var label in new[] { "Left", "Right", "Other:" })
            {
                var side = label == "Left" ? "left" : label == "Right" ? "right" : "other";
                var rb = new RadioButton { Content = label, GroupName = "mergeto", IsChecked = label == "Other:", Margin = new Thickness(4, 0, 8, 0), VerticalAlignment = VerticalAlignment.Center };
                AutomationProperties.SetName(rb, label);
                rb.Checked += (s, e) => state.SetMergeTo(side);
                radioRow.Children.Add(rb);
            }
            radioRow.Children.Add(destField);
            state.Changed += () => destField.Text = state.DestPath() ?? "";
            Grid.SetRow(radioRow, 1);
            outer.Children.Add(radioRow);

            var pvOut = new MergeOutputView(state, style);
            Grid.SetRow(pvOut, 2);
            outer.Children.Add(pvOut);

            dock.Children.Add(outer);

            // measured titles: '{destination basename} - Text Merge - <brand>'
            // — the title FOLLOWS the Merge to radio (§6.18: out.txt ->
            // left.txt the moment Left is picked); Other-without-path falls
            // back to the center file name (3-file step0). Brand swapped per
            // D1 (structural inheritance only).
            var win = new Window
            {
                Title = $"{state.DestTitle()} - Text Merge - LiuCompare",
                Width = 1456,
                Height = 864,
                Content = dock,
            };
            state.Changed += () => win.Title = $"{state.DestTitle()} - Text Merge - LiuCompare";
            // EXPLICIT SAVE ONLY (measured Q2): open/edits/Take NEVER touch
            // the disk; Ctrl+S writes to the Merge-to DESTINATION (§6.18:
            // Left radio -> left file; named Other -> output file; unnamed
            // Other -> save dialog, measured 'Save File on File System As -
            // Output Side'). REACMP_MERGE_SAVE_NEG=1 is a
            // TEST-INJECTION ONLY (the save silently no-ops) proving the edit
            // gate's file-content assertions have teeth. Never set in use.
            win.PreviewKeyDown += (s, e) =>
            {
                if (e.Key == Key.S && (Keyboard.Modifiers & ModifierKeys.Control) != 0)
                {
                    e.Handled = true;
                    if (Environment.GetEnvironmentVariable("REACMP_MERGE_SAVE_NEG") == "1") return;
                    string path = state.DestPath();
                    if (path == null)
                    {
                        var dlg = new Microsoft.Win32.SaveFileDialog
                        {
                            FileName = Path.GetFileNameWithoutExtension(center),
                            DefaultExt = ".txt",
                            Filter = "Text files (*.txt)|*.txt|All files (*.*)|*.*",
                        };
                        if (dlg.ShowDialog(win) != true) return;
                        path = dlg.FileName;
                    }
                    try
                    {
                        // measured bytes: UTF-8 no BOM, '\n'-joined, NO forced
                        // trailing newline (§6.17 OUT_after_ctrl_s)
                        File.WriteAllText(path, string.Join("\n", state.Doc), new UTF8Encoding(false));
                        state.MarkSaved(path);
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show(win, "SAVE-FAIL: " + ex.Message, "LiuCompare");
                    }
                }
            };
            return win;
        }
    }

    /// <summary>Engine section record (parsed from --merge3 JSON; the GUI
    /// never re-classifies).</summary>
    internal sealed class MergeSection
    {
        public string KindStr = "";        // equal | take-left | take-right | conflict
        public int B0, B1, L0, L1, R0, R1;
        public string OutputSource = "center";
    }

    internal sealed class MergeModel
    {
        public List<string> Left = new(), Center = new(), Right = new();
        public List<MergeSection> Sections = new();
        public int DifferenceSections, ConflictSections;
        public string LeftPath, RightPath, CenterPath;

        public static MergeModel Load(string jsonPath, string left, string right, string center)
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(jsonPath));
            var r = doc.RootElement;
            if (r.GetProperty("kind").GetString() != "reacmp-merge3/1")
                throw new InvalidOperationException("unexpected merge document kind");
            var m = new MergeModel { LeftPath = left, RightPath = right, CenterPath = center };
            var lines = r.GetProperty("lines");
            foreach (var e in lines.GetProperty("left").EnumerateArray()) m.Left.Add(e.GetString());
            foreach (var e in lines.GetProperty("center").EnumerateArray()) m.Center.Add(e.GetString());
            foreach (var e in lines.GetProperty("right").EnumerateArray()) m.Right.Add(e.GetString());
            var counts = r.GetProperty("counts");
            m.DifferenceSections = counts.GetProperty("difference_sections").GetInt32();
            m.ConflictSections = counts.GetProperty("conflict_sections").GetInt32();
            foreach (var s in r.GetProperty("sections").EnumerateArray())
            {
                var sec = new MergeSection { KindStr = s.GetProperty("kind").GetString() };
                sec.B0 = s.GetProperty("base")[0].GetInt32(); sec.B1 = s.GetProperty("base")[1].GetInt32();
                sec.L0 = s.GetProperty("left")[0].GetInt32(); sec.L1 = s.GetProperty("left")[1].GetInt32();
                sec.R0 = s.GetProperty("right")[0].GetInt32(); sec.R1 = s.GetProperty("right")[1].GetInt32();
                sec.OutputSource = s.GetProperty("output_source").GetString();
                m.Sections.Add(sec);
            }
            return m;
        }
    }

    /// <summary>Source-pane band row (tier-1 model unchanged): one visual row
    /// per band line across the three READ-ONLY panes; shorter sides pad
    /// (measured).</summary>
    internal sealed class MergeBandRow
    {
        public int SectionIndex;
        public string Kind = "";
        public int? LeftLine, CenterLine, RightLine;
    }

    internal static class MergeGrid
    {
        public static List<MergeBandRow> BuildSourceRows(MergeModel m)
        {
            var rows = new List<MergeBandRow>();
            for (int si = 0; si < m.Sections.Count; si++)
            {
                var s = m.Sections[si];
                int nb = s.B1 - s.B0, nl = s.L1 - s.L0, nr = s.R1 - s.R0;
                int h = Math.Max(nb, Math.Max(nl, nr));
                if (h == 0) continue;
                for (int k = 0; k < h; k++)
                    rows.Add(new MergeBandRow
                    {
                        SectionIndex = si,
                        Kind = s.KindStr,
                        LeftLine = k < nl ? s.L0 + k : (int?)null,
                        CenterLine = k < nb ? s.B0 + k : (int?)null,
                        RightLine = k < nr ? s.R0 + k : (int?)null,
                    });
            }
            return rows;
        }

        /// <summary>Initial COMPACT output document (measured Q1: the output
        /// pane shows the auto-merge, never the target file's disk content).
        /// Mechanical line selection per engine section — no re-classify.</summary>
        public static (List<string> doc, List<(int start, int end)> bounds) BuildOutputDoc(MergeModel m)
        {
            var doc = new List<string>();
            var bounds = new List<(int, int)>();
            for (int si = 0; si < m.Sections.Count; si++)
            {
                var s = m.Sections[si];
                var (list, a, b) = SourceRun(m, s, InitialResolution(s));
                int start = doc.Count;
                for (int j = a; j < b; j++) doc.Add(list[j]);
                bounds.Add((start, doc.Count));
            }
            return (doc, bounds);
        }

        public static string InitialResolution(MergeSection s) => s.KindStr switch
        {
            "take-left" => "left",
            "take-right" => "right",
            // measured: an unresolved conflict holds the CENTER content
            _ => "center",
        };

        public static (List<string> list, int a, int b) SourceRun(MergeModel m, MergeSection s, string side)
            => side switch
            {
                "left" => (m.Left, s.L0, s.L1),
                "right" => (m.Right, s.R0, s.R1),
                _ => (m.Center, s.B0, s.B1),
            };
    }

    /// <summary>Shared merge state: source band cursor/viewport + the output
    /// DOCUMENT (editable lines, per-section doc bounds, caret).</summary>
    internal sealed class MergeState
    {
        public readonly MergeModel Model;
        public List<MergeBandRow> BandRows;   // rebuilt by SwapSides
        public int SelectedBand = -1;          // source cursor (band row index)
        public int TopBand;
        public int VisibleBands = 40;

        public List<string> Doc;               // output document lines
        public readonly List<(int start, int end)> DocBounds;  // per section
        public int CaretRow, CaretCol;
        public int TopOut;
        public int VisibleOut = 40;
        public bool Dirty;
        public string SavedPath;

        // "Merge to defines the destination file of the merge results"
        // (help/sessiontextmergespecs.html). View-level measured behavior
        // (docs/19 §6.18, merge-to-findings.json): the radio picks the
        // Ctrl+S target; the window title follows the destination file name;
        // the path field next to 'Other:' always shows the CURRENT
        // destination path; switching never re-renders panes or counts.
        public string MergeTo = "other";       // left | right | other
        public string OtherPath;               // 4th CLI arg; null in 3-file form

        public event Action Changed;
        public void Raise() => Changed?.Invoke();

        /// <summary>Current save destination path (null = unnamed Other in
        /// the 3-file form -> Ctrl+S shows a save dialog, measured C2:
        /// named side files save with NO dialog).</summary>
        public string DestPath() => MergeTo switch
        {
            "left" => Model.LeftPath,
            "right" => Model.RightPath,
            _ => OtherPath,
        };

        /// <summary>Measured title rule: basename(current destination);
        /// Other-without-path falls back to basename(center) (3-file step0
        /// title = 'base.txt - Text Merge').</summary>
        public string DestTitle() =>
            Path.GetFileName(DestPath() ?? Model.CenterPath);

        public void SetMergeTo(string side)
        {
            // TEST-INJECTION ONLY (uia-text-merge-to-check negative): the
            // radio is accepted but the destination never moves — proves the
            // title/path assertions have teeth. Never set in product use.
            if (Environment.GetEnvironmentVariable("REACMP_MERGETO_NEG") == "1")
                return;
            if (MergeTo == side) return;
            MergeTo = side;
            Raise();
        }

        // section -> explicitly taken side (measured Take semantics); absent =
        // engine-initial resolution
        readonly Dictionary<int, string> Taken = new();

        public MergeState(MergeModel m, List<MergeBandRow> bandRows)
        {
            Model = m;
            BandRows = bandRows;
            var (doc0, bounds0) = MergeGrid.BuildOutputDoc(m);
            Doc = doc0;
            DocBounds = bounds0;
            // measured: a fresh view positions at the first actionable section
            int first = bandRows.FindIndex(r => r.Kind == "conflict");
            if (first < 0) first = bandRows.FindIndex(r => r.Kind != "equal");
            SelectedBand = first < 0 ? 0 : first;
            CaretRow = 0; CaretCol = 0;
        }

        public string StatusText
        {
            get
            {
                int unresolved = 0;
                for (int si = 0; si < Model.Sections.Count; si++)
                    if (Model.Sections[si].KindStr == "conflict" && DocRes(si) == "center")
                        unresolved++;
                var base_ = unresolved > 0
                    ? $"# {unresolved} conflict section(s)   {Model.DifferenceSections} difference section(s)"
                    : $"{Model.DifferenceSections} difference section(s)";
                // '[modified]' marker: presentation self-designed (BC signals
                // the modified state outside the measured statusbar cells)
                return Dirty ? base_ + "   [modified]" : base_;
            }
        }

        public string DocRes(int si)
        {
            var s = Model.Sections[si];
            if (s.KindStr == "equal") return "center";
            return Taken.TryGetValue(si, out var t) ? t : MergeGrid.InitialResolution(s);
        }

        /// <summary>Take a side on the section under the source cursor (BC:
        /// "Takes selected lines or current section from indicated side").
        /// Replaces the section's DOC block with the side's run — edits inside
        /// that block are overwritten (section semantics), edits elsewhere
        /// survive. 'conflict' re-opens back to center (measured unresolved).</summary>
        public void Take(string side)
        {
            if (SelectedBand < 0 || SelectedBand >= BandRows.Count) return;
            int si = BandRows[SelectedBand].SectionIndex;
            var s = Model.Sections[si];
            if (s.KindStr == "equal") return;
            // TEST-INJECTION ONLY (uia-text-merge-check negative): Take is
            // accepted but changes nothing — proves the resolution assertions
            // have teeth. Never set in product use.
            if (Environment.GetEnvironmentVariable("REACMP_MERGE_NEG") == "1")
                return;
            string res = side == "conflict" ? "center" : side;
            var (list, a, b) = MergeGrid.SourceRun(Model, s, res);
            var (bs, be) = DocBounds[si];
            int oldLen = be - bs, newLen = b - a;
            var newBlock = new List<string>();
            for (int j = a; j < b; j++) newBlock.Add(list[j]);
            Doc.RemoveRange(bs, oldLen);
            Doc.InsertRange(bs, newBlock);
            DocBounds[si] = (bs, bs + newLen);
            ShiftBounds(si, newLen - oldLen);
            if (side == "conflict") Taken.Remove(si); else Taken[si] = side;
            Dirty = true;
            Raise();
        }

        void ShiftBounds(int afterIdx, int delta)
        {
            if (delta == 0) return;
            for (int si = afterIdx + 1; si < DocBounds.Count; si++)
            {
                var (x, y) = DocBounds[si];
                DocBounds[si] = (x + delta, y + delta);
            }
        }

        /// <summary>Session &gt; Swap Sides (measured docs/19 §6.18: the
        /// physical toolbar 'Swap' click exchanges the side panes, center
        /// untouched, and the output re-materializes with band attribution
        /// swapped — took-left cyan ↔ took-right purple — content identical
        /// for a symmetric merge). Side manual edits restart as the fresh
        /// auto-merge (fresh-view measurement; 表现自设计: BC's edit
        /// preservation across swap is unprobed).</summary>
        public void SwapSides()
        {
            // TEST-INJECTION ONLY (uia-text-merge-to-check negative): Swap
            // accepted but sides never exchange. Never set in product use.
            if (Environment.GetEnvironmentVariable("REACMP_SWAP_NEG") == "1")
                return;
            var m = Model;
            (m.Left, m.Right) = (m.Right, m.Left);
            (m.LeftPath, m.RightPath) = (m.RightPath, m.LeftPath);
            foreach (var s in m.Sections)
            {
                (s.L0, s.R0) = (s.R0, s.L0);
                (s.L1, s.R1) = (s.R1, s.L1);
                s.KindStr = s.KindStr switch
                {
                    "take-left" => "take-right",
                    "take-right" => "take-left",
                    _ => s.KindStr,        // equal / conflict unchanged
                };
                if (s.OutputSource == "left") s.OutputSource = "right";
                else if (s.OutputSource == "right") s.OutputSource = "left";
            }
            var bandRows = MergeGrid.BuildSourceRows(m);
            var (doc0, bounds0) = MergeGrid.BuildOutputDoc(m);
            BandRows = bandRows;               // field is not readonly
            Doc = doc0;
            DocBounds.Clear();
            DocBounds.AddRange(bounds0);
            Taken.Clear();
            int first = bandRows.FindIndex(r => r.Kind == "conflict");
            if (first < 0) first = bandRows.FindIndex(r => r.Kind != "equal");
            SelectedBand = first < 0 ? 0 : first;
            TopBand = 0; TopOut = 0;
            CaretRow = 0; CaretCol = 0;
            Dirty = false;                     // doc == fresh auto-merge again
            Raise();
        }

        /// <summary>A doc edit inside section si changes its length; later
        /// sections shift. Equal-vs-take tints follow si, not content.</summary>
        void BoundsEdited(int si, int delta)
        {
            if (delta == 0) return;
            var (x, y) = DocBounds[si];
            DocBounds[si] = (x, y + delta);
            ShiftBounds(si, delta);
        }

        public void StepConflict(int delta)
        {
            var starts = new List<int>();
            for (int r = 0; r < BandRows.Count; r++)
                if (BandRows[r].Kind == "conflict" && (r == 0 || BandRows[r - 1].SectionIndex != BandRows[r].SectionIndex))
                    starts.Add(r);
            if (starts.Count == 0) return;
            int cur = SelectedBand;
            SelectedBand = delta > 0
                ? starts.FirstOrDefault(s => s > cur, starts[0])
                : Enumerable.Reverse(starts).FirstOrDefault(s => s < cur, starts[starts.Count - 1]);
            KeepBandVisible(SelectedBand);
            // bring the section's doc block into the output viewport too
            int si = BandRows[SelectedBand].SectionIndex;
            if (si < DocBounds.Count)
            {
                int row = DocBounds[si].start;
                if (row < TopOut) TopOut = row;
                else if (row >= TopOut + VisibleOut) TopOut = row;
            }
            Raise();
        }

        public void ClickBand(int viewportRow)
        {
            int src = TopBand + viewportRow;
            if (src < 0 || src >= BandRows.Count) return;
            SelectedBand = src;
            Raise();
        }

        public void ScrollBands(int notches)
        {
            TopBand = Math.Max(0, Math.Min(Math.Max(0, BandRows.Count - 1), TopBand - notches * 3));
            Raise();
        }

        public void KeepBandVisible(int r)
        {
            if (r < TopBand) TopBand = r;
            else if (r >= TopBand + VisibleBands) TopBand = Math.Max(0, r - VisibleBands / 2);
        }

        // ---- output document editing (measured: the ONE non-'Editing
        // disabled' pane is writable; save stays explicit, Q2) ----

        public int SectionAtDocRow(int row)
        {
            for (int si = 0; si < DocBounds.Count; si++)
                if (row < DocBounds[si].end) return si;
            return Math.Max(0, DocBounds.Count - 1);
        }

        public void InsertText(string text)
        {
            if (string.IsNullOrEmpty(text)) return;
            var clean = new string(text.Where(ch => ch >= ' ' || ch == '\t').ToArray());
            if (clean.Length == 0) return;
            if (CaretRow >= Doc.Count)
            {
                Doc.Add("");
                if (DocBounds.Count > 0) BoundsEdited(SectionAtDocRow(Doc.Count - 1), +1);
            }
            var line = Doc[CaretRow];
            CaretCol = Math.Clamp(CaretCol, 0, line.Length);
            Doc[CaretRow] = line.Substring(0, CaretCol) + clean + line.Substring(CaretCol);
            CaretCol += clean.Length;
            Dirty = true;
            Raise();
        }

        public void PressEnter()
        {
            if (CaretRow >= Doc.Count)
            {
                int si = SectionAtDocRow(Doc.Count - 1);
                Doc.Add("");
                BoundsEdited(si, +1);
                CaretRow = Doc.Count - 1; CaretCol = 0;
            }
            else
            {
                int si = SectionAtDocRow(CaretRow);
                var line = Doc[CaretRow];
                CaretCol = Math.Clamp(CaretCol, 0, line.Length);
                var rest = line.Substring(CaretCol);
                Doc[CaretRow] = line.Substring(0, CaretCol);
                Doc.Insert(CaretRow + 1, rest);
                BoundsEdited(si, +1);
                CaretRow++; CaretCol = 0;
            }
            KeepOutVisible(CaretRow);
            Dirty = true;
            Raise();
        }

        public void PressBackspace()
        {
            if (CaretCol > 0 && CaretRow < Doc.Count)
            {
                var line = Doc[CaretRow];
                Doc[CaretRow] = line.Remove(CaretCol - 1, 1);
                CaretCol--;
            }
            else if (CaretRow > 0 && CaretRow < Doc.Count)
            {
                int si = SectionAtDocRow(CaretRow - 1);
                var prev = Doc[CaretRow - 1];
                Doc[CaretRow - 1] = prev + Doc[CaretRow];
                Doc.RemoveAt(CaretRow);
                BoundsEdited(si, -1);
                CaretRow--; CaretCol = prev.Length;
            }
            Dirty = true;
            Raise();
        }

        public void MoveCaret(Key k)
        {
            switch (k)
            {
                case Key.Left:
                    if (CaretCol > 0 && CaretRow < Doc.Count) CaretCol--;
                    else if (CaretRow > 0) { CaretRow--; CaretCol = Doc[CaretRow].Length; }
                    break;
                case Key.Right:
                    if (CaretRow < Doc.Count && CaretCol < Doc[CaretRow].Length) CaretCol++;
                    else if (CaretRow + 1 < Doc.Count) { CaretRow++; CaretCol = 0; }
                    break;
                case Key.Up:
                    if (CaretRow > 0) CaretRow--;
                    break;
                case Key.Down:
                    if (CaretRow + 1 < Doc.Count) CaretRow++;
                    else if (Doc.Count > 0) CaretRow = Doc.Count;
                    break;
                case Key.Home: CaretCol = 0; break;
                case Key.End:
                    if (CaretRow < Doc.Count) CaretCol = Doc[CaretRow].Length;
                    break;
            }
            if (CaretRow < TopOut) TopOut = CaretRow;
            else if (CaretRow >= TopOut + VisibleOut) TopOut = CaretRow - VisibleOut + 1;
            Raise();
        }

        public void SetCaretFromClick(int row)
        {
            CaretRow = Math.Clamp(row, 0, Doc.Count);
            CaretCol = 0;
            Raise();
        }

        void KeepOutVisible(int r)
        {
            if (r < TopOut) TopOut = r;
            else if (r >= TopOut + VisibleOut) TopOut = r - VisibleOut + 1;
        }

        public void MarkSaved(string path)
        {
            Dirty = false; SavedPath = path; Raise();
        }

        /// <summary>Band tint for an output doc row (engine-side resolution +
        /// measured palette colors).</summary>
        public Color DocTint(int row)
        {
            var pal = MergePalette.C;
            if (row >= Doc.Count) return pal.Base;
            int si = SectionAtDocRow(row);
            var s = Model.Sections[si];
            string res = DocRes(si);
            if (s.KindStr == "equal") return pal.Base;
            return res switch
            {
                "left" => pal.OutLeft,
                "right" => pal.OutRight,
                // measured: unresolved conflict = red band holding center
                "center" => s.KindStr == "conflict" ? pal.Conflict : pal.Base,
                _ => pal.Base,
            };
        }
    }

    /// <summary>Merge palette, loaded STRICT from the measured probe artifact
    /// (extracted/live/textmerge-en/merge-palette.json, docs/19 §6.15).</summary>
    internal static class MergePalette
    {
        public sealed class Cols
        {
            public Color LeftBand, RightBand, OutLeft, OutRight, Conflict, Base, Void;
        }
        public static readonly Cols C = Load();

        static Cols Load()
        {
            string path = Path.Combine(MenuMode.RepoRoot(),
                "extracted", "live", "textmerge-en", "merge-palette.json");
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var t = doc.RootElement.GetProperty("tint_measured");
            Color Get(string k)
            {
                var a = t.GetProperty(k);
                return Color.FromRgb(a[0].GetByte(), a[1].GetByte(), a[2].GetByte());
            }
            var conflict = doc.RootElement.GetProperty("conflict_measured").GetProperty("output_band");
            return new Cols
            {
                LeftBand = Get("left_change_band"),
                RightBand = Get("right_change_band"),
                OutLeft = Get("output_took_left_band"),
                OutRight = Get("output_took_right_band"),
                Conflict = Color.FromRgb(conflict[0].GetByte(), conflict[1].GetByte(), conflict[2].GetByte()),
                Base = Get("equal_base"),
                Void = Get("void_rows_below_content"),
            };
        }
    }

    /// <summary>Owner-drawn READ-ONLY source pane (left/center/right). The
    /// 'Editing disabled' footer is drawn from the measured artifact — and
    /// this pane genuinely ignores text input (select/scroll only).</summary>
    internal sealed class MergePaneView : FrameworkElement
    {
        readonly MergeState V;
        readonly string Side; // left | center | right
        readonly PaneStyle S;
        static readonly Typeface Face = TextPaneView.DiffFace;
        const double FontSizePx = 11;

        public MergePaneView(MergeState v, string side, PaneStyle s)
        { V = v; Side = side; S = s; v.Changed += () => InvalidateVisual(); }

        static Color TintFor(MergeBandRow row, string side)
        {
            var pal = MergePalette.C;
            switch (row.Kind)
            {
                case "take-left": return side == "left" ? pal.LeftBand : pal.Base;
                case "take-right": return side == "right" ? pal.RightBand : pal.Base;
                case "conflict": return side == "left" ? pal.LeftBand : side == "right" ? pal.RightBand : pal.Base;
                default: return pal.Base;
            }
        }

        string TextAt(MergeBandRow row)
        {
            int? ln = Side switch { "left" => row.LeftLine, "center" => row.CenterLine, _ => row.RightLine };
            if (ln == null) return null;
            return Side switch
            {
                "left" => V.Model.Left[ln.Value],
                "center" => V.Model.Center[ln.Value],
                _ => V.Model.Right[ln.Value],
            };
        }

        protected override void OnRender(DrawingContext dc)
        {
            double pitch = S.RowPitch;
            double w = ActualWidth, h = ActualHeight;
            if (w <= 0 || h <= 0) return;
            var pal = MergePalette.C;
            V.VisibleBands = Math.Max(1, (int)(h / pitch));
            dc.DrawRectangle(new SolidColorBrush(pal.Base), null, new Rect(0, 0, w, h));
            int topRow = Math.Max(0, V.TopBand);
            int visRows = (int)(h / pitch) + 1;
            for (int j = 0; j < visRows; j++)
            {
                int k = topRow + j;
                double y = j * pitch;
                if (y >= h) break;
                if (k >= V.BandRows.Count)
                {
                    dc.DrawRectangle(new SolidColorBrush(pal.Void), null,
                        new Rect(0, y, w, Math.Min(pitch, h - y)));
                    continue;
                }
                var row = V.BandRows[k];
                var tint = TintFor(row, Side);
                if (tint != pal.Base)
                    dc.DrawRectangle(new SolidColorBrush(tint), null, new Rect(0, y, w, Math.Min(pitch, h - y)));
                string text = TextAt(row);
                if (text == null) continue;
                var ft = new FormattedText(text, CultureInfo.CurrentCulture,
                    FlowDirection.LeftToRight, Face, FontSizePx,
                    new SolidColorBrush(S.LeftInk), 1.0) { Trimming = TextTrimming.None };
                dc.DrawText(ft, new Point(6, y + (pitch - ft.Height) / 2));
            }
            var dis = new FormattedText("Editing disabled", CultureInfo.CurrentCulture,
                FlowDirection.LeftToRight, Face, FontSizePx,
                new SolidColorBrush(S.GutterDigits), 1.0);
            dc.DrawText(dis, new Point(6, Math.Max(0, h - pitch - dis.Height)));
        }

        protected override void OnMouseLeftButtonDown(MouseButtonEventArgs e)
        {
            base.OnMouseLeftButtonDown(e);
            V.ClickBand((int)(e.GetPosition(this).Y / S.RowPitch));
            e.Handled = true;
        }

        protected override void OnMouseWheel(MouseWheelEventArgs e)
        {
            base.OnMouseWheel(e);
            V.ScrollBands(e.Delta / 120);
            e.Handled = true;
        }

        // Locator peer (D3-aligned; the merge window is NOT one of the 12
        // golden-replayed views, so exposing pane rects to UIA is safe).
        protected override System.Windows.Automation.Peers.AutomationPeer OnCreateAutomationPeer()
            => new MergeClassPeer(this, "MergePane", Side);
    }

    internal sealed class MergeClassPeer : System.Windows.Automation.Peers.FrameworkElementAutomationPeer
    {
        readonly string _cls, _name;
        public MergeClassPeer(FrameworkElement o, string cls, string name) : base(o) { _cls = cls; _name = name; }
        protected override bool IsControlElementCore() => true;
        protected override string GetClassNameCore() => _cls;
        protected override string GetNameCore() => _name;
        protected override System.Windows.Automation.Peers.AutomationControlType GetAutomationControlTypeCore()
            => System.Windows.Automation.Peers.AutomationControlType.Pane;
    }

    /// <summary>The output pane: a COMPACT editable document (measured: the
    /// single writable pane; initial content = auto-merge, NOT the target
    /// file's disk content — §6.17 Q1). Editing: text insert / Enter /
    /// Backspace + caret movement; disk writes happen ONLY on an explicit
    /// window-level Ctrl+S (§6.17 Q2). Owner-drawn, self-managed caret.</summary>
    internal sealed class MergeOutputView : FrameworkElement
    {
        readonly MergeState V;
        readonly PaneStyle S;
        static readonly Typeface Face = TextPaneView.DiffFace;
        const double FontSizePx = 11;
        double CharW = -1;   // measured from our own face at first render
        bool FirstRender = true;

        public MergeOutputView(MergeState v, PaneStyle s)
        { V = v; S = s; v.Changed += () => InvalidateVisual(); Focusable = true; }

        protected override void OnRender(DrawingContext dc)
        {
            double pitch = S.RowPitch;
            double w = ActualWidth, h = ActualHeight;
            if (w <= 0 || h <= 0) return;
            if (CharW < 0)
                CharW = new FormattedText("0000000000", CultureInfo.CurrentCulture,
                    FlowDirection.LeftToRight, Face, FontSizePx,
                    new SolidColorBrush(S.LeftInk), 1.0).WidthIncludingTrailingWhitespace / 10.0;
            var pal = MergePalette.C;
            dc.DrawRectangle(new SolidColorBrush(S.LeftBase), null, new Rect(0, 0, w, h));
            V.VisibleOut = Math.Max(1, (int)(h / pitch));
            int top = Math.Max(0, V.TopOut);
            int visRows = (int)(h / pitch) + 1;
            var ink = new SolidColorBrush(S.LeftInk);
            for (int j = 0; j < visRows; j++)
            {
                int k = top + j;
                double y = j * pitch;
                if (y >= h) break;
                if (k >= V.Doc.Count)
                {
                    dc.DrawRectangle(new SolidColorBrush(pal.Void), null,
                        new Rect(0, y, w, Math.Min(pitch, h - y)));
                    continue;
                }
                var tint = V.DocTint(k);
                if (tint != pal.Base)
                    dc.DrawRectangle(new SolidColorBrush(tint), null, new Rect(0, y, w, Math.Min(pitch, h - y)));
                var ft = new FormattedText(V.Doc[k], CultureInfo.CurrentCulture,
                    FlowDirection.LeftToRight, Face, FontSizePx, ink, 1.0) { Trimming = TextTrimming.None };
                dc.DrawText(ft, new Point(6, y + (pitch - ft.Height) / 2));
                // caret = 1px vertical rule (presentation self-designed)
                if (k == V.CaretRow)
                    dc.DrawLine(new Pen(new SolidColorBrush(ink.Color), 1),
                        new Point(6 + V.CaretCol * CharW, y + 1),
                        new Point(6 + V.CaretCol * CharW, y + pitch - 1));
            }
            if (FirstRender) { Keyboard.Focus(this); FirstRender = false; }
        }

        protected override void OnMouseDown(MouseButtonEventArgs e)
        {
            base.OnMouseDown(e);
            Keyboard.Focus(this);
        }

        protected override void OnMouseLeftButtonDown(MouseButtonEventArgs e)
        {
            base.OnMouseLeftButtonDown(e);
            int row = V.TopOut + (int)(e.GetPosition(this).Y / S.RowPitch);
            V.SetCaretFromClick(row);
            e.Handled = true;
        }

        protected override void OnMouseWheel(MouseWheelEventArgs e)
        {
            base.OnMouseWheel(e);
            V.TopOut = Math.Max(0, Math.Min(Math.Max(0, V.Doc.Count - 1), V.TopOut - e.Delta / 120 * 3));
            V.Raise();
            e.Handled = true;
        }

        protected override void OnTextInput(TextCompositionEventArgs e)
        {
            base.OnTextInput(e);
            if (string.IsNullOrEmpty(e.Text)) return;
            if (e.Text[0] == '\r') { V.PressEnter(); e.Handled = true; return; }
            if (e.Text[0] == '\b') { V.PressBackspace(); e.Handled = true; return; }
            V.InsertText(e.Text);
            e.Handled = true;
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);
            // measured rule: NOTHING here writes to disk — save is the
            // window-level Ctrl+S only (§6.17 Q2)
            switch (e.Key)
            {
                case Key.Enter: V.PressEnter(); break;
                case Key.Back: V.PressBackspace(); break;
                case Key.Left:
                case Key.Right:
                case Key.Up:
                case Key.Down:
                case Key.Home:
                case Key.End:
                    V.MoveCaret(e.Key); break;
                default: return;
            }
            e.Handled = true;
        }

        // Output pane locator peer (class MergeOutput, name 'output').
        protected override System.Windows.Automation.Peers.AutomationPeer OnCreateAutomationPeer()
            => new MergeClassPeer(this, "MergeOutput", "output");
    }
}
