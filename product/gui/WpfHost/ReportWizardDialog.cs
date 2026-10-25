// Report wizard, first tier (docs/21 D; feature 11 GUI). The MVP last piece.
//
// Design = a THIN SHELL over the engine's report channels (docs/21 D): the
// GUI never reimplements a renderer, so a report the wizard writes is byte-for
// byte what `reacmp` produces for the same parameters. That is the gate's
// claim (uia-report-check: GUI output == CLI direct-run output, timestamps
// normalized exactly as product/verify/harness/normalize.py already does for
// every golden — `Produced:` line + `created=` attr).
//
// Channels (all engine-verified exit 0 before this shipped — see docs/21 D):
//   * Text Compare     : the three-path form
//                        reacmp <L> <R> <out> --layout=<l> [--opt=<o>]
//                        layouts (engine --help, 7): xml | side-by-side |
//                        interleaved | over-under | patch | summary | statistics
//   * Hex Compare      : @script `hex-report layout:<l> output-to:"<out>"
//                        "<L>" "<R>"`  (no options: hex has no display filter,
//                        observed exit 106)  layouts (3): side-by-side |
//                        interleaved | summary
//   * Folder Compare   : @script `load "<L>" "<R>"` newline `folder-report
//                        layout:<l> output-to:"<out>"`  layouts (3):
//                        side-by-side | summary | xml
// Other views keep their {View} Report... item present in the menu (the 845/
// 410/290 structure ledger is untouched) but get NO wizard in tier-1: their
// report engines are not all wired to a live session here (picture/registry/
// version/table/media), and the wizard must not fake a report it cannot
// produce — the click stays inert, an honest shell (docs/20 capability rule).
//
// Presentation = self-designed (annotated): a small WPF dialog; the layout
// list is populated from the ENGINE's supported set for the current view, so
// the wizard can never offer a layout the engine would reject.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Controls;

namespace ReaCompare.Gui
{
    internal static class ReportWizardDialog
    {
        public static void Show(Window owner, string view, string engineExe,
                                string left, string right)
        {
            if (!Channels.TryGetValue(view, out var ch))
                return; // honest inert: no live report engine wired for this view
            bool isText = view == "Text Compare";
            var w = new Window
            {
                Title = ch.Title,
                Owner = owner,
                WindowStartupLocation = WindowStartupLocation.CenterOwner,
                SizeToContent = SizeToContent.WidthAndHeight,
                ResizeMode = ResizeMode.NoResize,
                ShowInTaskbar = false,
                MinWidth = 460,
            };
            var grid = new Grid { Margin = new Thickness(12) };
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(300) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            for (int i = 0; i < (isText ? 3 : 2); i++)
                grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(10) });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            // layout combo (engine's legal set for THIS view — from --help /
            // *_LAYOUT_NAMES, never a guess)
            grid.Children.Add(new TextBlock { Text = "Layout:", Margin = new Thickness(0, 5, 8, 0), VerticalAlignment = VerticalAlignment.Center });
            Grid.SetRow((UIElement)grid.Children[grid.Children.Count - 1], 0);
            var layout = new ComboBox { Margin = new Thickness(0, 3, 4, 3) };
            foreach (var l in ch.Layouts) layout.Items.Add(l);
            layout.SelectedIndex = 0;
            AutomationProperties.SetName(layout, "ReportLayout");
            Grid.SetRow(layout, 0); Grid.SetColumn(layout, 1);
            grid.Children.Add(layout);

            int row = 1;
            TextBox optBox = null;
            if (isText)
            {
                // options: maps to --opt=<name> (text channel display filter);
                // hex/folder have none (hex refuses options= exit 106).
                grid.Children.Add(new TextBlock { Text = "Options:", Margin = new Thickness(0, 5, 8, 0), VerticalAlignment = VerticalAlignment.Center });
                Grid.SetRow((UIElement)grid.Children[grid.Children.Count - 1], row);
                optBox = new TextBox { Margin = new Thickness(0, 3, 4, 3), ToolTip = "display-mismatches, ignore-unimportant, … (comma separated; leave empty for default)" };
                AutomationProperties.SetName(optBox, "ReportOptions");
                Grid.SetRow(optBox, row); Grid.SetColumn(optBox, 1);
                grid.Children.Add(optBox);
                row++;
            }

            // output path (default = <left basename>.report.<ext>)
            grid.Children.Add(new TextBlock { Text = "Output file:", Margin = new Thickness(0, 5, 8, 0), VerticalAlignment = VerticalAlignment.Center });
            Grid.SetRow((UIElement)grid.Children[grid.Children.Count - 1], row);
            var outBox = new TextBox { Margin = new Thickness(0, 3, 4, 3), Text = DefaultOut(left, ch.Ext) };
            AutomationProperties.SetName(outBox, "ReportOutput");
            Grid.SetRow(outBox, row); Grid.SetColumn(outBox, 1);
            grid.Children.Add(outBox);
            var browse = new Button { Content = "...", Width = 28, Margin = new Thickness(0, 3, 0, 3) };
            AutomationProperties.SetName(browse, "Browse");
            browse.Click += (s, e) =>
            {
                var dlg = new Microsoft.Win32.SaveFileDialog
                {
                    FileName = Path.GetFileName(outBox.Text),
                    Filter = "Report (*.xml;*.txt)|*.xml;*.txt|All files (*.*)|*.*",
                };
                if (dlg.ShowDialog(w) == true) outBox.Text = dlg.FileName;
            };
            Grid.SetRow(browse, row); Grid.SetColumn(browse, 2);
            grid.Children.Add(browse);

