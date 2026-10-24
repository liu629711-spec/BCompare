//! Folder reports in the three documented layouts.
//!
//! `help/scripting_reference.html`, FOLDER-REPORT:
//!
//! > `folder-report layout:<layout> [options:<options>] [title:<report title>]
//! > output-to:(printer|clipboard|<filename>) [output-options:<options>]`
//! > …
//! > `layout` controls the report's appearance and can be **side-by-side**,
//! > **summary** or **xml**.
//!
//! (O level: the layout names are quoted from the shipped help file, and the
//! `verify/dir/` scripts target `layout:xml`.)
//!
//! # XML layout — evidence grade per element
//!
//! The XML writer is modelled on the observed output
//! `tools/_audit/dir-load-expand-report.xml` (O level: the file exists in this
//! workspace and was produced by the Oracle). Byte-level facts taken from it:
//!
//! | Fact | Grade | Evidence |
//! |---|---|---|
//! | UTF-8 BOM (`EF BB BF`) first | **O** | first 3 bytes of the file |
//! | `<?xml version="1.0" encoding="utf-8"?>` then CRLF | **O** | bytes 3..39 |
//! | `<bcreport created="YYYY/MM/DD HH:MM:SS">` | **O** | line 2 |
//! | one tab per nesting level | **O** | `\t<foldercomp>` at offset 0x8C |
//! | CRLF line endings throughout, trailing CRLF at EOF | **O** | 88 CRLF, 88 LF |
//! | root `<foldercomp>` holds `<ltpath>` then `<rtpath>` | **O** | lines 3..5 |
//! | subdirectory = nested `<foldercomp>` with `<lt>`/`<rt>` children | **O** | lines 6..36 |
//! | file = `<filecomp status="…">` with `<lt>`/`<rt>` | **O** | lines 37..48 |
//! | one-sided row omits the missing side's element entirely | **O** | lines 49..62 |
//! | `<size>` is empty for an unexpanded directory, numeric once expanded | **O** | compare the two audit files |
//! | `<modified>` is local wall-clock `YYYY/MM/DD HH:MM:SS` | **O + D** | value cross-checked against the fixture's own mtime — see `reacmp_vfs::time` |
//! | status tokens are exactly the six string-table literals | **O** | `extracted/pseudocode/140fd1e90.c` |
//! | `<size/>` (self-closing) for a zero-size *file* | **U** | never observed: no zero-byte file appears in the stored reports. This writer emits `<size>0</size>` for a file, which is what `<size>0</size>` for `emptydir` suggests for a numeric value |
//! | `<mode>`, `ignoreunimportant`, `filters`, `advfilters` elements | **O (existence) / U (when)** | strings exist in `FUN_140fd2340`; the stored reports do not contain them |
//! | `created` timestamp format | **O** | `2026/10/13 14:17:16` |
//!
//! Anything **not** in the table above is a guess and is marked as `inferred` in
//! this file's comments.

use std::fmt::Write as _;

use reacmp_vfs::Side;

use crate::error::DirError;
use crate::status::Status;
use crate::tree::{FolderComparison, TreeNode};

/// The three documented folder-report layouts.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Layout {
    SideBySide,
    Summary,
    Xml,
}

impl Layout {
    /// The exact name BC accepts in `layout:<name>`.
    pub fn as_str(self) -> &'static str {
        match self {
            Layout::SideBySide => "side-by-side",
            Layout::Summary => "summary",
            Layout::Xml => "xml",
        }
    }

    pub fn parse(name: &str) -> Result<Self, DirError> {
        match name {
            "side-by-side" => Ok(Layout::SideBySide),
            "summary" => Ok(Layout::Summary),
            "xml" => Ok(Layout::Xml),
            other => Err(DirError::UnknownLayout {
                layout: other.to_string(),
            }),
        }
    }
}

