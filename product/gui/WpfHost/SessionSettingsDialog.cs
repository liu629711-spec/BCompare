// Session Settings dialog, first tier (docs/21 C; measured ring docs/19 §6.22,
// extracted/live/session-settings-en/session-settings-findings.json).
//
// Scope of the FIRST tier — exactly what the probes measured:
//   * dispatched engine views Text/Hex/Folder Compare: the Specs frame shows
//     TWO path fields (measured: n_spec_combos=2 in the text-view run);
//   * OK = apply IN PLACE: the CALLER re-runs the view's own engine channel
//     with the new pair and swaps the model into the live state objects — the
//     window and its UIA handle SURVIVE (measured main-replaced=false) and the
//     panes re-compare (measured left-pane pixel diff 690 / whole-window 3078);
//   * the text-view title FOLLOWS the new pair (measured title-after =
//     'left2.txt <--> right.txt - Text Compare ...') — the caller recomputes
//     it with the same measured DispatchTable template as the D1 brand swap;
//   * Cancel/Esc = discard with ZERO side effects (measured).
//
// The merge view's richer ring (Center/Output fields + the 'Save merge
// output?' confirm modal, measured ok-yes/ok-no arms) belongs to the merge
// window, which has NO menu bar in tier-1 — wiring Session Settings there is
// an explicit follow-up (docs/21 C). Format/Importance/Alignment tabs and the
// Copy/Swap spec buttons are out of scope (in案).
//
// Presentation: a small WPF window (our look, not VCL's); fields = editable
// TextBox + a Browse button (Win32 OpenFileDialog). BC's combos expose a
// dropdown history we do NOT fake (no measured content for it in a session
// with no history). The dialog is a MODAL owned window OUTSIDE the main
// window's UIA subtree, so the 12-golden pre-order stays untouched; the field
// boxes are role-named (LeftPath/RightPath) so gates can find and edit them.

using System;
using System.IO;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Controls;

namespace ReaCompare.Gui
{
    /// <summary>Outcome of Show(): cancelled, or the validated new pair.</summary>
    internal sealed class SpecResult
    {
        public bool Applied;
        public string Left = "", Right = "";
    }

    internal static class SessionSettingsDialog
    {
        /// <summary>Show the modal Specs dialog for a dispatched two-sided
        /// view. Returns applied=false on Cancel/validation-refusal (no side
        /// effects — measured Cancel ring); on OK the dialog CLOSES first, then
        /// the caller re-runs the engine in place (measured: settings dialog
        /// gone, main window handle alive, panes re-compared).</summary>
        public static SpecResult Show(Window owner, string view,
                                      string curLeft, string curRight)
        {
            var res = new SpecResult();
            var w = new Window
            {
                Title = $"Session Settings - {view}",
                Owner = owner,
                WindowStartupLocation = WindowStartupLocation.CenterOwner,
                SizeToContent = SizeToContent.WidthAndHeight,
                ResizeMode = ResizeMode.NoResize,
                ShowInTaskbar = false,
                MinWidth = 480,
            };
            var grid = new Grid { Margin = new Thickness(12) };
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(320) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(10) });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            string[] labels = { "Left file:", "Right file:" };
            string[] vals = { curLeft, curRight };
            var boxes = new TextBox[2];
            for (int i = 0; i < 2; i++)
            {
                grid.Children.Add(new TextBlock
                {
                    Text = labels[i],
                    Margin = new Thickness(0, 5, 8, 0),
                    VerticalAlignment = VerticalAlignment.Center,
                });
                Grid.SetRow((UIElement)grid.Children[grid.Children.Count - 1], i);
                var tb = new TextBox { Text = vals[i], Margin = new Thickness(0, 3, 4, 3) };
                // UIA identity for the gate (probe-measured top-order combo
                // mapping = Left then Right):
                AutomationProperties.SetName(tb, i == 0 ? "LeftPath" : "RightPath");
                Grid.SetRow(tb, i); Grid.SetColumn(tb, 1);
                grid.Children.Add(tb);
                boxes[i] = tb;
                var browse = new Button { Content = "...", Width = 28, Margin = new Thickness(0, 3, 0, 3) };
                AutomationProperties.SetName(browse, "Browse");
                int idx = i;
                browse.Click += (s, e) =>
                {
                    var dlg = new Microsoft.Win32.OpenFileDialog
                    {
                        FileName = Path.GetFileName(boxes[idx].Text),
                        CheckFileExists = false,
                    };
                    if (dlg.ShowDialog(w) == true) boxes[idx].Text = dlg.FileName;
                };
                Grid.SetRow(browse, i); Grid.SetColumn(browse, 2);
                grid.Children.Add(browse);
            }

            var ok = new Button { Content = "OK", Width = 96, Height = 30, IsDefault = true, Margin = new Thickness(0, 0, 8, 0) };
            AutomationProperties.SetName(ok, "OK");
            var cancel = new Button { Content = "Cancel", Width = 96, Height = 30, IsCancel = true };
            AutomationProperties.SetName(cancel, "Cancel");
            var btns = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };
            btns.Children.Add(ok); btns.Children.Add(cancel);
            Grid.SetRow(btns, 3); Grid.SetColumnSpan(btns, 3);
            grid.Children.Add(btns);
            w.Content = grid;

            ok.Click += (s, e) =>
            {
                // validate like the engine would refuse (fail closed, never a
                // half-applied session): existing paths, file-vs-folder matching
                // the view (Folder Compare = both dirs; the rest = both files).
                string left = boxes[0].Text.Trim(), right = boxes[1].Text.Trim();
                string err = Validate(view, left, right);
                if (err != null)
                {
                    // BC refuses with a modal; MessageBox is the native
                    // equivalent (presentation ours). STAY in the dialog to
                    // keep editing — the confirm-Cancel arm was never measured
                    // on BC, keep-editing is the safe self-design (annotated
                    // docs/19 §6.22).
                    MessageBox.Show(w, err, "Session Settings");
                    return;
                }
                res.Applied = true; res.Left = left; res.Right = right;
                w.DialogResult = true;
            };
            w.ShowDialog();   // the dialog CLOSES here, before any apply
            return res;
        }

        static string Validate(string view, string left, string right)
        {
            if (left.Length == 0 || right.Length == 0) return "Both paths are required.";
            bool wantDir = view == "Folder Compare";
            foreach (var p in new[] { left, right })
            {
                bool isDir = Directory.Exists(p);
                bool isFile = File.Exists(p);
                if (!isDir && !isFile) return $"Path not found: {p}";
                if (wantDir && !isDir) return $"Folder Compare needs folders: {p}";
                if (!wantDir && isDir) return $"{view} needs files, not a folder: {p}";
            }
            return null;
        }
    }
}