            var run = new Button { Content = "Run", Width = 96, Height = 30, IsDefault = true, Margin = new Thickness(0, 0, 8, 0) };
            AutomationProperties.SetName(run, "ReportRun");
            var cancel = new Button { Content = "Cancel", Width = 96, Height = 30, IsCancel = true };
            AutomationProperties.SetName(cancel, "Cancel");
            var btns = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };
            btns.Children.Add(run); btns.Children.Add(cancel);
            Grid.SetRow(btns, row + 1); Grid.SetColumnSpan(btns, 3);
            grid.Children.Add(btns);
            var status = new TextBlock { Margin = new Thickness(0, 6, 0, 0), TextWrapping = TextWrapping.Wrap };
            AutomationProperties.SetName(status, "ReportStatus");
            Grid.SetRow(status, row + 2); Grid.SetColumnSpan(status, 3);
            grid.Children.Add(status);
            w.Content = grid;

            run.Click += (s, e) =>
            {
                // TEST-INJECTION ONLY (uia-report-check negative): the run
                // reports success but writes NOTHING — simulating the fault
                // "wizard not bound to the engine" so the gate's
                // file-existence + byte-equality assertions have teeth. Never
                // set in product use.
                if (Environment.GetEnvironmentVariable("REACMP_REPORT_NEG") == "1")
                {
                    status.Text = "Report written (injected no-op).";
                    return;
                }
                string outPath = outBox.Text.Trim();
                if (outPath.Length == 0)
                { status.Text = "Output file is required."; return; }
                string err;
                bool ok = RunChannel(view, ch, engineExe, left, right,
                                     (string)layout.SelectedItem,
                                     optBox?.Text.Trim() ?? "", outPath, out err);
                // NON-MODAL status line (not a MessageBox): a child modal would
                // block the gate's UIA Invoke (WPF pumps the modal on the same
                // thread), and the gate verifies the FILE independently anyway.
                status.Text = ok ? "Report written: " + outPath
                                : "Report failed: " + err;   // CLI stderr verbatim
            };
            w.ShowDialog();
        }

        // per-view channel descriptor (layout sets are ENGINE facts, not guesses)
        sealed class Channel { public string Title; public string[] Layouts; public string Ext; }
        static readonly Dictionary<string, Channel> Channels = new Dictionary<string, Channel>(StringComparer.Ordinal)
        {
            ["Text Compare"] = new Channel { Title = "Text Compare Report", Ext = ".xml",
                Layouts = new[] { "xml", "side-by-side", "interleaved", "over-under", "patch", "summary", "statistics" } },
            ["Hex Compare"] = new Channel { Title = "Hex Compare Report", Ext = ".txt",
                Layouts = new[] { "side-by-side", "interleaved", "summary" } },
            ["Folder Compare"] = new Channel { Title = "Folder Compare Report", Ext = ".xml",
                Layouts = new[] { "side-by-side", "summary", "xml" } },
        };

        static string DefaultOut(string left, string ext)
        {
            string dir = Path.GetDirectoryName(Path.GetFullPath(left)) ?? ".";
            string stem = Path.GetFileNameWithoutExtension(left);
            return Path.Combine(dir, stem + ".report" + ext);
        }

        /// <summary>Build the CLI argv for the channel and run it. text = the
        /// three-path form; hex/folder = a generated @script with the exact
        /// verbs verified to exit 0 before this shipped.</summary>
        static bool RunChannel(string view, Channel ch, string exe, string left, string right,
                              string layout, string options, string outPath, out string err)
        {
            err = "";
            if (exe == null || !File.Exists(exe)) { err = "reacmp engine not found"; return false; }
            string scriptPath = null;
            string args;
            if (view == "Text Compare")
            {
                args = $"\"{left}\" \"{right}\" \"{outPath}\" --layout={layout}";
                if (!string.IsNullOrEmpty(options)) args += " --opt=" + options;
            }
            else
            {
                // @script file (UTF-8 no BOM, the verbs verified exit-0):
                //   hex:    hex-report layout:<l> output-to:"<out>" "<L>" "<R>"
                //   folder: load "<L>" "<R>" \n folder-report layout:<l> output-to:"<out>"
                scriptPath = Path.Combine(Path.GetTempPath(), $"reacmp-rep-{Guid.NewGuid():N}.bc");
                string s = view == "Hex Compare"
                    ? $"hex-report layout:{layout} output-to:\"{outPath}\" \"{left}\" \"{right}\""
                    : $"load \"{left}\" \"{right}\"\nfolder-report layout:{layout} output-to:\"{outPath}\"";
                try { File.WriteAllText(scriptPath, s + "\n", new System.Text.UTF8Encoding(false)); }
                catch (Exception e) { err = e.Message; return false; }
                args = "@" + scriptPath;
            }
            try
            {
                var psi = new ProcessStartInfo(exe, args)
                { UseShellExecute = false, RedirectStandardError = true, CreateNoWindow = true };
                using (var p = Process.Start(psi))
                {
                    err = (p.StandardError.ReadToEnd() ?? "").Trim();
                    p.WaitForExit();
                    if (p.ExitCode != 0 || !File.Exists(outPath))
                        return false;
                }
                return true;
            }
            catch (Exception e) { err = e.Message; return false; }
            finally { if (scriptPath != null) try { File.Delete(scriptPath); } catch { } }
        }
    }
}