/// Options that shape a report.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReportOptions {
    /// The `created` value for the XML header.
    ///
    /// Injected rather than read from the clock so a report is reproducible: the
    /// same comparison rendered twice produces identical bytes. Pass `None` to
    /// omit the attribute, which is also what makes the fixture corpus's
    /// committed expectations stable.
    pub created: Option<String>,
    /// Optional `title:` text. BC writes none by default (O: absent from the
    /// stored reports).
    pub title: Option<String>,
    /// Emit `<ignoreunimportant/>` after `<rtpath>`.
    ///
    /// Observed in `A3-folder-gate-serial-04/oracle/reject-ignore-unimportant-
    /// not-probed.out` and every u4d `iu-*` probe: the empty element sits
    /// directly after the two path elements, before the first comparison row.
    pub ignore_unimportant: bool,
    /// The raw `filter` mask text, echoed verbatim into `<filters>`.
    ///
    /// Observed order (u5i, fivecases: `xml-filter-only`, `xml-iu-only`,
    /// `xml-filter-and-iu`, `xml-filter-then-iu`, `xml-iu-then-filter`):
    ///
    /// ```text
    /// <ltpath>…</ltpath>
    /// <rtpath>…</rtpath>
    /// <ignoreunimportant/>    <- only when criteria say so
    /// <filters>raw</filters>  <- only when a filter was set
    /// …rows…
    /// ```
    ///
    /// so `<ignoreunimportant/>` and `<filters>` are independent and
    /// `<filters>` always comes second. The text is the script's own mask
    /// string, character for character — `filter "-A\\"` renders
    /// `<filters>-A\\</filters>` (u5h), which is why the executor must not
    /// unescape it.
    ///
    /// `None` means "no filter was set" and emits nothing; a filter that was set
    /// writes the element even when its masks remove no row (`filter "sub\\"`
    /// leaves the report unchanged and still writes `<filters>sub\\</filters>`,
    /// u5c `filter-folder-mask`).
    pub filters: Option<String>,
}

impl Default for ReportOptions {
    fn default() -> Self {
        ReportOptions {
            created: None,
            title: None,
            ignore_unimportant: false,
            filters: None,
        }
    }
}

/// Render a comparison in the requested layout.
pub fn render(
    comparison: &FolderComparison,
    layout: Layout,
    options: &ReportOptions,
) -> Result<String, DirError> {
    match layout {
        Layout::Xml => render_xml(comparison, options),
        Layout::SideBySide => render_side_by_side(comparison, options),
        Layout::Summary => render_summary(comparison, options),
    }
}

// ==========================================================================
// XML
// ==========================================================================

/// Group a size with thousands commas, the way the observed writer renders it.
///
/// Observed (u4d `size-big`, `size-dir-big`): `6017` renders `6,017`, `55192`
/// renders `55,192`, and the grouping is identical on the English reference
/// install and the zh current one — so it is NOT locale-dependent. Values below
/// 1000 and zero render bare (`0`, `999`), and a zero-byte FILE renders
/// `<size>0</size>`, not the self-closing form (u4d `size-zero`).
fn grouped_size(n: u64) -> String {
    let digits = n.to_string();
    let mut out = String::with_capacity(digits.len() + digits.len() / 3);
    let len = digits.len();
    for (i, ch) in digits.chars().enumerate() {
        if i > 0 && (len - i) % 3 == 0 {
            out.push(',');
        }
        out.push(ch);
    }
    out
}

/// Escape XML text content.
///
/// Matches the observed output for the characters that occur in a path or name:
/// the stored reports contain `\` unescaped (Windows paths), which is correct —
/// only `&`, `<`, `>` and, in attributes, the quote need escaping.
fn esc(text: &str) -> String {    let mut out = String::with_capacity(text.len());
    for ch in text.chars() {
        match ch {
            '&' => out.push_str("&amp;"),
            '<' => out.push_str("&lt;"),
            '>' => out.push_str("&gt;"),
            _ => out.push(ch),
        }
    }
    out
}

fn esc_attr(text: &str) -> String {
    esc(text).replace('"', "&quot;")
}

/// One `<ltpath>`/`<rtpath>` line at two tabs, self-closing when empty.
///
/// Observed: u5e `load-left-only` writes `<ltpath>D:\…\L</ltpath>` followed by
/// `<rtpath/>` — an empty path is the empty element, never
/// `<rtpath></rtpath>`. The same shape appears in the 155-byte no-`load` shell
/// (u5b) and the 122-byte text shell (u5f).
fn path_line(tag: &str, path: &str) -> String {
    if path.is_empty() {
        format!("\t\t<{tag}/>\r\n")
    } else {
        format!("\t\t<{tag}>{}</{tag}>\r\n", esc(path))
    }
}

/// Render the `layout:xml` report.
///
/// Structure reproduced from the observed file, element for element:
///
/// ```text
/// <bcreport created="…">
/// 	<foldercomp>
/// 		<ltpath>…</ltpath>
/// 		<rtpath>…</rtpath>
/// 		<foldercomp>            <- a subdirectory row
/// 			<lt><name>…</name><size>…</size><modified>…</modified></lt>
/// 			<rt>…</rt>
/// 			<filecomp status="same">…</filecomp>
/// 		</foldercomp>
/// 		<filecomp status="ltonly">
/// 			<lt>…</lt>
/// 		</filecomp>
/// 	</foldercomp>
/// </bcreport>
/// ```
pub fn render_xml(
    comparison: &FolderComparison,
    options: &ReportOptions,
) -> Result<String, DirError> {
    let mut out = String::new();
    // The BOM is a byte-level observation of the Oracle's output.
    out.push('\u{feff}');
    out.push_str("<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n");

    match &options.created {
        Some(ts) => {
            let _ = write!(out, "<bcreport created=\"{}\">\r\n", esc_attr(ts));
        }
        None => out.push_str("<bcreport>\r\n"),
    }

    out.push_str("\t<foldercomp>\r\n");
    // An empty path renders the self-closing form: u5e `load-left-only` (a
    // `load` with only a left side) has `<rtpath/>` on its own line while
    // `<ltpath>` carries the folder, so an absent side is not `<rtpath></rtpath>`.
    let _ = write!(out, "{}", path_line("ltpath", comparison.left_root.as_str()));
    let _ = write!(out, "{}", path_line("rtpath", comparison.right_root.as_str()));
    if options.ignore_unimportant {
        out.push_str("\t\t<ignoreunimportant/>\r\n");
    }
    // u5i: `<filters>` follows `<ignoreunimportant/>` and precedes every row,
    // and the raw mask text is written verbatim (a `\` is NOT escaped: u5h
    // renders `-A\\` exactly as the script wrote it).
    if let Some(filters) = &options.filters {
        let _ = write!(out, "\t\t<filters>{}</filters>\r\n", esc(filters));
    }

    for node in &comparison.entries {
        write_node(&mut out, node, 2, comparison)?;
    }

    out.push_str("\t</foldercomp>\r\n");
    out.push_str("</bcreport>\r\n");
    Ok(out)
}

fn write_node(
    out: &mut String,
    node: &TreeNode,
    depth: usize,
    comparison: &FolderComparison,
) -> Result<(), DirError> {
    if node.is_hidden() {
        // A row a `filter` removed is not written at all (u5c
        // `filter-include-txt` has no `b.log` row).
        return Ok(());
    }
    let indent = "\t".repeat(depth);
    // A directory row is a nested `<foldercomp>`; every other row is a
    // `<filecomp status="…">`. `is_dir_row` (not `is_dir`) is used so a kind
    // conflict — a file on one side and a directory on the other — is reported as
    // a file row, because it cannot be expanded. Derived, not observed: see
    // `TreeNode::is_dir_row`.
    if node.is_dir_row() {
        // OBSERVED (u5j): a directory row NEVER carries a `status` attribute,
        // expanded or not — every one of the 18 u5j reports has plain
        // `<foldercomp>` for `d`/`onlyL`/`thing`, with `diff` content inside.
        let _ = write!(out, "{indent}<foldercomp>\r\n");
        write_side(out, node, Side::Left, depth + 1, comparison);
        write_side(out, node, Side::Right, depth + 1, comparison);
        // An unexpanded directory has no children to write (u5g s1).
        for child in &node.children {
            write_node(out, child, depth + 1, comparison)?;
        }
        let _ = write!(out, "{indent}</foldercomp>\r\n");
    } else {
        let token = node.status.xml_token().ok_or_else(|| {
            DirError::UnrepresentableStatus {
                status: format!("{:?}", node.status),
            }
        })?;
        let _ = write!(out, "{indent}<filecomp status=\"{token}\">\r\n");
        write_side(out, node, Side::Left, depth + 1, comparison);
        write_side(out, node, Side::Right, depth + 1, comparison);
        let _ = write!(out, "{indent}</filecomp>\r\n");
    }
    Ok(())
}

/// Write one side's `<lt>`/`<rt>` block, or nothing when that side is absent.
///
/// The observed report simply omits the missing side rather than emitting an
/// empty element (O: `leftonly.txt` has only `<lt>`).
fn write_side(
    out: &mut String,
    node: &TreeNode,
    side: Side,
    depth: usize,
    comparison: &FolderComparison,
) {
    let metadata = node.metadata_for(side);
    let Some(metadata) = metadata else {
        return;
    };
    let indent = "\t".repeat(depth);
    let tag = match side {
        Side::Left => "lt",
        Side::Right => "rt",
    };
    let _ = write!(out, "{indent}<{tag}>\r\n");
    let _ = write!(
        out,
        "{indent}\t<name>{}</name>\r\n",
        esc(&node.name)
    );

    // Size: the row's own size for a file, the subtree aggregate for a
    // directory — but only when the whole subtree is expanded (u5g).
    //
    // The M3 comment here said "an unexpanded directory contributes no
    // children, so the aggregate is zero"; the M4 probes measured the opposite
    // shape for that case: an unexpanded directory renders `<size/>`, NOT
    // `<size>0</size>`. `reported_size` returns `None` for it now, which is the
    // same branch a directory with an unknown size takes — both are the
    // observed self-closing element, so no distinction is lost.
    let size = if node.is_dir() {
        node.reported_size(side)
    } else {
        metadata.size
    };
    match size {
        Some(n) => {
            let _ = write!(out, "{indent}\t<size>{}</size>\r\n", grouped_size(n));
        }
        // OBSERVED u5g s1/s3 (`A=<size/>`), u5h `expand-a-file`, u5j
        // `*-noexpand`.
        None => {
            let _ = write!(out, "{indent}\t<size/>\r\n");
        }
    }

    match metadata.modified {
        Some(t) => {
            let offset = comparison.offset_minutes.unwrap_or(0);
            let _ = write!(
                out,
                "{indent}\t<modified>{}</modified>\r\n",
                esc(&t.format_local(offset))
            );
        }
        None => {
            let _ = write!(out, "{indent}\t<modified/>\r\n");
        }
    }

    let _ = write!(out, "{indent}</{tag}>\r\n");
}

// ==========================================================================
// Text layouts
// ==========================================================================

/// `layout:side-by-side` — one row per aligned entry, left and right columns.
///
/// **No observed sample exists.** `product/verify/README.md` section 9 states
/// there is no golden folder report and that only the *recipe* is verified, so
/// the exact column widths, separators and header of BC's text folder layouts are
/// **not known**. This renders a deterministic, self-describing table instead of
/// imitating an unobserved format, and the header says so.
///
/// Marked `inferred` / `unknown` rather than presented as compatible.
pub fn render_side_by_side(
    comparison: &FolderComparison,
    options: &ReportOptions,
) -> Result<String, DirError> {
    let mut out = String::new();
    if let Some(title) = &options.title {
        let _ = write!(out, "{title}\r\n");
    }
    let _ = write!(out, "Folder Compare\r\n");
    let _ = write!(out, "Left:  {}\r\n", comparison.left_root);
    let _ = write!(out, "Right: {}\r\n", comparison.right_root);
    let _ = write!(out, "Criteria: {}\r\n", criteria_text(comparison));
    write_filter_line(&mut out, options);
    out.push_str(
        "NOTE: exact Beyond Compare text-layout formatting is unobserved; \
         this layout is NOT byte-compatible.\r\n",
    );
    out.push_str("\r\n");

    // Column widths sized to content so the output is stable and readable.
    let mut rows: Vec<Row> = Vec::new();
    for node in &comparison.entries {
        collect_rows(node, 0, &mut rows);
    }
    let left_w = rows
        .iter()
        .map(|r| display_width(&r.left_cell()))
        .max()
        .unwrap_or(0)
        .max("Left".len());
    let right_w = rows
        .iter()
        .map(|r| display_width(&r.right_cell()))
        .max()
        .unwrap_or(0)
        .max("Right".len());

    let _ = write!(
        out,
        "{:<lw$} | {:<rw$} | {}\r\n",
        "Left",
        "Right",
        "Status",
        lw = left_w,
        rw = right_w
    );
    let _ = write!(
        out,
        "{:-<lw$}-+-{:-<rw$}-+--------\r\n",
        "",
        "",
        lw = left_w,
        rw = right_w
    );
    for row in &rows {
        let _ = write!(
            out,
            "{:<lw$} | {:<rw$} | {}\r\n",
            row.left_cell(),
            row.right_cell(),
            row.status.label(),
            lw = left_w,
            rw = right_w
        );
    }

    if !comparison.notes.is_empty() {
        out.push_str("\r\nNotes:\r\n");
        for note in &comparison.notes {
            let _ = write!(out, "  - {note}\r\n");
        }
    }
    Ok(out)
}

/// `layout:summary` — counts of each status plus the criteria in force.
///
/// Same caveat as the side-by-side layout: **unobserved**, so this is a
/// self-describing summary rather than an imitation.
pub fn render_summary(
    comparison: &FolderComparison,
    options: &ReportOptions,
) -> Result<String, DirError> {
    let mut out = String::new();
    if let Some(title) = &options.title {
        let _ = write!(out, "{title}\r\n");
    }
    out.push_str("Folder Compare Summary\r\n");
    let _ = write!(out, "Left:  {}\r\n", comparison.left_root);
    let _ = write!(out, "Right: {}\r\n", comparison.right_root);
    let _ = write!(out, "Criteria: {}\r\n", criteria_text(comparison));
    write_filter_line(&mut out, options);
    out.push_str(
        "NOTE: exact Beyond Compare summary-layout formatting is unobserved; \
         this layout is NOT byte-compatible.\r\n",
    );
    out.push_str("\r\n");

    // Every observed token is reported, including the zero rows, so a missing
    // category is visible rather than absent.
    let counts: Vec<(Status, usize)> = [
        Status::Same,
        Status::Diff,
        Status::LeftNewer,
        Status::RightNewer,
        Status::LeftOnly,
        Status::RightOnly,
        Status::Unknown,
    ]
    .iter()
    .map(|s| (*s, comparison.count_status(*s)))
    .collect();

    let width = counts
        .iter()
        .map(|(s, _)| s.label().len())
        .max()
        .unwrap_or(0);
    for (status, n) in &counts {
        let _ = write!(out, "{:<width$} : {n}\r\n", status.label(), width = width);
    }
    let _ = write!(out, "{:<width$} : {}\r\n", "total", comparison.row_count(), width = width);

    if !comparison.notes.is_empty() {
        out.push_str("\r\nNotes:\r\n");
        for note in &comparison.notes {
            let _ = write!(out, "  - {note}\r\n");
        }
    }
    Ok(out)
}

fn criteria_text(comparison: &FolderComparison) -> String {
    let text = comparison.criteria.to_argument_string();
    if text.is_empty() {
        "(default)".to_string()
    } else {
        text
    }
}

/// Write the `filter` line the Oracle puts in its text layouts, when a filter
/// was set.
///
/// Exact bytes, measured from `u5i-probe-20261014T032235Z/reports/
/// summary-filter.out` and `sxs-filter.out` (line 4 of both):
///
/// ```text
/// 过滤：  *.txt
/// ```
///
/// i.e. the two CJK characters `过滤` (U+8FC7 U+6EE4), a **fullwidth** colon
/// (U+FF1A), then **two** ASCII spaces, then the raw mask text. The Oracle is
/// the Chinese repack, so the label is Chinese; the harness's normalizer does
/// **not** translate this line (it is not in `TEXT_LABEL_PAIRS`), so the bytes
/// must match or the normalised comparison fails.
///
/// Placement: the measured order is `模式：  全部` → `过滤：  …` → the two base
/// folder lines. These text layouts are not byte-compatible overall (see their
/// own doc comments), so the line is emitted in the same *relative* position —
/// after the criteria/mode header and before the body — and the divergence of
/// the surrounding header stays recorded rather than papered over.
fn write_filter_line(out: &mut String, options: &ReportOptions) {
    if let Some(filters) = &options.filters {
        let _ = write!(out, "过滤：  {filters}\r\n");
    }
}

struct Row {
    depth: usize,
    name: String,
    status: Status,
    left_size: Option<u64>,
    right_size: Option<u64>,
}

impl Row {
    fn left_cell(&self) -> String {
        self.cell(Side::Left)
    }

    fn right_cell(&self) -> String {
        self.cell(Side::Right)
    }

    fn cell(&self, side: Side) -> String {
        let (present, size) = match side {
            Side::Left => (self.left_size.is_some(), self.left_size),
            Side::Right => (self.right_size.is_some(), self.right_size),
        };
        if !present {
            return String::new();
        }
        let indent = "  ".repeat(self.depth);
        match size {
            Some(n) => format!("{indent}{} ({n})", self.name),
            None => format!("{indent}{}", self.name),
        }
    }
}

fn collect_rows(node: &TreeNode, depth: usize, out: &mut Vec<Row>) {
    if node.is_hidden() {
        // A row a `filter` removed is not in the text layouts either — the row
        // set is one property of the comparison, not one per layout.
        return;
    }
    out.push(Row {
        depth,
        name: node.name.clone(),
        status: node.status,
        left_size: node.left.as_ref().map(|e| e.metadata.size.unwrap_or(0)),
        right_size: node.right.as_ref().map(|e| e.metadata.size.unwrap_or(0)),
    });
    for child in &node.children {
        collect_rows(child, depth + 1, out);
    }
}

/// Width in characters, not bytes, so a non-ASCII fixture name does not skew the
/// table.
fn display_width(s: &str) -> usize {
    s.chars().count()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::criteria::Criteria;
    use crate::tree::TreeNode;
    use reacmp_vfs::{Entry, Metadata, Timestamp, VfsPath};

    fn mk_file(name: &str, size: u64) -> Entry {
        Entry::new(
            name,
            VfsPath::new(format!(r"D:\L\{name}")),
            Metadata::file(size).with_modified(Timestamp::from_unix_seconds(1_791_857_172)),
        )
    }

    fn leaf(name: &str, l: Option<Entry>, r: Option<Entry>, status: Status) -> TreeNode {
        TreeNode {
            name: name.to_string(),
            relative_path: name.to_string(),
            left: l,
            right: r,
            status,
            children: vec![],
            hidden: false,
            expanded: true,
            notes: vec![],
        }
    }

    fn sample() -> FolderComparison {
        let sub_inner = leaf(
            "inner.txt",
            Some(mk_file("inner.txt", 3)),
            Some(mk_file("inner.txt", 3)),
            Status::Same,
        );
        let sub = TreeNode {
            name: "sub".to_string(),
            relative_path: "sub".to_string(),
            left: Some(Entry::new(
                "sub",
                VfsPath::new(r"D:\L\sub"),
                Metadata::directory().with_modified(Timestamp::from_unix_seconds(1_791_857_172)),
            )),
            right: Some(Entry::new(
                "sub",
                VfsPath::new(r"D:\R\sub"),
                Metadata::directory().with_modified(Timestamp::from_unix_seconds(1_791_857_172)),
            )),
            status: Status::Same,
            children: vec![sub_inner],
            hidden: false,
            expanded: true,
            notes: vec![],
        };
        let emptydir = TreeNode {
            name: "emptydir".to_string(),
            relative_path: "emptydir".to_string(),
            left: None,
            right: Some(Entry::new(
                "emptydir",
                VfsPath::new(r"D:\R\emptydir"),
                Metadata::directory().with_modified(Timestamp::from_unix_seconds(1_791_857_172)),
            )),
            status: Status::RightOnly,
            children: vec![],
            hidden: false,
            expanded: true,
            notes: vec![],
        };
        let files = vec![
            leaf(
                "diff.txt",
                Some(mk_file("diff.txt", 6)),
                Some(mk_file("diff.txt", 6)),
                Status::Same,
            ),
            leaf("leftonly.txt", Some(mk_file("leftonly.txt", 3)), None, Status::LeftOnly),
            leaf("rightonly.txt", None, Some(mk_file("rightonly.txt", 3)), Status::RightOnly),
            leaf(
                "same.txt",
                Some(mk_file("same.txt", 7)),
                Some(mk_file("same.txt", 7)),
                Status::Same,
            ),
            leaf(
                "samesize.bin",
                Some(mk_file("samesize.bin", 4)),
                Some(mk_file("samesize.bin", 4)),
                Status::Same,
            ),
        ];
        FolderComparison {
            left_root: VfsPath::new(r"D:\L"),
            right_root: VfsPath::new(r"D:\R"),
            criteria: Criteria::observed_default(),
            entries: std::iter::once(sub)
                .chain(std::iter::once(emptydir))
                .chain(files)
                .collect(),
            notes: vec![],
            follow_symlinks: false,
            offset_minutes: Some(480),
            expand: crate::expand::ExpandPolicy::All,
            filter: crate::filter::Filter::none(),
        }
    }

    #[test]
    fn xml_layout_parses_and_has_the_observed_skeleton() {
        let xml = render_xml(&sample(), &ReportOptions::default()).unwrap();
        assert!(xml.starts_with('\u{feff}'));
        assert!(xml.contains("<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n"));
        assert!(xml.contains("<bcreport>\r\n"));
        assert!(xml.contains("\t<foldercomp>\r\n"));
        assert!(xml.contains("<ltpath>D:\\L</ltpath>"));
        assert!(xml.contains("<rtpath>D:\\R</rtpath>"));
        assert!(xml.contains("</bcreport>\r\n"));
        // CRLF only.
        assert_eq!(xml.matches('\n').count(), xml.matches("\r\n").count());
    }

    #[test]
    fn xml_uses_one_tab_per_level_like_the_observed_report() {
        let xml = render_xml(&sample(), &ReportOptions::default()).unwrap();
        // Root foldercomp at 1 tab, its children at 2, a side block at 3, name at 4.
        assert!(xml.contains("\t<foldercomp>\r\n"));
        assert!(xml.contains("\t\t<filecomp status=\"same\">\r\n"));
        assert!(xml.contains("\t\t\t<lt>\r\n"));
        assert!(xml.contains("\t\t\t\t<name>same.txt</name>\r\n"));
    }

    #[test]
    fn xml_omits_the_missing_side_entirely() {
        let xml = render_xml(&sample(), &ReportOptions::default()).unwrap();
        let left_only = xml
            .split("<filecomp status=\"ltonly\">")
            .nth(1)
            .and_then(|s| s.split("</filecomp>").next())
            .expect("ltonly block");
        assert!(left_only.contains("<lt>"));
        assert!(!left_only.contains("<rt>"), "a left-only row must not emit an rt block");

        let right_only = xml
            .split("<filecomp status=\"rtonly\">")
            .nth(1)
            .and_then(|s| s.split("</filecomp>").next())
            .expect("rtonly block");
        assert!(right_only.contains("<rt>"));
        assert!(!right_only.contains("<lt>"));
    }

    #[test]
    fn xml_reports_status_tokens_from_the_observed_vocabulary() {
        let xml = render_xml(&sample(), &ReportOptions::default()).unwrap();
        // This sample contains `same`, `ltonly` and `rtonly`.
        for token in ["same", "ltonly", "rtonly"] {
            assert!(xml.contains(&format!("status=\"{token}\"")), "missing {token}");
        }
        // No unobserved token may appear.
        for bad in ["leftolder", "rightolder", "orphan", "conflict"] {
            assert!(!xml.contains(&format!("status=\"{bad}\"")), "leaked {bad}");
        }
    }

    #[test]
    fn xml_emits_the_newer_tokens_when_the_engine_produces_them() {
        let mut c = sample();
        c.entries = vec![
            leaf(
                "same.txt",
                Some(mk_file("same.txt", 4)),
                Some(mk_file("same.txt", 4)),
                Status::Same,
            ),
            leaf(
                "newer-left.txt",
                Some(mk_file("newer-left.txt", 4)),
                Some(mk_file("newer-left.txt", 4)),
                Status::LeftNewer,
            ),
            leaf(
                "newer-right.txt",
                Some(mk_file("newer-right.txt", 4)),
                Some(mk_file("newer-right.txt", 4)),
                Status::RightNewer,
            ),
            leaf(
                "differs.txt",
                Some(mk_file("differs.txt", 4)),
                Some(mk_file("differs.txt", 5)),
                Status::Diff,
            ),
            leaf(
                "left-only.txt",
                Some(mk_file("left-only.txt", 4)),
                None,
                Status::LeftOnly,
            ),
            leaf(
                "right-only.txt",
                None,
                Some(mk_file("right-only.txt", 4)),
                Status::RightOnly,
            ),
        ];
        let xml = render_xml(&c, &ReportOptions::default()).unwrap();
        for token in Status::observed_tokens() {
            assert!(xml.contains(&format!("status=\"{token}\"")), "missing {token}");
        }
    }

    #[test]
    fn xml_directory_size_is_the_subtree_aggregate() {
        let xml = render_xml(&sample(), &ReportOptions::default()).unwrap();
        // `sub` holds one 3-byte file; the observed report shows <size>3</size>.
        let sub = xml
            .split("<name>sub</name>")
            .nth(1)
            .and_then(|s| s.split("</lt>").next())
            .expect("sub block");
        assert!(sub.contains("<size>3</size>"), "got {sub:?}");
        // The empty directory shows zero.
        let empty = xml
            .split("<name>emptydir</name>")
            .nth(1)
            .and_then(|s| s.split("</rt>").next())
            .expect("emptydir block");
        assert!(empty.contains("<size>0</size>"), "got {empty:?}");
    }

    #[test]
    fn xml_modified_time_is_rendered_in_the_local_zone() {
        let xml = render_xml(&sample(), &ReportOptions::default()).unwrap();
        // 1_791_857_172 s = 2026-10-13 02:06:12 UTC = 10:06:12 at UTC+8.
        assert!(xml.contains("<modified>2026/10/13 10:06:12</modified>"), "{xml}");
    }

    #[test]
    fn xml_is_deterministic_for_a_fixed_created_value() {
        let opts = ReportOptions {
            created: Some("2026/10/13 14:17:16".to_string()),
            title: None,
            ignore_unimportant: false,
            filters: None,
        };
        let a = render_xml(&sample(), &opts).unwrap();
        let b = render_xml(&sample(), &opts).unwrap();
        assert_eq!(a, b);
        assert!(a.contains("<bcreport created=\"2026/10/13 14:17:16\">"));
    }

    #[test]
    fn xml_without_a_created_value_omits_the_attribute() {
        let xml = render_xml(&sample(), &ReportOptions::default()).unwrap();
        assert!(xml.contains("<bcreport>\r\n"));
        assert!(!xml.contains("created="));
    }

    #[test]
    fn xml_escapes_special_characters_in_names_and_paths() {
        let mut c = sample();
        c.left_root = VfsPath::new(r"D:\a&b<c>");
        let node = leaf(
            "x&y.txt",
            Some(mk_file("x&y.txt", 1)),
            Some(mk_file("x&y.txt", 1)),
            Status::Same,
        );
        c.entries = vec![node];
        let xml = render_xml(&c, &ReportOptions::default()).unwrap();
        assert!(xml.contains("<ltpath>D:\\a&amp;b&lt;c&gt;</ltpath>"));
        assert!(xml.contains("<name>x&amp;y.txt</name>"));
        // The escaping must still be parseable.
        assert!(!xml.contains("<name>x&y"));
    }

    #[test]
    fn xml_refuses_to_write_a_status_with_no_observed_token() {
        let mut c = sample();
        c.entries = vec![leaf(
            "x.txt",
            Some(mk_file("x.txt", 1)),
            Some(mk_file("x.txt", 1)),
            Status::Unknown,
        )];
        let err = render_xml(&c, &ReportOptions::default()).unwrap_err();
        assert!(matches!(err, DirError::UnrepresentableStatus { .. }), "{err:?}");
    }

    #[test]
    fn unknown_layout_name_is_an_explicit_error() {
        assert!(matches!(
            Layout::parse("html"),
            Err(DirError::UnknownLayout { .. })
        ));
        for (name, expected) in [
            ("side-by-side", Layout::SideBySide),
            ("summary", Layout::Summary),
            ("xml", Layout::Xml),
        ] {
            assert_eq!(Layout::parse(name).unwrap(), expected);
        }
    }

    #[test]
    fn side_by_side_states_that_it_is_not_byte_compatible() {
        let text = render_side_by_side(&sample(), &ReportOptions::default()).unwrap();
        assert!(text.contains("NOT byte-compatible"));
        assert!(text.contains("Left:  D:\\L"));
        assert!(text.contains("Right: D:\\R"));
        // Both sides of a one-sided row: one column is empty.
        assert!(text.contains("leftonly.txt"));
        assert!(text.contains("rightonly.txt"));
    }

    /// Parse the `label : count` body of a summary report into a map, so the
    /// assertion does not depend on the column padding.
    fn parse_summary_counts(text: &str) -> std::collections::HashMap<String, usize> {
        let mut out = std::collections::HashMap::new();
        for line in text.lines() {
            if let Some((label, value)) = line.split_once(':') {
                let label = label.trim();
                if let Ok(n) = value.trim().parse::<usize>() {
                    out.insert(label.to_string(), n);
                }
            }
        }
        out
    }

    #[test]
    fn summary_counts_every_status_including_zeros() {
        let text = render_summary(&sample(), &ReportOptions::default()).unwrap();
        let counts = parse_summary_counts(&text);
        // The sample has: sub + inner (2 same), emptydir (right only),
        // diff.txt / same.txt / samesize.bin (3 same), leftonly.txt, rightonly.txt.
        assert_eq!(counts.get("same"), Some(&5), "{text}");
        assert_eq!(counts.get("different"), Some(&0), "{text}");
        assert_eq!(counts.get("left only"), Some(&1), "{text}");
        assert_eq!(counts.get("right only"), Some(&2), "{text}");
        assert_eq!(counts.get("unknown"), Some(&0), "{text}");
        assert_eq!(counts.get("total"), Some(&8), "{text}");
        assert!(text.contains("NOT byte-compatible"));
    }

    #[test]
    fn summary_declares_the_criteria_in_force() {
        let mut c = sample();
        c.criteria = Criteria::from_content(crate::criteria::ContentCriteria::Crc);
        let text = render_summary(&c, &ReportOptions::default()).unwrap();
        assert!(text.contains("Criteria: CRC"), "{text}");
    }
}
