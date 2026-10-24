//! Importance (M2): the real per-element engine.
//!
//! Replaces the M1 line-level approximation. The observable contract is the
//! **O**-level U1/U2 behaviour tables (`product/verify/probes/U1-FINDINGS.md`,
//! `U2-FINDINGS.md`, runs `u1-probe-*`, `u2-probe-*`, `u2b-probe-*`):
//!
//! 1. A changed pair of lines is **unimportant** (`similar`, folded to `same`
//!    by `ignore-unimportant`) **iff every differing element on it is a
//!    comment or whitespace element** (U1: directive/operator/identifier/
//!    number/string/keyword/case differences are all important).
//! 2. The rule is per *element*, so it holds for mixed lines too: `x = 1; //
//!    note` vs `x = 1; // other` is `similar` (u2 `mixed-trailing-comment`).
//! 3. Whitespace *inside* a string literal is string content, not whitespace,
//!    and is important (u2 `string-internal-ws`). The same holds for regex
//!    literals (u2 `js-regex-ws`) and triple-quoted Python strings, whose
//!    bodies span lines (u2 `py-triple-quote`), so tokenization carries
//!    cross-line state for block comments and multi-line strings.
//! 4. A line whose elements are *entirely* comment/whitespace/empty shares one
//!    alignment class: comments align with comments, blanks and empty lines
//!    (u2 `comment-syntax-swap`, `comment-vs-empty`, `blank-vs-ws`).
//! 5. Python's leading `Indent` element is important (u2 `py-indent`: `x = 1`
//!    vs `    x = 1` is `different`); trailing whitespace is not.
//! 6. Extensions with no known format mask are **plain text**: case-insensitive,
//!    no comments (u2 `foo-*`: `.foo` behaves like `.txt`, not like a syntax
//!    format). This replaces the M1 guess that unknown extensions are
//!    syntax-aware.
//!
//! # What the engine deliberately does NOT model
//!
//! * Which elements are *forced* important in BC's strong sense (immune to
//!   user Weights) — not CLI-observable; the tables above are the contract.
//! * Per-element Weights (`CaseSig`) — the CLI cannot set them.
//! * The 15 other BC formats. Their masks are recorded in [`FORMAT_SPECS`]
//!   but their grammars are not implemented; those extensions fall back to
//!   plain text, which is a **known difference** documented in
//!   `product/docs/07-m2-importance.md` (e.g. a `.pl` POD block would be
//!   unimportant where plain text reports the change as important).
//! * Case policies are per-format and measured (m53b/m53c/m53d probes): the
//!   C-like grammars compare every important element verbatim; XML/HTML fold
//!   every unclaimed span (tag names, attribute names, text) while string
//!   contents and listed HTML entities stay verbatim; SQL folds keywords and
//!   identifiers while string tokens stay verbatim. Plain text folds
//!   everything.
//! * Keyword/operator list exactness. U1 shows every non-comment/
//!   non-whitespace class is important and compared by exact text, so the
//!   keyword/identifier distinction cannot change a verdict; the lists below
//!   are public language facts, kept for element classification only.

/// Which grammar a file is compared under, selected by extension.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Grammar {
    /// Plain text: no tokens, no syntax. Case-insensitive and whitespace-
    /// insensitive by observation (`case-txt`, `ws-*`, u2 `foo-*`).
    PlainText,
    /// The BC "CPP" format (`*.c;*.cc;*.cpp;*.cs;*.h;*.hpp;*.m`).
    Cpp,
    /// The BC "PYTHON" format (`*.py`).
    Python,
    /// The BC "JS" format (`*.js`).
    JavaScript,
    /// The BC "JAVA" format (`*.jav;*.java`), measured by the m53 probe
    /// (`probes/m53_java_grammar.py`, runs `m53-java-*`).
    Java,
    /// The BC "XML" format (`*.xml;*.xsd;*.xsl`): a structural `TXMLFormat`
    /// comparer plus a text grammar, measured by the m53b/m53c/m53d probes
    /// (runs `m53b-xml-html-sql-*`, `m53c-case-model-*`, `m53d-edge-*`).
    Xml,
    /// The BC "HTML" format (`*.ascx;*.asp;*.aspx;*.htm;*.html`).
    Html,
    /// The BC "SQL" format (`*.dsql;*.sql`).
    Sql,
    /// The BC "PAS" format (`*.dpk;*.dpr;*.inc;*.pas`), measured by the
    /// m53e/m53f probes (runs `m53e-batch3-*`, `m53f-edge-*`).
    Pas,
    /// The BC "VB" format (`*.bas;*.cls;*.ctl;*.frm;*.vb;*.vbp;*.vbs`).
    Vb,
    /// The BC "REG" format (`*.ini;*.reg`).
    Reg,
    /// The BC "COBOL" format (`*.cbl;*.cob;*.cpy`).
    Cobol,
    /// The BC "DFM" format (`*.dfm;*.fmx;*.nfm;*.xfm`).
    Dfm,
    /// The BC "PERL" format (`*.pl;*.pm`), measured by the m53g/m53h/m53i/
    /// m53k/m53l probes (runs `m53g-bash-perl-*` et al.).
    Perl,
}

/// Format masks, as BC associates them. Factual file-name associations, not
/// copied grammars; the thirteen implemented grammars are [`Grammar::Cpp`],
/// [`Grammar::Python`], [`Grammar::JavaScript`], [`Grammar::Java`],
/// [`Grammar::Xml`], [`Grammar::Html`], [`Grammar::Sql`], [`Grammar::Pas`],
/// [`Grammar::Vb`], [`Grammar::Reg`], [`Grammar::Cobol`], [`Grammar::Dfm`]
/// and [`Grammar::Perl`]. BASH is NOT a grammar: the m53g-m53j probes show
/// BC compares `.sh` exactly as plain text (see `Grammar::for_path`).
pub const FORMAT_SPECS: &[(&str, &[&str])] = &[
    ("BASH", &["sh"]),
    ("CPP", &["c", "cc", "cpp", "cs", "h", "hpp", "m"]),
    ("COBOL", &["cbl", "cob", "cpy"]),
    ("CSV", &["csv"]),
    ("DFM", &["dfm", "fmx", "nfm", "xfm"]),
    ("PAS", &["dpk", "dpr", "inc", "pas"]),
    ("EXE", &["386", "bcp", "bpl", "dll", "drv", "exe", "ocx", "scr", "sys", "vxd"]),
    ("HTML", &["ascx", "asp", "aspx", "htm", "html"]),
    ("JAVA", &["jav", "java"]),
    ("JS", &["js"]),
    ("MEDIA", &["flac", "m4a", "m4b", "m4p", "m4v", "mp3", "mp4", "mpeg3", "tag", "wav"]),
    ("MSEXCEL", &["xls", "xlsm", "xlsx"]),
    ("MSWORD", &["doc", "docm", "docx", "dot", "dotm", "dotx"]),
    ("OPENOFFICE", &["odb", "odf", "odg", "odm", "odp", "ods", "odt", "otg", "oth", "otp", "ots", "ott", "stc", "std", "sti", "stw", "sxc", "sxd", "sxg", "sxi", "sxm", "sxw"]),
    ("PDF", &["pdf"]),
    ("PERL", &["pl", "pm"]),
    ("PIX", &["bmp", "gif", "ico", "jpg", "png", "tif"]),
    ("PYTHON", &["py"]),
    ("REG", &["ini", "reg"]),
    ("RTF", &["rtf"]),
    ("SORT", &[]),
    ("SQL", &["dsql", "sql"]),
    ("VB", &["bas", "cls", "ctl", "frm", "vb", "vbp", "vbs"]),
    ("XML", &["xml", "xsd", "xsl"]),
];

/// The extensions whose grammar is actually implemented.
const IMPLEMENTED: &[(&str, Grammar)] = &[
    ("CPP", Grammar::Cpp),
    ("PYTHON", Grammar::Python),
    ("JS", Grammar::JavaScript),
    ("JAVA", Grammar::Java),
    ("XML", Grammar::Xml),
    ("HTML", Grammar::Html),
    ("SQL", Grammar::Sql),
    ("PAS", Grammar::Pas),
    ("VB", Grammar::Vb),
    ("REG", Grammar::Reg),
    ("COBOL", Grammar::Cobol),
    ("DFM", Grammar::Dfm),
    ("PERL", Grammar::Perl),
];

impl Grammar {
    /// Pick a grammar from a path's extension.
    ///
    /// Known format masks select their grammar when implemented. Everything
    /// else — including extensions whose BC format exists but is not
    /// implemented here — falls back to plain text, which u2's `foo-*` probes
    /// show is what BC does for unknown extensions; for the not-implemented
    /// known formats this is a recorded known difference, not an observation.
    pub fn for_path(path: &str) -> Grammar {
        let lower = path.to_ascii_lowercase();
        let after_dot = lower.rfind('.').map(|i| i + 1).unwrap_or(usize::MAX);
        let ext = if after_dot == usize::MAX || after_dot == lower.len() {
            return Grammar::PlainText;
        } else {
            &lower[after_dot..]
        };
        // Extensions like `tar.gz` or `name.py` compare on the last suffix
        // only; masks never carry wildcards in BC's observed table beyond the
        // leading `*`, so a plain suffix match is the whole rule.
        for (name, exts) in FORMAT_SPECS {
            if exts.contains(&ext) {
                return IMPLEMENTED
                    .iter()
                    .find(|(n, _)| n == name)
                    .map(|(_, g)| *g)
                    .unwrap_or(Grammar::PlainText);
            }
        }
        // `.txt`/`.text` are in no mask and fall through here.
        Grammar::PlainText
    }

    fn is_plain(self) -> bool {
        matches!(self, Grammar::PlainText)
    }
}

/// The three-way verdict for a matched pair.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Verdict {
    /// Byte-identical lines. Always wins.
    Same,
    /// The lines differ, but only in unimportant elements.
    Similar,
    /// The lines differ in an important way.
    Different,
}

/// Element classes the tokenizer produces.
///
/// Only [`Kind::Comment`] and [`Kind::Whitespace`] are unimportant (U1); every
/// other class — including Python's [`Kind::Indent`] (u2 `py-indent`) — is
/// important. The distinction between the important classes is informational.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Kind {
    Whitespace,
    /// Python's leading-indentation element; important (u2 `py-indent`).
    Indent,
    Comment,
    Str,
    Directive,
    Keyword,
    Identifier,
    Number,
    Operator,
    /// COBOL's fixed-column sequence areas (columns 1-6 and 73-80); measured
    /// unimportant (m53e `cobol-linenum`, `cobol-linenum-trailer`).
    LineNum,
    /// Any character no grammar element claims. Important, like every
    /// non-comment/non-whitespace class (U1).
    Other,
}

/// One token: an element class over a char-index range of the line.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Spanned {
    pub kind: Kind,
    pub start: usize,
    pub end: usize,
}

/// Cross-line tokenizer state: an unterminated block comment (`/*`), an
/// unterminated multi-line string (Python `'''`/`"""`, C++ `@"`), or an
/// unterminated JS regex literal.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
enum Cont {
    #[default]
    None,
    /// Inside `/* ... */`, scanning for this stop text.
    BlockComment(&'static str),
    /// Inside a multi-line string scanning for this stop text.
    MultiStr(&'static str),
    /// Inside a C++ verbatim `@"..."` string, where `""` is an escaped quote.
    VerbatimStr,
    /// Inside a Perl `"`/`'` string (backslash escapes honoured; the element
    /// has StopText but NO StopEOL, so it spans lines — m53g
    /// `perl-dquote-multi-hash`).
    StrQuote(char),
    /// Inside a Perl POD block; the stop marker is a LINE PREFIX
    /// (`"=cut"`/`"=back"`/`"=end"`) and its whole line belongs to the
    /// comment (m53k `pod-stop-tail`).
    Pod(&'static str),
}

/// Tokenize one line, carrying multi-line state.
///
/// Comment/string elements absorb whatever follows their start marker up to
/// the stop marker or end of line, which is what makes u2's block-comment and
/// triple-quote bodies come out entirely unimportant/important respectively.
fn scan_line(line: &str, format: Grammar, cont: &mut Cont) -> Vec<Spanned> {
    if format.is_plain() {
        // Plain text has no elements; the whole line is one "other" span.
        let n = line.chars().count();
        if n == 0 {
            return Vec::new();
        }
        return vec![Spanned { kind: Kind::Other, start: 0, end: n }];
    }
    let chars: Vec<char> = line.chars().collect();
    let n = chars.len();
    let mut out: Vec<Spanned> = Vec::new();
    let mut i = 0usize;

    // Continue an open multi-line element.
    match *cont {
        Cont::BlockComment(stop) => {
            match find(&chars, 0, stop) {
                Some(k) => {
                    out.push(Spanned { kind: Kind::Comment, start: 0, end: k + stop.len() });
                    *cont = Cont::None;
                    i = k + stop.len();
                }
                None => {
                    out.push(Spanned { kind: Kind::Comment, start: 0, end: n });
                    return out;
                }
            }
        }
        Cont::MultiStr(stop) => {
            match find(&chars, 0, stop) {
                Some(k) => {
                    out.push(Spanned { kind: Kind::Str, start: 0, end: k + stop.len() });
                    *cont = Cont::None;
                    i = k + stop.len();
                }
                None => {
                    out.push(Spanned { kind: Kind::Str, start: 0, end: n });
                    return out;
                }
            }
        }
        Cont::VerbatimStr => {
            match find_verbatim_close(&chars, 0) {
                Some(k) => {
                    out.push(Spanned { kind: Kind::Str, start: 0, end: k + 1 });
                    *cont = Cont::None;
                    i = k + 1;
                }
                None => {
                    out.push(Spanned { kind: Kind::Str, start: 0, end: n });
                    return out;
                }
            }
        }
        Cont::StrQuote(quote) => {
            // Continuation line: the string content starts at column 0 —
            // the closing quote may be the very first character.
            let mut j = 0;
            let close = loop {
                if j >= n {
                    break None;
                }
                if chars[j] == '\\' {
                    j += 2;
                    continue;
                }
                if chars[j] == quote {
                    break Some(j + 1);
                }
                j += 1;
            };
            match close {
                Some(k) => {
                    out.push(Spanned { kind: Kind::Str, start: 0, end: k });
                    *cont = Cont::None;
                    i = k;
                }
                None => {
                    out.push(Spanned { kind: Kind::Str, start: 0, end: n });
                    return out;
                }
            }
        }
        Cont::Pod(stop) => {
            // The stop marker is a line PREFIX and its whole line belongs to
            // the comment (m53k: `x =cut y` vs `x =cut z` body-differs, and
            // `=cut Z1` vs `=cut Z2` is the pair that decides line ownership).
            if starts_with(&chars, 0, &pod_stop_chars(stop)) {
                out.push(Spanned { kind: Kind::Comment, start: 0, end: n });
                *cont = Cont::None;
            } else {
                out.push(Spanned { kind: Kind::Comment, start: 0, end: n });
            }
            return out;
        }
        Cont::None => {}
    }

    // Python: leading whitespace before content is the `Indent` element
    // (important, u2 `py-indent`); a `#` after it makes the whole prefix part
    // of the comment (`\s*#` in BC's PYTHON grammar). Whitespace running to
    // end of line is ordinary unimportant whitespace.
    if format == Grammar::Python && i == 0 && n > 0 && chars[0].is_whitespace() {
        let mut j = 0;
        while j < n && chars[j].is_whitespace() {
            j += 1;
        }
        if j == n {
            out.push(Spanned { kind: Kind::Whitespace, start: 0, end: n });
            return out;
        }
        if chars[j] == '#' {
            out.push(Spanned { kind: Kind::Comment, start: 0, end: n });
            return out;
        }
        out.push(Spanned { kind: Kind::Indent, start: 0, end: j });
        i = j;
    }

    while i < n {
        let c = chars[i];
        // Perl POD blocks open at column 0 (`^=(head\d|item|pod)` /
        // `^=over` / `^=begin`, m53g/m53k): the opener line is fully a
        // comment and the block closes on the first following line that
        // STARTS with the stop marker — that stop line belongs to the
        // comment in full (`=cut Z1` vs `=cut Z2` = similar) and a stop
        // marker mid-line does NOT close (`x =cut y` keeps the block open).
        if format == Grammar::Perl && i == 0 && c == '=' {
            if let Some(stop) = pod_start(&chars) {
                out.push(Spanned { kind: Kind::Comment, start: 0, end: n });
                *cont = Cont::Pod(stop);
                return out;
            }
        }
        // Whitespace runs are unimportant everywhere.
        if c.is_whitespace() {
            let j = i;
            while i < n && chars[i].is_whitespace() {
                i += 1;
            }
            out.push(Spanned { kind: Kind::Whitespace, start: j, end: i });
            continue;
        }
        // Line comments.
        if (format == Grammar::Cpp
            || format == Grammar::JavaScript
            || format == Grammar::Java
            || format == Grammar::Pas)
            && c == '/'
            && i + 1 < n
            && chars[i + 1] == '/'
        {
            out.push(Spanned { kind: Kind::Comment, start: i, end: n });
            return out;
        }
        // Block comments: `/* ... */`, possibly spanning lines.
        if (format == Grammar::Cpp
            || format == Grammar::JavaScript
            || format == Grammar::Java)
            && c == '/'
            && i + 1 < n
            && chars[i + 1] == '*'
        {
            match find(&chars, i + 2, "*/") {
                Some(k) => {
                    out.push(Spanned { kind: Kind::Comment, start: i, end: k + 2 });
                    i = k + 2;
                }
                None => {
                    out.push(Spanned { kind: Kind::Comment, start: i, end: n });
                    *cont = Cont::BlockComment("*/");
                    return out;
                }
            }
            continue;
        }
        // Python `#` comments.
        if format == Grammar::Python && c == '#' {
            out.push(Spanned { kind: Kind::Comment, start: i, end: n });
            return out;
        }
        // Strings. Triple quotes are checked before single quotes (longer
        // start marker wins).
        if format == Grammar::Python && (c == '\'' || c == '"') {
            let triple: &'static str = if c == '\'' { "'''" } else { "\"\"\"" };
            let tc: Vec<char> = triple.chars().collect();
            if starts_with(&chars, i, &tc) {
                match find(&chars, i + 3, triple) {
                    Some(k) => {
                        out.push(Spanned { kind: Kind::Str, start: i, end: k + 3 });
                        i = k + 3;
                    }
                    None => {
                        out.push(Spanned { kind: Kind::Str, start: i, end: n });
                        *cont = Cont::MultiStr(triple);
                        return out;
                    }
                }
                continue;
            }
            if let Some(k) = scan_quoted(&chars, i, c, true) {
                out.push(Spanned { kind: Kind::Str, start: i, end: k });
                i = k;
                continue;
            }
            // StopEOL string (BC's PYTHON single/double String elements set
            // `StopEOL="True"`): an unterminated quote is one string element
            // running to the end of the line, so whitespace, `#` and `/*`
            // inside it stay *string content* — important, and never re-read
            // as a comment or a new block comment (u2 `string-unterminated`,
            // `string-internal-ws`; the leak probe on `a = "x /*` shows why
            // the rest of the file must stay out of `BlockComment` state).
            // The element does NOT span lines: the next line tokenizes fresh.
            out.push(Spanned { kind: Kind::Str, start: i, end: n });
            return out;
        }
        if format == Grammar::JavaScript && (c == '\'' || c == '"') {
            if let Some(k) = scan_quoted(&chars, i, c, true) {
                out.push(Spanned { kind: Kind::Str, start: i, end: k });
                i = k;
                continue;
            }
            out.push(Spanned { kind: Kind::Str, start: i, end: n });
            return out;
        }
        // Java strings and char literals: both quote kinds carry backslash
        // escapes (Escape=92) and StopEOL (m53 `str-escape`, `char-*`): a
        // closed literal ends at its unescaped quote, an unterminated one runs
        // to end of line as string content — so `//` and `/*` inside it stay
        // *important string text* and never open a comment, and no cross-line
        // state is set (m53 `str-vs-block`: the next line tokenizes fresh).
        if format == Grammar::Java && (c == '\'' || c == '"') {
            if let Some(k) = scan_quoted(&chars, i, c, true) {
                out.push(Spanned { kind: Kind::Str, start: i, end: k });
                i = k;
                continue;
            }
            out.push(Spanned { kind: Kind::Str, start: i, end: n });
            return out;
        }
        // XML/HTML: `<!-- ... -->` comments span lines and an unterminated
        // `<!--` carries the comment state to the next line (m53b
        // `xml-comment-span`, `xml-comment-open`). Strings declare NO Escape
        // attribute: `\` is inert, so `"x\"` closes at the second quote
        // (m53c `xml-no-escape` = similar), and StopEOL runs an unterminated
        // quote to end of line with no cross-line state.
        if format == Grammar::Xml || format == Grammar::Html {
            if c == '<' && starts_with(&chars, i, &['<', '!', '-', '-']) {
                match find(&chars, i + 4, "-->") {
                    Some(k) => {
                        out.push(Spanned { kind: Kind::Comment, start: i, end: k + 3 });
                        i = k + 3;
                    }
                    None => {
                        out.push(Spanned { kind: Kind::Comment, start: i, end: n });
                        *cont = Cont::BlockComment("-->");
                        return out;
                    }
                }
                continue;
            }
            if c == '"' || c == '\'' {
                if let Some(k) = scan_quoted(&chars, i, c, false) {
                    out.push(Spanned { kind: Kind::Str, start: i, end: k });
                    i = k;
                    continue;
                }
                out.push(Spanned { kind: Kind::Str, start: i, end: n });
                return out;
            }
        }
        // HTML character references. A LISTED named reference (matched
        // case-sensitively, m53d) is a keyword element and compares
        // verbatim; an unlisted `&name;` stays unclaimed text, which folds
        // under the XML/HTML case policy below.
        if format == Grammar::Html && c == '&' {
            if let Some(k) = match_html_entity(&chars, i) {
                out.push(Spanned { kind: Kind::Keyword, start: i, end: k });
                i = k;
                continue;
            }
        }
        // SQL: `--` to end of line, `/* ... */` across lines. Strings are
        // COMPLETE-MATCH elements (a regex, no StopEOL): an unterminated
        // quote matches nothing and falls through to ordinary tokenizing, so
        // a later `--` is still a real comment (m53b
        // `sql-str-unterminated-comment` = similar) while a matched string
        // absorbs `--` as content (m53c `sql-string-absorbs-comment`).
        // The optional `n`/`N` prefix is part of the string token and
        // compares verbatim (m53d `sql-nprefix-case` = different).
        if format == Grammar::Sql {
            if c == '-' && i + 1 < n && chars[i + 1] == '-' {
                out.push(Spanned { kind: Kind::Comment, start: i, end: n });
                return out;
            }
            if c == '/' && i + 1 < n && chars[i + 1] == '*' {
                match find(&chars, i + 2, "*/") {
                    Some(k) => {
                        out.push(Spanned { kind: Kind::Comment, start: i, end: k + 2 });
                        i = k + 2;
                    }
                    None => {
                        out.push(Spanned { kind: Kind::Comment, start: i, end: n });
                        *cont = Cont::BlockComment("*/");
                        return out;
                    }
                }
                continue;
            }
            if c == '\'' || c == '"' || ((c == 'n' || c == 'N') && i + 1 < n
                && (chars[i + 1] == '\'' || chars[i + 1] == '"'))
            {
                if let Some(k) = scan_sql_string(&chars, i) {
                    out.push(Spanned { kind: Kind::Str, start: i, end: k });
                    i = k;
                    continue;
                }
            }
        }
        if format == Grammar::Cpp {
            if c == '@' && i + 1 < n && chars[i + 1] == '"' {
                match find_verbatim_close(&chars, i + 2) {
                    Some(k) => {
                        out.push(Spanned { kind: Kind::Str, start: i, end: k + 1 });
                        i = k + 1;
                    }
                    None => {
                        out.push(Spanned { kind: Kind::Str, start: i, end: n });
                        *cont = Cont::VerbatimStr;
                        return out;
                    }
                }
                continue;
            }
            if c == '\'' || c == '"' {
                if let Some(k) = scan_quoted(&chars, i, c, true) {
                    out.push(Spanned { kind: Kind::Str, start: i, end: k });
                    i = k;
                    continue;
                }
                // Same StopEOL rule as the Python/JS quote branches above:
                // `char *s = "abc` (u2 `string-unterminated`) is one string
                // to the line end, and the `"` never re-opens a `//`/`/*`
                // comment scan on the tail of the line.
                out.push(Spanned { kind: Kind::Str, start: i, end: n });
                return out;
            }
            // Preprocessor directives: a `#` followed by a known directive
            // word. An unrecognised `#` is an ordinary character.
            if c == '#' {
                if let Some(k) = match_word_list(&chars, i + 1, CPP_DIRECTIVES) {
                    out.push(Spanned { kind: Kind::Directive, start: i, end: k });
                    i = k;
                    continue;
                }
            }
        }
        // Pascal: `{$...}` compiler directives are IMPORTANT (m53e
        // `pas-directive-vs-comment` = different); `{...}` and `(*...*)`
        // comments span lines and persist when unterminated (m53e
        // `pas-comment-brace-span`, m53f `pas-paren-comment-span`). Strings
        // are COMPLETE-MATCH elements (`'..'` with `''` doubling, `#65` char
        // literals, no backslash escape), so an unterminated `'` falls
        // through to ordinary tokenizing and a later `//` stays a real
        // comment (m53e `pas-string-unterminated-comment` = similar). An
        // unterminated directive is EOL-bounded here: its persistence would
        // be verdict-invisible either way (directive and code are both
        // important classes), so the simpler reading is taken.
        if format == Grammar::Pas {
            if c == '{' {
                if i + 1 < n && chars[i + 1] == '$' {
                    match find(&chars, i + 2, "}") {
                        Some(k) => {
                            out.push(Spanned { kind: Kind::Directive, start: i, end: k + 1 });
                            i = k + 1;
                        }
                        None => {
                            out.push(Spanned { kind: Kind::Directive, start: i, end: n });
                            return out;
                        }
                    }
                    continue;
                }
                match find(&chars, i + 1, "}") {
                    Some(k) => {
                        out.push(Spanned { kind: Kind::Comment, start: i, end: k + 1 });
                        i = k + 1;
                    }
                    None => {
                        out.push(Spanned { kind: Kind::Comment, start: i, end: n });
                        *cont = Cont::BlockComment("}");
                        return out;
                    }
                }
                continue;
            }
            if c == '(' && i + 1 < n && chars[i + 1] == '*' {
                match find(&chars, i + 2, "*)") {
                    Some(k) => {
                        out.push(Spanned { kind: Kind::Comment, start: i, end: k + 2 });
                        i = k + 2;
                    }
                    None => {
                        out.push(Spanned { kind: Kind::Comment, start: i, end: n });
                        *cont = Cont::BlockComment("*)");
                        return out;
                    }
                }
                continue;
            }
            if c == '\'' {
                if let Some(k) = scan_pascal_string(&chars, i) {
                    out.push(Spanned { kind: Kind::Str, start: i, end: k });
                    i = k;
                    continue;
                }
            }
            if c == '#' {
                let mut j = i + 1;
                while j < n && chars[j].is_ascii_digit() {
                    j += 1;
                }
                if j > i + 1 {
                    out.push(Spanned { kind: Kind::Str, start: i, end: j });
                    i = j;
                    continue;
                }
            }
        }
        // VB: `'` and a word-shaped `rem` followed by space/tab/EOL comment
        // to end of line — `rem` matches UNANCHORED, so `x = 1 rem y` is a
        // comment from `rem` on (m53e `vb-rem-midline` = similar). Strings
        // are regexes with an EOL-anchored fallback (`"([^"]|"")*$`), so an
        // unterminated `"` still absorbs to end of line with `""` doubling
        // inside (m53e `vb-string-unterminated*`).
        if format == Grammar::Vb {
            if c == '\'' {
                out.push(Spanned { kind: Kind::Comment, start: i, end: n });
                return out;
            }
            if c == '"' {
                let k = scan_vb_string(&chars, i);
                out.push(Spanned { kind: Kind::Str, start: i, end: k });
                i = k;
                continue;
            }
        }
        // REG (ini): comments are LINE-ANCHORED (`^\s*;`) — a `;` after any
        // content stays unclaimed text (m53e `reg-midline-semicolon` =
        // different); strings carry Escape=92 and StopEOL.
        if format == Grammar::Reg {
            if c == ';' && out.iter().all(|s| s.kind == Kind::Whitespace) {
                out.push(Spanned { kind: Kind::Comment, start: i, end: n });
                return out;
            }
            if c == '"' {
                if let Some(k) = scan_quoted(&chars, i, c, true) {
                    out.push(Spanned { kind: Kind::Str, start: i, end: k });
                    i = k;
                    continue;
                }
                out.push(Spanned { kind: Kind::Str, start: i, end: n });
                return out;
            }
        }
        // COBOL: fixed columns. Columns 1-6 of digits and columns 73-80 are
        // LineNum elements, measured UNIMPORTANT (m53e `cobol-linenum`,
        // `cobol-linenum-trailer` = similar); a `*` in column 7 makes the
        // rest of the line a comment (`^.{6}\*`, m53e `cobol-comment-col7`)
        // while a `*` anywhere else stays an operator (m53f). `"` strings
        // carry Escape=92 and StopEOL.
        if format == Grammar::Cobol {
            if i == 0 && n >= 6 && chars[..6].iter().all(|c| c.is_ascii_digit()) {
                out.push(Spanned { kind: Kind::LineNum, start: 0, end: 6 });
                i = 6;
                continue;
            }
            if i == 72 && n > 72 {
                let e = n.min(80);
                out.push(Spanned { kind: Kind::LineNum, start: 72, end: e });
                i = e;
                continue;
            }
            if i == 6 && c == '*' {
                out.push(Spanned { kind: Kind::Comment, start: i, end: n });
                return out;
            }
            if c == '"' {
                if let Some(k) = scan_quoted(&chars, i, c, true) {
                    out.push(Spanned { kind: Kind::Str, start: i, end: k });
                    i = k;
                    continue;
                }
                out.push(Spanned { kind: Kind::Str, start: i, end: n });
                return out;
            }
        }
        // DFM: `#65` and `'..'` string regexes (complete match, `''`
        // doubling); there is NO comment element — `{` stays unclaimed text
        // (m53e `dfm-no-comment` = different).
        if format == Grammar::Dfm && (c == '\'' || c == '#') {
            if c == '\'' {
                if let Some(k) = scan_pascal_string(&chars, i) {
                    out.push(Spanned { kind: Kind::Str, start: i, end: k });
                    i = k;
                    continue;
                }
            }
            let mut j = i + 1;
            while j < n && chars[j].is_ascii_digit() {
                j += 1;
            }
            if j > i + 1 {
                out.push(Spanned { kind: Kind::Str, start: i, end: j });
                i = j;
                continue;
            }
        }
        // Perl (m53g/m53i/m53k/m53l/m53m probes): `#` comments to EOL. POD
        // blocks (`=pod`/`=head1`/`=item` -> `=cut`, `=over` -> `=back`) are
        // LINE-ANCHORED comment spans whose start and stop lines are fully
        // comment: `x =cut y` does NOT stop a block (the stop must start the
        // line), while the stop line's tail belongs to it (`=cut Z1` vs
        // `=cut Z2` = similar, m53k). `"`/`'` strings carry Escape=92 and NO
        // StopEOL: they span lines and absorb `#` (m53g
        // `perl-dquote-multi-hash`). The quote-like forms apply as COMPLETE
        // matches (`q(...)`/`qq(...)`/`s/.../.../`; NO `#` delimiters —
        // m53l `s#a#b#c#d#` is not a string), and the division-shaped
        // `/[^/]*/` regex is real: `a / b / c` pairs `/ b /` (m53g). Every
        // span compares VERBATIM: `CaseSensitive=False` changes tokenization
        // only, not comparison — `$Name` vs `$name`, `@Items` vs `@items`
        // and even bare `Name` vs `name` all measure different (m53m), so
        // the perl branch below is the one grammar where that flag does not
        // imply folding (see `span_folds`).
        if format == Grammar::Perl {
            // An unclaimed `rem`-like path is impossible here; POD detection
            // happens before tokenizing (below) for line-anchored starts.
            if c == '#' {
                out.push(Spanned { kind: Kind::Comment, start: i, end: n });
                return out;
            }
            if c == '"' || c == '\'' {
                if let Some(k) = scan_quoted(&chars, i, c, true) {
                    out.push(Spanned { kind: Kind::Str, start: i, end: k });
                    i = k;
                    continue;
                }
                // StopText without StopEOL: the string is still OPEN — the
                // rest of the line is its content and the next line
                // continues it (`#` included).
                out.push(Spanned { kind: Kind::Str, start: i, end: n });
                *cont = Cont::StrQuote(c);
                return out;
            }
            // Quote-like forms, then the bare `/.../` regex element.
            if (c == 'q' || c == 's') && i + 1 < n && chars[i + 1] == '(' {
                if let Some(k) = scan_bracketed(&chars, i, '(', ')') {
                    out.push(Spanned { kind: Kind::Str, start: i, end: k });
                    i = k;
                    continue;
                }
            }
            if c == 'q' && i + 2 < n && (chars[i + 1] == 'q' || chars[i + 1] == 'w') {
                if let Some(k) = scan_bracketed(&chars, i, '(', ')') {
                    out.push(Spanned { kind: Kind::Str, start: i, end: k });
                    i = k;
                    continue;
                }
            }
            // `(s|tr)/([^/]*/){2}`: `s/a/b/` or `tr/a/b/`.
            if (c == 's' && i + 1 < n && chars[i + 1] == '/')
                || (c == 't' && i + 2 < n && chars[i + 1] == 'r' && chars[i + 2] == '/')
            {
                let slash = if c == 's' { i + 1 } else { i + 2 };
                if let Some(k) = scan_slash_form(&chars, slash) {
                    out.push(Spanned { kind: Kind::Str, start: i, end: k });
                    i = k;
                    continue;
                }
            }
            if c == '/' {
                if let Some(k) = scan_slash_regex(&chars, i) {
                    out.push(Spanned { kind: Kind::Str, start: i, end: k });
                    i = k;
                    continue;
                }
            }
        }
        // JS regex literal: `/.../flags` with at least one flag. The flag
        // requirement is what keeps `a / b / c` from being read as a regex
        // (u2 `js-regex-literal`, `js-regex-ws`).
        if format == Grammar::JavaScript && c == '/' {
            if let Some(k) = scan_js_regex(&chars, i) {
                out.push(Spanned { kind: Kind::Str, start: i, end: k });
                i = k;
                continue;
            }
        }
        // Word runs: numbers, keywords, identifiers.
        if is_word_char(c, format) {
            let j = i;
            if c.is_ascii_digit() {
                i = scan_number(&chars, i, format);
                out.push(Spanned { kind: Kind::Number, start: j, end: i });
            } else {
                i = scan_word(&chars, i, format);
                let text: String = chars[j..i].iter().collect();
                // VB's `rem` comment element matches UNANCHORED: the word
                // `rem` (any case) followed by space/tab/EOL comments out the
                // rest of the line, wherever it appears (m53e
                // `vb-rem-midline` = similar).
                if format == Grammar::Vb
                    && text.eq_ignore_ascii_case("rem")
                    && (i >= n || chars[i] == ' ' || chars[i] == '\t')
                {
                    out.push(Spanned { kind: Kind::Comment, start: j, end: n });
                    return out;
                }
                let kind = if matches_keyword(format, &text) && word_boundary(&chars, i) {
                    Kind::Keyword
                } else {
                    Kind::Identifier
                };
                out.push(Spanned { kind, start: j, end: i });
            }
            continue;
        }
        // Operators (longest item first), then any other character.
        if let Some(k) = match_word_list(&chars, i, operators(format)) {
            out.push(Spanned { kind: Kind::Operator, start: i, end: k });
            i = k;
            continue;
        }
        out.push(Spanned { kind: Kind::Other, start: i, end: i + 1 });
        i += 1;
    }
    out
}

fn find(chars: &[char], from: usize, stop: &str) -> Option<usize> {
    let stop: Vec<char> = stop.chars().collect();
    if stop.is_empty() || chars.len() < stop.len() {
        return None;
    }
    (from..=chars.len() - stop.len()).find(|&k| chars[k..k + stop.len()] == stop[..])
}

fn starts_with(chars: &[char], at: usize, prefix: &[char]) -> bool {
    chars.len() >= at + prefix.len() && chars[at..at + prefix.len()] == *prefix
}

/// Scan a `'`/`"` string starting at `at` (which holds the quote). `escape`
/// enables backslash escapes. Returns the index *past* the closing quote, or
/// None when the line ends first (StopEOL strings simply end at the line end,
/// which the caller renders as a string to EOL).
fn scan_quoted(chars: &[char], at: usize, quote: char, escape: bool) -> Option<usize> {
    let mut j = at + 1;
    while j < chars.len() {
        if escape && chars[j] == '\\' {
            j += 2;
            continue;
        }
        if chars[j] == quote {
            return Some(j + 1);
        }
        j += 1;
    }
    None
}

/// End of a C++ verbatim `@"..."` string: a `"` not doubled.
fn find_verbatim_close(chars: &[char], from: usize) -> Option<usize> {
    let mut j = from;
    while j < chars.len() {
        if chars[j] == '"' {
            if j + 1 < chars.len() && chars[j + 1] == '"' {
                j += 2;
                continue;
            }
            return Some(j);
        }
        j += 1;
    }
    None
}

/// An HTML character reference starting at `at` (which holds `&`): the
/// numeric form `&#123;` by shape, or a named reference matched
/// case-sensitively against [`HTML_ENTITIES`]. Returns the index past `;`.
fn match_html_entity(chars: &[char], at: usize) -> Option<usize> {
    if !starts_with(chars, at, &['&']) {
        return None;
    }
    let mut j = at + 1;
    if j < chars.len() && chars[j] == '#' {
        j += 1;
        let digits = j;
        while j < chars.len() && chars[j].is_ascii_digit() {
            j += 1;
        }
        if j > digits && j < chars.len() && chars[j] == ';' {
            return Some(j + 1);
        }
        return None;
    }
    let name = j;
    while j < chars.len() && chars[j].is_ascii_alphanumeric() {
        j += 1;
    }
    if j == name || j >= chars.len() || chars[j] != ';' {
        return None;
    }
    let text: String = chars[at..=j].iter().collect();
    if HTML_ENTITIES.contains(&text.as_str()) {
        return Some(j + 1);
    }
    None
}

/// A SQL string literal starting at `at`: optional `n`/`N` prefix, then a
/// quote, then content of escapes (`\x`), doubled quotes (`''`) or ordinary
/// characters, closed by the matching quote. COMPLETE match only — `None`
/// means the element does not apply and tokenizing falls through.
fn scan_sql_string(chars: &[char], at: usize) -> Option<usize> {
    let mut j = at;
    if (chars[j] == 'n' || chars[j] == 'N')
        && j + 1 < chars.len()
        && (chars[j + 1] == '\'' || chars[j + 1] == '"')
    {
        j += 1;
    }
    let quote = chars[j];
    if quote != '\'' && quote != '"' {
        return None;
    }
    j += 1;
    while j < chars.len() {
        match chars[j] {
            '\\' => j += 2,
            c if c == quote => {
                if j + 1 < chars.len() && chars[j + 1] == quote {
                    j += 2;
                } else {
                    return Some(j + 1);
                }
            }
            _ => j += 1,
        }
    }
    None
}

/// A Pascal/DFM string literal starting at `at` (which holds `'`): content
/// of ordinary characters or doubled quotes (`''`), closed by the quote —
/// backslashes are ORDINARY content (no Escape attribute). COMPLETE match
/// only; `None` means the element does not apply.
fn scan_pascal_string(chars: &[char], at: usize) -> Option<usize> {
    let mut j = at + 1;
    while j < chars.len() {
        if chars[j] == '\'' {
            if j + 1 < chars.len() && chars[j + 1] == '\'' {
                j += 2;
            } else {
                return Some(j + 1);
            }
        } else {
            j += 1;
        }
    }
    None
}

/// A VB string literal starting at `at` (which holds `"`): content of
/// ordinary characters or doubled quotes (`""`), closed by the quote with an
/// optional `c` suffix. The grammar's EOL-anchored fallback
/// (`"([^"]|"")*$`) always matches, so an unterminated `"` absorbs to end of
/// line (m53e `vb-string-unterminated`).
fn scan_vb_string(chars: &[char], at: usize) -> usize {
    let mut j = at + 1;
    while j < chars.len() {
        if chars[j] == '"' {
            if j + 1 < chars.len() && chars[j + 1] == '"' {
                j += 2;
                continue;
            }
            j += 1;
            if j < chars.len() && (chars[j] == 'c' || chars[j] == 'C') {
                j += 1;
            }
            return j;
        }
        j += 1;
    }
    chars.len()
}

/// JS regex literal starting at `at` (which holds `/`): a closed `/.../` with
/// at least one `gimuysd`-flag character after it, no newline possible (we
/// are within one line), backslash escapes honoured.
fn scan_js_regex(chars: &[char], at: usize) -> Option<usize> {
    let mut j = at + 1;
    let mut closed = None;
    while j < chars.len() {
        match chars[j] {
            '\\' => j += 2,
            '/' => {
                closed = Some(j);
                break;
            }
            _ => j += 1,
        }
    }
    let close = closed?;
    let mut k = close + 1;
    let mut flags = 0;
    while k < chars.len() && "gimuysd".contains(chars[k]) {
        flags += 1;
        k += 1;
    }
    if flags == 0 {
        return None;
    }
    Some(k)
}

fn is_word_char(c: char, format: Grammar) -> bool {
    c.is_ascii_alphanumeric() || c == '_' || (format == Grammar::JavaScript && c == '$')
}

fn scan_word(chars: &[char], at: usize, format: Grammar) -> usize {
    let mut j = at;
    while j < chars.len() && is_word_char(chars[j], format) {
        j += 1;
    }
    j
}

/// Number shapes, close enough for classification (verbatim text is what the
/// verdict compares): decimal digits, optional hex prefix forms (`0x...`),
/// optional fraction and exponent. Python, Java, SQL, XML, HTML, Pascal, VB,
/// DFM, COBOL and REG grammars declare no `0x` hex number element, so `0x1f`
/// tokenizes as a number followed by an identifier there — informational
/// only; the concatenated important text is identical.
fn scan_number(chars: &[char], at: usize, format: Grammar) -> usize {
    let hex = !matches!(
        format,
        Grammar::Python
            | Grammar::Java
            | Grammar::Sql
            | Grammar::Xml
            | Grammar::Html
            | Grammar::Pas
            | Grammar::Vb
            | Grammar::Dfm
            | Grammar::Cobol
            | Grammar::Reg
    ) && chars[at] == '0'
        && at + 1 < chars.len()
        && (chars[at + 1] == 'x' || chars[at + 1] == 'X');
    if hex {
        let mut j = at + 2;
        while j < chars.len() && chars[j].is_ascii_hexdigit() {
            j += 1;
        }
        return j;
    }
    let mut j = scan_word(chars, at, format);
    // Fraction and exponent may extend past the identifier-ish run (`.` is
    // not a word character).
    if j < chars.len() && chars[j] == '.' && j + 1 < chars.len() && chars[j + 1].is_ascii_digit() {
        j += 1;
        j = scan_word(chars, j, format);
    }
    if j < chars.len() && (chars[j] == 'e' || chars[j] == 'E') {
        let mut k = j + 1;
        if k < chars.len() && (chars[k] == '+' || chars[k] == '-') {
            k += 1;
        }
        if k < chars.len() && chars[k].is_ascii_digit() {
            j = scan_word(chars, k, format);
        }
    }
    j
}

fn word_boundary(chars: &[char], at: usize) -> bool {
    at >= chars.len() || !is_word_char(chars[at], Grammar::JavaScript)
}

/// Longest item of `list` matching at `at`; the returned index is past the
/// item. A word-shaped item must end on a word boundary.
fn match_word_list(chars: &[char], at: usize, list: &[&str]) -> Option<usize> {
    let mut best: Option<usize> = None;
    for item in list {
        let ic: Vec<char> = item.chars().collect();
        if !starts_with(chars, at, &ic) {
            continue;
        }
        let end = at + ic.len();
        let boundary = ic.last().map(|c| !is_word_char(*c, Grammar::JavaScript)).unwrap_or(true)
            || word_boundary(chars, end);
        if !boundary {
            continue;
        }
        if best.map(|b| end > b).unwrap_or(true) {
            best = Some(end);
        }
    }
    best
}

fn matches_keyword(format: Grammar, word: &str) -> bool {
    let list: &[&str] = match format {
        Grammar::PlainText => &[],
        Grammar::Cpp => CPP_KEYWORDS,
        Grammar::Python => PYTHON_KEYWORDS,
        Grammar::JavaScript => JS_KEYWORDS,
        Grammar::Java => JAVA_KEYWORDS,
        // XML/HTML/SQL word runs carry no keyword element in this engine:
        // XML has none, HTML tags fold as unclaimed text anyway (the only
        // case-sensitive keyword class is the entity table, matched in
        // `scan_line`), and SQL keywords and identifiers fold identically.
        // PAS/VB/DFM/COBOL keywords fold identically to identifiers, and
        // REG's `dword`/`hex` keywords are case-sensitive and compare
        // verbatim like every other span (m53f `reg-keyword-case`).
        Grammar::Xml | Grammar::Html | Grammar::Sql | Grammar::Pas | Grammar::Vb
        | Grammar::Dfm | Grammar::Cobol | Grammar::Reg | Grammar::Perl => &[],
    };
    list.contains(&word)
}

fn operators(format: Grammar) -> &'static [&'static str] {
    match format {
        // Longest first so multi-character operators win.
        Grammar::Python => &[
            "**=", "//=", "...", "**", "//", "<<", ">>", "<=", ">=", "==", "!=", "->", ":=", "+=",
            "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>=", "+", "-", "*", "/", "%", "@",
            "<", ">", "=", "!", "&", "|", "^", "~", "(", ")", "[", "]", "{", "}", ",", ":", ".",
            ";",
        ],
        Grammar::JavaScript => &[
            "===", "!==", "**=", "...", "&&=", "||=", "??=", "<<=", ">>=", ">>>", "**", "==", "!=",
            "<=", ">=", "&&", "||", "??", "?.", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=",
            "<<", ">>", "=>", "++", "--", "+", "-", "*", "/", "%", "&", "|", "^", "~", "!", "<",
            ">", "=", "?", ":", ";", ",", ".", "(", ")", "[", "]", "{", "}",
        ],
        Grammar::Cpp => &["{", "}", "(", ")", "[", "]", ".", ":", ",", ";", "!", "?", "|", "&", "+", "-", "/", "*", "=", ">", "<", "%", "^", "~", "@"],
        Grammar::Java => &[
            ">>>=", ">>>", "<<=", ">>=", "==", "+=", "<=", "-=", ">=", "*=", "!=", "&&", "/=",
            "||", "|=", "++", "^=", "--", "%=", "<<", ">>", "(", ")", "{", "}", "[", "]", ";",
            ",", ".", "=", ">", "<", "-", "*", "!", "~", "/", "?", "|", ":", "^", "%",
        ],
        Grammar::Xml => &["/>", "<", ">"],
        Grammar::Html => &["=", ","],
        Grammar::Sql => &[
            "<>", "<=", ">=", "||", "(", ")", "[", "]", ",", ";", "+", "-", "*", "/", "%", "&",
            "|", "^", "~", "<", ">", "=", ".",
        ],
        Grammar::Pas => &[
            ":=", "..", "(", ")", "[", "]", ".", ";", ":", "=", "+", "-", "*", "/", "<", ">",
            "@", "^",
        ],
        Grammar::Vb => &[
            ":=", "<<=", ">>=", "(", ")", ".", "!", "#", ",", ":", "&", "+", "-", "*", "/", "\\",
            "^", "<", ">", "=", ";",
        ],
        Grammar::Reg => &["=", ":"],
        Grammar::Cobol => &["<=", ">=", "**", "<", ">", "+", "-", "*", "/", "=", "@"],
        Grammar::Dfm => &["(", ")", "[", "]", "=", "+", ">", "<"],
        Grammar::Perl => &[
            "\\\"", "\\'", "&", "|", "<", ">", "+", "-", "*", "/", "\\", "%", "^", "~", "!",
            "?", ",", "=", ".",
        ],
        Grammar::PlainText => &[],
    }
}

/// Keyword lists are public language facts used only for element
/// classification. They cannot change verdicts (see the module header): every
/// non-comment, non-whitespace class is important and compared by exact text.
const CPP_KEYWORDS: &[&str] = &[
    "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor", "bool", "break",
    "case", "catch", "char", "char8_t", "char16_t", "char32_t", "class", "compl", "concept",
    "const", "consteval", "constexpr", "constinit", "const_cast", "continue", "co_await",
    "co_return", "co_yield", "decltype", "default", "delete", "do", "double", "dynamic_cast",
    "else", "enum", "explicit", "export", "extern", "false", "float", "for", "friend", "goto",
    "if", "inline", "int", "long", "mutable", "namespace", "new", "noexcept", "not", "not_eq",
    "nullptr", "operator", "or", "or_eq", "private", "protected", "public", "register",
    "reinterpret_cast", "requires", "return", "short", "signed", "sizeof", "static",
    "static_assert", "static_cast", "struct", "switch", "template", "this", "thread_local",
    "throw", "true", "try", "typedef", "typeid", "typename", "union", "unsigned", "using",
    "virtual", "void", "volatile", "wchar_t", "while", "xor", "xor_eq",
];

const CPP_DIRECTIVES: &[&str] = &[
    "define", "defined", "elif", "else", "endif", "error", "if", "ifdef", "ifndef", "import",
    "include", "line", "pragma", "undef", "warning",
];

const PYTHON_KEYWORDS: &[&str] = &[
    "False", "None", "True", "and", "as", "assert", "async", "await", "break", "class",
    "continue", "def", "del", "elif", "else", "except", "finally", "for", "from", "global",
    "if", "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield",
];

const JS_KEYWORDS: &[&str] = &[
    "abstract", "any", "as", "async", "await", "boolean", "break", "case", "catch", "class",
    "const", "continue", "debugger", "declare", "default", "delete", "do", "else", "enum",
    "export", "extends", "false", "finally", "for", "from", "function", "get", "if", "implements",
    "import", "in", "instanceof", "interface", "is", "let", "namespace", "new", "null", "number",
    "of", "package", "private", "protected", "public", "readonly", "return", "set", "static",
    "string", "super", "switch", "symbol", "this", "throw", "true", "try", "type", "typeof",
    "undefined", "unknown", "var", "void", "while", "with", "yield",
];

const JAVA_KEYWORDS: &[&str] = &[
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char", "class", "const",
    "continue", "default", "do", "double", "else", "enum", "extends", "final", "finally", "float",
    "for", "goto", "if", "implements", "import", "instanceof", "int", "interface", "long",
    "native", "new", "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws", "transient", "try",
    "void", "volatile", "while",
];

/// The standard HTML named character references (W3C HTML 4.01 entity set;
/// public data). BC's HTML grammar matches these case-SENSITIVELY: a listed
/// reference compares verbatim while an unlisted `&name;` falls to unclaimed
/// text and folds (m53d: `&COPY;` vs `&copy;` = different, `&bogus;` vs
/// `&BOGUS;` = similar).
const HTML_ENTITIES: &[&str] = &[
    "&Aacute;", "&aacute;", "&Acirc;", "&acirc;", "&acute;", "&AElig;",
    "&aelig;", "&Agrave;", "&agrave;", "&alefsym;", "&Alpha;", "&alpha;",
    "&amp;", "&and;", "&ang;", "&Aring;", "&aring;", "&asymp;",
    "&Atilde;", "&atilde;", "&auml;", "&Auml;", "&bdquo;", "&beta;",
    "&Beta;", "&brvbar;", "&bull;", "&cap;", "&Ccedil;", "&ccedil;",
    "&cedil;", "&cent;", "&Chi;", "&chi;", "&circ;", "&clubs;",
    "&cong;", "&copy;", "&crarr;", "&cup;", "&curren;", "&Dagger;",
    "&dagger;", "&darr;", "&dArr;", "&deg;", "&deg;", "&Delta;",
    "&delta;", "&diams;", "&divide;", "&divide;", "&eacute;", "&Eacute;",
    "&Ecirc;", "&ecirc;", "&Egrave;", "&egrave;", "&empty;", "&emsp;",
    "&ensp;", "&Epsilon;", "&epsilon;", "&equiv;", "&Eta;", "&eta;",
    "&eth;", "&ETH;", "&euml;", "&Euml;", "&euro;", "&exist;",
    "&fnof;", "&forall;", "&frac12;", "&frac12;", "&frac14;", "&frac14;",
    "&frac34;", "&frac34;", "&frasl;", "&Gamma;", "&gamma;", "&ge;",
    "&ge;", "&gt;", "&hArr;", "&harr;", "&hearts;", "&hellip;",
    "&Iacute;", "&iacute;", "&Icirc;", "&icirc;", "&iexcl;", "&igrave;",
    "&Igrave;", "&image;", "&infin;", "&int;", "&Iota;", "&iota;",
    "&iquest;", "&isin;", "&Iuml;", "&iuml;", "&kappa;", "&Kappa;",
    "&Lambda;", "&lambda;", "&lang;", "&laquo;", "&lArr;", "&larr;",
    "&lceil;", "&ldquo;", "&le;", "&le;", "&lfloor;", "&lowast;",
    "&loz;", "&lrm;", "&lsaquo;", "&lsquo;", "&lt;", "&macr;",
    "&mdash;", "&micro;", "&middot;", "&minus;", "&minus;", "&mu;",
    "&Mu;", "&nabla;", "&nbsp;", "&ndash;", "&ne;", "&ni;",
    "&not;", "&notin;", "&nsub;", "&ntilde;", "&Ntilde;", "&nu;",
    "&Nu;", "&Oacute;", "&oacute;", "&Ocirc;", "&ocirc;", "&oelig;",
    "&OElig;", "&Ograve;", "&ograve;", "&oline;", "&Omega;", "&omega;",
    "&omicron;", "&Omicron;", "&oplus;", "&or;", "&ordf;", "&ordm;",
    "&oslash;", "&Oslash;", "&Otilde;", "&otilde;", "&otimes;", "&ouml;",
    "&Ouml;", "&para;", "&part;", "&permil;", "&perp;", "&phi;",
    "&Phi;", "&pi;", "&Pi;", "&piv;", "&plusmn;", "&pound;",
    "&prime;", "&Prime;", "&prod;", "&prop;", "&Psi;", "&psi;",
    "&quot;", "&radic;", "&rang;", "&raquo;", "&rArr;", "&rarr;",
    "&rceil;", "&rdquo;", "&real;", "&reg;", "&rfloor;", "&rho;",
    "&Rho;", "&rlm;", "&rsaquo;", "&rsquo;", "&sbquo;", "&Scaron;",
    "&scaron;", "&sdot;", "&sect;", "&shy;", "&sigma;", "&Sigma;",
    "&sigmaf;", "&sim;", "&spades;", "&sub;", "&sube;", "&sum;",
    "&sup;", "&sup1;", "&sup2;", "&sup2;", "&sup3;", "&supe;",
    "&szlig;", "&tau;", "&Tau;", "&there4;", "&theta;", "&Theta;",
    "&thetasym;", "&thinsp;", "&thorn;", "&THORN;", "&tilde;", "&times;",
    "&trade;", "&uacute;", "&Uacute;", "&uArr;", "&uarr;", "&ucirc;",
    "&Ucirc;", "&Ugrave;", "&ugrave;", "&uml;", "&upsih;", "&Upsilon;",
    "&upsilon;", "&uuml;", "&Uuml;", "&weierp;", "&xi;", "&Xi;",
    "&Yacute;", "&yacute;", "&yen;", "&Yuml;", "&yuml;", "&zeta;",
    "&Zeta;", "&zwj;", "&zwnj;",
];

/// The alignment-time key for one line, kept for the tests that assert two
/// lines share an alignment class.
///
/// The aligner itself no longer compares these keys directly: `align` builds
/// its own [`crate::align::AnchorKey`]s, in which a line with important content
/// anchors on its important text while a line with none takes a key unique to
/// itself (BC places such lines by similarity rather than by identity — see
/// `align::pair_block`). This enum still names that class distinction, and
/// [`Plan::line_is_unimportant`] is the predicate the aligner actually uses.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum AlignKey {
    /// A line with no important content at all: comments, blanks, whitespace.
    /// All such lines align with each other (u2 `comment-vs-empty`,
    /// `blank-vs-ws`, `comment-syntax-swap`; U1 `comment`).
    Unimportant,
    /// The verbatim concatenation of the line's important element texts
    /// (plain text: whitespace-stripped lower-cased line).
    Seq(String),
}

/// What the engine needs to know about one line, precomputed per side.
#[derive(Debug, Clone)]
struct LineFacts {
    key: AlignKey,
    /// Concatenation of the important element texts. Two aligned lines are
    /// `similar` iff these are equal, `different` otherwise.
    important: String,
    /// Per-span element classes (`S`tring/`K`eyword/`O`ther) over the spans
    /// that built `important`, empty for every other grammar. XML/HTML/SQL
    /// pair element CLASSES (m53d: a listed `&copy;` keyword against
    /// unclaimed `&COPY;` text is an important difference even though the
    /// folded texts match), so the class sequence must agree before a pair
    /// can be `similar`.
    profile: String,
}

fn plain_facts(line: &str) -> LineFacts {
    let seq: String = line
        .chars()
        .filter(|c| !c.is_whitespace())
        .flat_map(|c| c.to_lowercase())
        .collect();
    let key = if seq.is_empty() {
        AlignKey::Unimportant
    } else {
        AlignKey::Seq(seq.clone())
    };
    LineFacts { key, important: seq, profile: String::new() }
}

/// Whether one span's text enters the comparison string case-folded. The
/// measured case policies (m53b/m53c/m53d/m53e probes): the C-like grammars
/// and REG compare everything verbatim (m53f `reg-keyword-case`); XML/HTML
/// fold every unclaimed span (tag and attribute names, text content —
/// `TXMLFormat` structural behaviour) while string contents and listed HTML
/// entities stay verbatim; SQL, Pascal, VB, DFM and COBOL fold keywords and
/// identifiers (CaseSensitive=False elements) while string tokens stay
/// verbatim (COBOL LineNum columns are unimportant and never reach here).
/// Unclaimed punctuation folds identically either way.
fn span_folds(format: Grammar, kind: Kind) -> bool {
    match format {
        Grammar::PlainText => true,
        Grammar::Cpp | Grammar::Python | Grammar::JavaScript | Grammar::Java
        | Grammar::Reg | Grammar::Perl => false,
        Grammar::Html => kind != Kind::Str && kind != Kind::Keyword,
        Grammar::Xml | Grammar::Sql | Grammar::Pas | Grammar::Vb | Grammar::Dfm
        | Grammar::Cobol => kind != Kind::Str,
    }
}

fn syntax_facts(line: &str, format: Grammar, cont: &mut Cont) -> LineFacts {
    let spans = scan_line(line, format, cont);
    let mut important = String::new();
    let mut profile = String::new();
    let chars: Vec<char> = line.chars().collect();
    for s in &spans {
        if matches!(s.kind, Kind::Comment | Kind::Whitespace | Kind::LineNum) {
            continue;
        }
        profile.push(profile_char(s.kind));
        if span_folds(format, s.kind) {
            let text: String = chars[s.start..s.end].iter().collect();
            important.extend(text.to_lowercase().chars());
        } else {
            important.extend(&chars[s.start..s.end]);
        }
    }
    let key = if important.is_empty() {
        AlignKey::Unimportant
    } else {
        AlignKey::Seq(important.clone())
    };
    LineFacts { key, important, profile }
}

/// One class character per important span, in order. Used only by the
/// XML/HTML/SQL class-pairing check in `Plan::verdict`.
fn profile_char(kind: Kind) -> char {
    match kind {
        Kind::Str => 'S',
        Kind::Keyword => 'K',
        _ => 'O',
    }
}

/// The character vector of a POD stop prefix.
fn pod_stop_chars(stop: &'static str) -> Vec<char> {
    stop.chars().collect()
}

/// A Perl POD opener at column 0: `=head1..4`/`=item`/`=pod` (stop `=cut`),
/// `=over` (stop `=back`), `=begin` (stop `=end`) — the grammar's three
/// line-anchored Comment elements. Returns the stop prefix or None when the
/// line does not open a block (`=cut`/`=back`/`=end` alone never open one).
fn pod_start(chars: &[char]) -> Option<&'static str> {
    if chars.first() != Some(&'=') {
        return None;
    }
    let word: String = chars[1..]
        .iter()
        .take_while(|c| c.is_ascii_alphanumeric())
        .collect();
    match word.as_str() {
        "head1" | "head2" | "head3" | "head4" | "item" | "pod" => Some("=cut"),
        "over" => Some("=back"),
        "begin" => Some("=end"),
        _ => None,
    }
}

/// A bracket-delimited quote-like form starting at `at`: the word (q/qq/qw/
/// s/tr) up to `opener`, content to the first `closer` (no nesting or
/// escapes — `[^)]+` in BC's element). Returns the index past the closer, or
/// None when the line does not complete the form (complete match only).
fn scan_bracketed(chars: &[char], at: usize, opener: char, closer: char) -> Option<usize> {
    let mut j = at;
    while j < chars.len() && chars[j] != opener {
        j += 1;
    }
    if j >= chars.len() {
        return None;
    }
    let content = j + 1;
    j += 1;
    while j < chars.len() && chars[j] != closer {
        j += 1;
    }
    if j >= chars.len() || j == content {
        return None;
    }
    Some(j + 1)
}

/// A Perl `s/.../.../` or `tr/.../.../` form: `(s|tr)/([^/]*/){2}` — the
/// first `/` (empty segments allowed). `slash` indexes that first `/`.
/// COMPLETE match only.
fn scan_slash_form(chars: &[char], slash: usize) -> Option<usize> {
    let mut j = slash + 1;
    for _ in 0..2 {
        while j < chars.len() && chars[j] != '/' {
            j += 1;
        }
        if j >= chars.len() {
            return None;
        }
        j += 1;
    }
    Some(j)
}

/// The division-shaped Perl regex element `/[^/]*/` (content between two
/// slashes, no empty content). COMPLETE match only.
fn scan_slash_regex(chars: &[char], at: usize) -> Option<usize> {
    let mut j = at + 1;
    while j < chars.len() && chars[j] != '/' {
        j += 1;
    }
    if j >= chars.len() || j == at + 1 {
        return None;
    }
    Some(j + 1)
}

/// Everything the alignment and classification need, computed once per side so
/// the cross-line tokenizer state is threaded in document order.
///
/// Building the plan is the ONLY place tokenization happens; `align` pairs by
/// [`AlignKey`] and [`Plan::verdict`] classifies each matched pair.
#[derive(Debug, Clone)]
pub struct Plan {
    pub format: Grammar,
    left_lines: Vec<String>,
    right_lines: Vec<String>,
    left: Vec<LineFacts>,
    right: Vec<LineFacts>,
}

impl Plan {
    pub fn build(left: &[String], right: &[String], format: Grammar) -> Plan {
        let mut cont_l = Cont::None;
        let mut cont_r = Cont::None;
        let facts = |lines: &[String], cont: &mut Cont| -> Vec<LineFacts> {
            lines
                .iter()
                .map(|l| match format {
                    Grammar::PlainText => plain_facts(l),
                    _ => syntax_facts(l, format, cont),
                })
                .collect()
        };
        Plan {
            format,
            left_lines: left.to_vec(),
            right_lines: right.to_vec(),
            left: facts(left, &mut cont_l),
            right: facts(right, &mut cont_r),
        }
    }

    pub fn left_key(&self, i: usize) -> &AlignKey {
        &self.left[i].key
    }

    pub fn right_key(&self, j: usize) -> &AlignKey {
        &self.right[j].key
    }

    pub fn left_len(&self) -> usize {
        self.left.len()
    }

    pub fn right_len(&self) -> usize {
        self.right.len()
    }

    /// The verbatim source line, for the mode3 window engine's line weights
    /// (`FUN_140e75c50`: blank runs use the raw length in `2*len+50`).
    pub fn left_line(&self, i: usize) -> &str {
        &self.left_lines[i]
    }

    pub fn right_line(&self, j: usize) -> &str {
        &self.right_lines[j]
    }

    /// True when the line carries no important content (comment, blank or
    /// whitespace-only). One-sided such lines are reported
    /// `leftsimilar`/`rightsimilar` instead of orphans (u2b).
    pub fn line_is_unimportant(&self, left_side: bool, i: usize) -> bool {
        let f = if left_side { &self.left[i] } else { &self.right[i] };
        matches!(f.key, AlignKey::Unimportant)
    }

    /// Per-line unimportance mask for one side, in one pass.
    ///
    /// The `statistics` layout splits the original-line counters by importance
    /// (`IOriginal`/`UOriginal`, m52 probe), which the group list alone cannot
    /// answer — a `same` row says nothing about whether its left line is a
    /// comment.
    pub fn unimportant_mask(lines: &[String], grammar: Grammar) -> Vec<bool> {
        let mut cont = Cont::None;
        lines
            .iter()
            .map(|l| match grammar {
                Grammar::PlainText => plain_facts(l).key == AlignKey::Unimportant,
                _ => {
                    let f = syntax_facts(l, grammar, &mut cont);
                    f.key == AlignKey::Unimportant
                }
            })
            .collect()
    }

    /// The normalized important text of one line: every whitespace and comment
    /// element removed, everything else verbatim (plain text is
    /// whitespace-stripped and lower-cased). Two lines are `similar` exactly
    /// when these are equal while the raw lines differ, and the closeness
    /// pairing in `align` ranks candidates by their longest common
    /// subsequence over this text.
    pub fn important_text(&self, left_side: bool, i: usize) -> &str {
        let f = if left_side { &self.left[i] } else { &self.right[i] };
        &f.important
    }

    /// The text the closeness pass measures similarity on.
    ///
    /// Plain text uses the **verbatim line**: the m51b probe
    /// (`runs/m51b-probe-20261014T163003Z`, `cs-check`) shows BC zipping
    /// `[bbbb, xx] vs [X, Y]` into two zero-score pairs, which lower-cased
    /// text (`xx` scoring 1 against `X`) would never produce — while the
    /// anchor layer above stays case-insensitive so case-swapped twins can
    /// still align as `similar` (disambig/case-swap-align). Syntax formats
    /// keep the verbatim important text: comments and whitespace carry no
    /// weight there, which is what the recorded m26 comment pairings show.
    pub fn closeness_text(&self, left_side: bool, i: usize) -> &str {
        match self.format {
            Grammar::PlainText => {
                if left_side {
                    &self.left_lines[i]
                } else {
                    &self.right_lines[i]
                }
            }
            _ => {
                let f = if left_side { &self.left[i] } else { &self.right[i] };
                &f.important
            }
        }
    }

    /// The text BC's pair scorer fetches (`FUN_140e723a0` → the line-text
    /// accessor): the verbatim line with only leading/trailing whitespace
    /// trimmed — comments and case are kept.
    ///
    /// This is deliberately NOT [`Self::closeness_text`]: scoring syntax lines
    /// on comment-stripped text is measurably worse than on the verbatim line
    /// (docs/11 §15, configs C/E vs D — 105 vs 95 of 120 fuzz cases).
    pub fn score_text(&self, left_side: bool, i: usize) -> &str {
        let line = if left_side {
            &self.left_lines[i]
        } else {
            &self.right_lines[i]
        };
        line.trim()
    }

    /// The text `interval_nw` scores on. For plain text the scorer sees the
    /// line with **all whitespace removed** — measured 2026-10-16 by the
    /// six-case discriminant probe (docs/11 §22): `"x node beta"` vs `"Node"`
    /// pairs at -17 and beats skipping to `"beta"` (-21) only when the 11
    /// verbatim characters shrink to 9, while `"beta"` vs `"NODE X BETA"`
    /// keeps its baseline -21/-40 pairings. Case is never folded here:
    /// `NODEx`/`NODE X BETA`/`alpha node item value` all pin case-sensitive
    /// bytes. Syntax formats keep the verbatim trimmed line — whitespace
    /// carries meaning there (folding it regressed f0059/f0062).
    pub fn nw_score_text(&self, left_side: bool, i: usize) -> String {
        let t = self.score_text(left_side, i);
        if matches!(self.format, Grammar::PlainText) {
            t.chars().filter(|c| !c.is_whitespace()).collect()
        } else {
            t.to_string()
        }
    }

    /// Classify a matched pair.
    pub fn verdict(&self, li: usize, ri: usize) -> Verdict {
        if self.left_lines[li] == self.right_lines[ri] {
            return Verdict::Same;
        }
        if self.left[li].important == self.right[ri].important {
            // XML/HTML/SQL and the m53e batch pair element classes as well
            // as text: a listed HTML entity never pairs with unclaimed text
            // even when the folded bytes match (m53d), and a keyword never
            // pairs with a string. REG compares everything verbatim, so its
            // concat check already implies the class sequence.
            let fold_classes = matches!(
                self.format,
                Grammar::Xml | Grammar::Html | Grammar::Sql | Grammar::Pas
                    | Grammar::Vb | Grammar::Dfm | Grammar::Cobol
            );
            if !fold_classes || self.left[li].profile == self.right[ri].profile {
                return Verdict::Similar;
            }
        }
        Verdict::Different
    }
}

/// `rules-based ignore-unimportant` for two in-memory files: true when every
/// difference between them is unimportant under the M2 importance rules.
///
/// Used by the folder comparison (`dir` crate) so both paths share one
/// definition of "unimportant". The grammar is chosen from `name`'s extension
/// exactly as the text comparison does, so `a.c` gets the C/C++ rules and an
/// unknown extension compares as plain text (u2 `foo-*`).
///
/// Decoding mirrors the text pipeline: UTF-8 with replacement, line-split on
/// LF/CRLF/CR. A file that does not decode cleanly is not "all unimportant":
/// replacement characters make the important text differ, which is the honest
/// conservative answer, and no error is invented for bytes the Oracle reads.
pub fn folder_rules_based_ignoring_unimportant(left: &[u8], right: &[u8], name: &str) -> bool {
    let grammar = Grammar::for_path(name);
    let dl = crate::lines::decode(left);
    let dr = crate::lines::decode(right);
    let ll = crate::lines::split_text(&dl.text);
    let rl = crate::lines::split_text(&dr.text);
    if ll.len() != rl.len() {
        // A line-count change is always an important structural difference.
        return false;
    }
    let plan = Plan::build(&ll, &rl, grammar);
    (0..ll.len()).all(|i| !matches!(plan.verdict(i, i), Verdict::Different))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn v(l: &str, r: &str, format: Grammar) -> Verdict {
        let ls = vec![l.to_string()];
        let rs = vec![r.to_string()];
        Plan::build(&ls, &rs, format).verdict(0, 0)
    }

    fn same_key(l: &str, r: &str, format: Grammar) -> bool {
        let ls = vec![l.to_string()];
        let rs = vec![r.to_string()];
        let p = Plan::build(&ls, &rs, format);
        p.left_key(0) == p.right_key(0)
    }

    // ---------------------------------------------------------------
    // Grammar selection
    // ---------------------------------------------------------------

    #[test]
    fn masks_select_the_implemented_grammars() {
        for ext in ["c", "cc", "cpp", "cs", "h", "hpp", "m", "C", "H"] {
            assert_eq!(Grammar::for_path(&format!("a.{ext}")), Grammar::Cpp, "{ext}");
        }
        assert_eq!(Grammar::for_path("a.py"), Grammar::Python);
        assert_eq!(Grammar::for_path("a.js"), Grammar::JavaScript);
        assert_eq!(Grammar::for_path("a.java"), Grammar::Java);
        assert_eq!(Grammar::for_path("a.jav"), Grammar::Java);
        assert_eq!(Grammar::for_path("a.xml"), Grammar::Xml);
        assert_eq!(Grammar::for_path("a.xsd"), Grammar::Xml);
        assert_eq!(Grammar::for_path("a.htm"), Grammar::Html);
        assert_eq!(Grammar::for_path("a.aspx"), Grammar::Html);
        assert_eq!(Grammar::for_path("a.sql"), Grammar::Sql);
        assert_eq!(Grammar::for_path("a.dsql"), Grammar::Sql);
        assert_eq!(Grammar::for_path("a.pas"), Grammar::Pas);
        assert_eq!(Grammar::for_path("a.dpr"), Grammar::Pas);
        assert_eq!(Grammar::for_path("a.bas"), Grammar::Vb);
        assert_eq!(Grammar::for_path("a.vbs"), Grammar::Vb);
        assert_eq!(Grammar::for_path("a.ini"), Grammar::Reg);
        assert_eq!(Grammar::for_path("a.reg"), Grammar::Reg);
        assert_eq!(Grammar::for_path("a.cbl"), Grammar::Cobol);
        assert_eq!(Grammar::for_path("a.dfm"), Grammar::Dfm);
        assert_eq!(Grammar::for_path("a.pl"), Grammar::Perl);
        assert_eq!(Grammar::for_path("a.pm"), Grammar::Perl);
        // BASH is measured plain-text behaviour (m53g-m53j): .sh selects the
        // PlainText comparison exactly as BC does.
        assert_eq!(Grammar::for_path("a.sh"), Grammar::PlainText);
        assert_eq!(Grammar::for_path(r"D:\x\y.PY"), Grammar::Python);
    }

    #[test]
    fn unknown_and_unimplemented_extensions_are_plain_text() {
        // u2 foo-*: BC treats an unknown extension as plain text.
        for ext in ["txt", "text", "foo", "md", ""] {
            assert_eq!(Grammar::for_path(&format!("a.{ext}")), Grammar::PlainText, "{ext}");
        }
        assert_eq!(Grammar::for_path("no_extension"), Grammar::PlainText);
    }

    // ---------------------------------------------------------------
    // U1 table: single-class .c pairs
    // ---------------------------------------------------------------

    #[test]
    fn u1_important_classes_stay_important() {
        let g = Grammar::Cpp;
        assert_eq!(v("#include <stdio.h>", "#include <stdlib.h>", g), Verdict::Different);
        assert_eq!(v("int s = a + b;", "int s = a - b;", g), Verdict::Different);
        assert_eq!(v("int alpha1;", "int alpha2;", g), Verdict::Different);
        assert_eq!(v("int x = 10;", "int x = 20;", g), Verdict::Different);
        assert_eq!(v("char *m = \"abc\";", "char *m = \"abd\";", g), Verdict::Different);
        assert_eq!(v("unsigned int x;", "signed int x;", g), Verdict::Different);
        assert_eq!(v("int Alpha;", "int alpha;", g), Verdict::Different);
        assert_eq!(v("int same;", "int same;", g), Verdict::Same);
    }

    #[test]
    fn u1_comment_and_whitespace_stay_unimportant() {
        let g = Grammar::Cpp;
        assert_eq!(v("// alpha", "// beta", g), Verdict::Similar);
        assert_eq!(v("int  x;", "int x;", g), Verdict::Similar);
        assert_eq!(v("int x;   ", "int x;", g), Verdict::Similar);
    }

    // ---------------------------------------------------------------
    // U2 table
    // ---------------------------------------------------------------

    #[test]
    fn u2_mixed_lines_fold_on_the_comment_part() {
        let g = Grammar::Cpp;
        assert_eq!(v("int x = 1; // note", "int x = 1; // other", g), Verdict::Similar);
        assert_eq!(v("/* head */ int x;", "/* tail */ int x;", g), Verdict::Similar);
        assert!(same_key("int x = 1; // note", "int x = 1; // other", g));
    }

    #[test]
    fn u2_block_comments_span_lines() {
        let ls: Vec<String> = ["/*", "alpha body", "*/", "int x;"]
            .iter().map(|s| s.to_string()).collect();
        let rs: Vec<String> = ["/*", "beta body", "*/", "int x;"]
            .iter().map(|s| s.to_string()).collect();
        let p = Plan::build(&ls, &rs, Grammar::Cpp);
        assert_eq!(p.verdict(0, 0), Verdict::Same);
        assert_eq!(p.verdict(1, 1), Verdict::Similar, "block body is unimportant");
        assert!(p.line_is_unimportant(true, 1));
        assert_eq!(p.verdict(2, 2), Verdict::Same);
        assert_eq!(p.verdict(3, 3), Verdict::Same);
    }

    #[test]
    fn u2_string_interiors_are_important() {
        let g = Grammar::Cpp;
        assert_eq!(v("char *a = \"a b\";", "char *a = \"a  b\";", g), Verdict::Different);
        assert_eq!(v("char *a = \"ABC\";", "char *a = \"abc\";", g), Verdict::Different);
        assert_eq!(v("char *a = \"abc", "char *a = \"abd", g), Verdict::Different);
        assert_eq!(v("char *a = \"a\\\"b\";", "char *a = \"a\\\"c\";", g), Verdict::Different);
    }

    #[test]
    fn u2_numbers_keep_their_shapes() {
        let g = Grammar::Cpp;
        assert_eq!(v("int a = 0x10;", "int a = 0x20;", g), Verdict::Different);
        assert_eq!(v("double a = 1.5e3;", "double a = 1.5e4;", g), Verdict::Different);
        // Identical numbers with different spelling still differ by text.
        assert_eq!(v("int a = 0x10;", "int a = 16;", g), Verdict::Different);
    }

    #[test]
    fn u2_python_indent_is_important_but_trailing_ws_is_not() {
        let g = Grammar::Python;
        assert_eq!(v("x = 1", "    x = 1", g), Verdict::Different);
        assert_eq!(v("x = 1   ", "x = 1", g), Verdict::Similar);
        assert_eq!(v("x = 1  # alpha", "x = 1  # beta", g), Verdict::Similar);
        assert_eq!(v("# alpha", "# beta", g), Verdict::Similar);
        // A comment after leading whitespace is one comment element.
        assert!(same_key("  # a", "  # b", g));
    }

    #[test]
    fn u2_python_triple_quotes_span_lines() {
        let ls: Vec<String> = ["'''", "a b", "'''"].iter().map(|s| s.to_string()).collect();
        let rs: Vec<String> = ["'''", "a  b", "'''"].iter().map(|s| s.to_string()).collect();
        let p = Plan::build(&ls, &rs, Grammar::Python);
        assert_eq!(p.verdict(0, 0), Verdict::Same);
        assert_eq!(p.verdict(1, 1), Verdict::Different, "string body is important");
        assert_eq!(p.verdict(2, 2), Verdict::Same);
    }

    // ---------------------------------------------------------------
    // StopEOL strings: an unterminated quote is one string element to the
    // line end (bcfileformats-spec.json PYTHON/CPP/JS `'`/`"` String
    // elements all carry StopEOL="True"). Whitespace and `#` inside that
    // span stay *string content* (important), and the line never opens a
    // block comment after the quote (u2 `string-unterminated`,
    // `string-internal-ws`).
    // ---------------------------------------------------------------

    #[test]
    fn py_unterminated_string_runs_to_eol() {
        let g = Grammar::Python;
        // Whitespace inside the StopEOL span is string content, important.
        assert_eq!(v("x = 'a b", "x = 'a  b", g), Verdict::Different);
        // A `#` inside the span is not a comment.
        assert_eq!(v("x = 'a # b", "x = 'a # c", g), Verdict::Different);
        assert_eq!(v("x = 'a # b", "x = 'a # b", g), Verdict::Same);
        // The element does not span lines: the next line tokenizes fresh.
        let ls: Vec<String> = ["x = 'a b", "y = 1"].iter().map(|s| s.to_string()).collect();
        let rs: Vec<String> = ["x = 'a b", "y = 2"].iter().map(|s| s.to_string()).collect();
        let p = Plan::build(&ls, &rs, g);
        assert_eq!(p.verdict(1, 1), Verdict::Different);
        assert!(!p.line_is_unimportant(true, 0));
    }

    #[test]
    fn cpp_unterminated_string_does_not_open_block_comment() {
        let g = Grammar::Cpp;
        // `a = "x /*` is one string to EOL; the `/*` inside it is string
        // content and must NOT push the rest of the file into block-comment
        // state. `int y;` vs `int Y;` on the next line stays important.
        let ls: Vec<String> =
            ["a = \"x /*", "int y;", "int z;"].iter().map(|s| s.to_string()).collect();
        let rs: Vec<String> =
            ["a = \"x /*", "int Y;", "int z;"].iter().map(|s| s.to_string()).collect();
        let p = Plan::build(&ls, &rs, g);
        assert_eq!(p.verdict(0, 0), Verdict::Same);
        assert_eq!(p.verdict(1, 1), Verdict::Different, "no block-comment leak");
        assert_eq!(p.verdict(2, 2), Verdict::Same);
        assert!(!p.line_is_unimportant(true, 1));
    }

    #[test]
    fn js_unterminated_string_runs_to_eol() {
        let g = Grammar::JavaScript;
        assert_eq!(v("var s = 'a b", "var s = 'a  b", g), Verdict::Different);
        assert_eq!(v("var s = 'a // b", "var s = 'a // c", g), Verdict::Different);
    }

    #[test]
    fn u2_js_regex_literals_are_strings() {
        let g = Grammar::JavaScript;
        assert_eq!(v("var r = /ab/g;", "var r = /ac/g;", g), Verdict::Different);
        assert_eq!(v("var r = /a b/g;", "var r = /ab/g;", g), Verdict::Different);
        // Division is not a regex: both sides tokenize as operators and the
        // difference is still important.
        assert_eq!(v("var q = a / b;", "var q = a / c;", g), Verdict::Different);
        assert_eq!(v("// alpha", "// beta", g), Verdict::Similar);
        assert_eq!(v("var t = `a b`;", "var t = `a c`;", g), Verdict::Different);
    }

    #[test]
    fn u2_unknown_extensions_behave_like_plain_text() {
        let g = Grammar::PlainText;
        assert_eq!(v("Alpha", "alpha", g), Verdict::Similar);
        // No comment rules in plain text.
        assert_eq!(v("// alpha", "// beta", g), Verdict::Different);
        assert_eq!(v("int x = 10;", "long x = 20;", g), Verdict::Different);
    }

    // ---------------------------------------------------------------
    // Alignment classes
    // ---------------------------------------------------------------

    #[test]
    fn all_unimportant_lines_share_one_class() {
        let g = Grammar::Cpp;
        assert!(same_key("// a", "// b", g));
        assert!(same_key("// a", "", g));
        assert!(same_key("", "   ", g));
        assert!(same_key("// a", "/* a */", g));
        assert!(!same_key("// a", "x;", g));
        assert!(!same_key("", "x;", g));
    }

    #[test]
    fn plain_text_class_is_case_and_whitespace_insensitive() {
        let g = Grammar::PlainText;
        assert!(same_key("a ", "a", g));
        assert!(same_key("Alpha", "aLPHA", g));
        assert!(same_key("a\tb", "a b", g));
        assert!(!same_key("a", "b", g));
    }

    #[test]
    fn cpp_class_is_verbatim_on_important_parts() {
        let g = Grammar::Cpp;
        assert!(same_key("int  x;", "int x;", g));
        assert!(same_key("x = 1; // one", "x = 1; // two", g));
        // Leading whitespace is unimportant under every grammar (the Python
        // Indent element is the only important whitespace, tested above).
        assert!(same_key("    x = 1;", "x = 1;", g));
        assert!(!same_key("int Alpha;", "int alpha;", g));
    }

    #[test]
    fn cpp_verbatim_string_uses_doubled_quote_escape() {
        let g = Grammar::Cpp;
        // @"a""b" is one string whose content includes a quote.
        assert_eq!(v("string s = @\"a\"\"b\";", "string s = @\"a\"\"c\";", g), Verdict::Different);
        assert_eq!(v("string s = @\"a\"\"b\";", "string s = @\"a\"\"b\";", g), Verdict::Same);
    }

    #[test]
    fn scan_line_kinds_smoke() {
        let mut cont = Cont::None;
        let spans = scan_line("int x = 0x1f; // note", Grammar::Cpp, &mut cont);
        let kinds: Vec<Kind> = spans.iter().map(|s| s.kind).collect();
        assert_eq!(kinds, vec![Kind::Keyword, Kind::Whitespace, Kind::Identifier, Kind::Whitespace, Kind::Operator, Kind::Whitespace, Kind::Number, Kind::Operator, Kind::Whitespace, Kind::Comment]);
        assert_eq!(cont, Cont::None);
    }

    #[test]
    fn directive_and_operator_multi_char_first() {
        let mut cont = Cont::None;
        let spans = scan_line("#include <a.h>", Grammar::Cpp, &mut cont);
        assert_eq!(spans[0].kind, Kind::Directive);
        assert_eq!(spans[0].end, "#include".len());
        let spans = scan_line("x = a ** b", Grammar::Python, &mut cont);
        let op = spans
            .iter()
            .find(|s| s.kind == Kind::Operator && s.end - s.start == 2)
            .expect("** must tokenize as one operator");
        assert_eq!(op.end - op.start, 2, "longest operator wins");
    }

    #[test]
    fn unterminated_block_comment_closes_on_a_later_line() {
        let lines: Vec<String> = ["/*", "still", "*/ x;"].iter().map(|s| s.to_string()).collect();
        let p = Plan::build(&lines, &lines, Grammar::Cpp);
        assert!(p.line_is_unimportant(true, 0));
        assert!(p.line_is_unimportant(true, 1));
        assert!(!p.line_is_unimportant(true, 2));
    }

    // ---------------------------------------------------------------
    // JAVA grammar (m53 probe, runs m53-java-*)
    // ---------------------------------------------------------------

    #[test]
    fn java_case_only_changes_are_different() {
        let g = Grammar::Java;
        assert_eq!(v("int value = 1;", "int Value = 1;", g), Verdict::Different);
        assert_eq!(v("if (x) { return; }", "IF (x) { RETURN; }", g), Verdict::Different);
        assert_eq!(v("int X = 1; // c", "int x = 1; // c", g), Verdict::Different);
        assert_eq!(v("char c = 'a';", "char c = 'A';", g), Verdict::Different);
    }

    #[test]
    fn java_comments_and_whitespace_stay_unimportant() {
        let g = Grammar::Java;
        assert_eq!(v("int x = 1; // alpha", "int x = 1; // beta", g), Verdict::Similar);
        assert_eq!(v("    int x = 1;", "int x = 1;", g), Verdict::Similar);
        assert_eq!(v("int x = 1;", "int  x = 1;", g), Verdict::Similar);
        // Comment and blank lines share the alignment class.
        assert!(same_key("// note", "", g));
        assert_eq!(v("// note", "", g), Verdict::Similar);
    }

    #[test]
    fn java_block_comments_span_lines() {
        let ls: Vec<String> = ["/* head", "body one", "*/ int y = 1;"]
            .iter().map(|s| s.to_string()).collect();
        let rs: Vec<String> = ["/* head", "body two", "*/ int y = 1;"]
            .iter().map(|s| s.to_string()).collect();
        let p = Plan::build(&ls, &rs, Grammar::Java);
        assert_eq!(p.verdict(0, 0), Verdict::Same);
        assert_eq!(p.verdict(1, 1), Verdict::Similar);
        assert_eq!(p.verdict(2, 2), Verdict::Same);
    }

    #[test]
    fn java_string_content_is_important() {
        let g = Grammar::Java;
        assert_eq!(v("String s = \"a b\";", "String s = \"ab\";", g), Verdict::Different);
        // Escape=92: `\"` does not close, so the `//` stays string content.
        assert_eq!(v("s = \"a\\\" // x\";", "s = \"a\\\" // y\";", g), Verdict::Different);
    }

    #[test]
    fn java_unterminated_string_absorbs_to_eol_without_leaking() {
        let g = Grammar::Java;
        // StopEOL: `//` and `/*` inside an unterminated string are content.
        assert_eq!(v("String s = \"abc // x", "String s = \"abc // y", g), Verdict::Different);
        assert_eq!(v("char c = 'x // y", "char c = 'x // z", g), Verdict::Different);
        // No cross-line state: the next line tokenizes fresh (m53 str-vs-block).
        let ls: Vec<String> = ["String s = \"x /* y", "int z = 1;"]
            .iter().map(|s| s.to_string()).collect();
        let rs: Vec<String> = ["String s = \"x /* y", "int z = 2;"]
            .iter().map(|s| s.to_string()).collect();
        let p = Plan::build(&ls, &rs, Grammar::Java);
        assert_eq!(p.verdict(0, 0), Verdict::Same);
        assert_eq!(p.verdict(1, 1), Verdict::Different);
    }

    // ---------------------------------------------------------------
    // XML / HTML / SQL grammars (m53b/m53c/m53d probes)
    // ---------------------------------------------------------------

    #[test]
    fn xml_markup_folds_but_string_content_is_exact() {
        let g = Grammar::Xml;
        assert_eq!(v("<Tag v=\"1\">x</Tag>", "<tag v=\"1\">x</tag>", g), Verdict::Similar);
        assert_eq!(v("<a B=\"1\"/>", "<a b=\"1\"/>", g), Verdict::Similar);
        assert_eq!(v("<p>Hello</p>", "<p>HELLO</p>", g), Verdict::Similar);
        assert_eq!(v("hello", "HELLO", g), Verdict::Similar);
        assert_eq!(v("<?xml version=\"1.0\"?>", "<?XML version=\"1.0\"?>", g), Verdict::Similar);
        // String contents compare verbatim.
        assert_eq!(v("<a b=\"x\"/>", "<a b=\"X\"/>", g), Verdict::Different);
        assert_eq!(v("<a t='x\"y'/>", "<a t='x\"z'/>", g), Verdict::Different);
        // No entity element in the XML grammar: `&amp;` is unclaimed text.
        assert_eq!(v("<p>&amp;</p>", "<p>&AMP;</p>", g), Verdict::Similar);
    }

    #[test]
    fn xml_comments_span_lines_and_persist_when_unterminated() {
        let g = Grammar::Xml;
        assert_eq!(v("<!-- a --> <x/>", "<!-- b --> <x/>", g), Verdict::Similar);
        let ls: Vec<String> = ["<!--", "body one", "--> <x/>"]
            .iter().map(|s| s.to_string()).collect();
        let rs: Vec<String> = ["<!--", "body two", "--> <x/>"]
            .iter().map(|s| s.to_string()).collect();
        let p = Plan::build(&ls, &rs, g);
        assert_eq!(p.verdict(1, 1), Verdict::Similar);
        // Unterminated `<!--` carries the comment to the next line (m53b).
        let ls: Vec<String> = ["<!-- open", "int a = 1;"]
            .iter().map(|s| s.to_string()).collect();
        let rs: Vec<String> = ["<!-- open", "int a = 2;"]
            .iter().map(|s| s.to_string()).collect();
        let p = Plan::build(&ls, &rs, g);
        assert_eq!(p.verdict(1, 1), Verdict::Similar);
    }

    #[test]
    fn xml_strings_are_stopeol_without_escapes() {
        let g = Grammar::Xml;
        assert_eq!(v("<a href=\"x", "<a href=\"y", g), Verdict::Different);
        // `\` is inert: the string closes at the second quote, so the
        // `<!--` tail is a real comment (m53c xml-no-escape = similar).
        assert_eq!(v("<a b=\"x\\\" <!-- one", "<a b=\"x\\\" <!-- two", g),
                   Verdict::Similar);
    }

    #[test]
    fn html_entities_are_list_matched_case_sensitively() {
        let g = Grammar::Html;
        assert_eq!(v("<p>&COPY;</p>", "<p>&copy;</p>", g), Verdict::Different);
        assert_eq!(v("<p>&AMP;</p>", "<p>&amp;</p>", g), Verdict::Different);
        assert_eq!(v("<p>&bogus;</p>", "<p>&BOGUS;</p>", g), Verdict::Similar);
        assert_eq!(v("<p>&#38;</p>", "<p>&#39;</p>", g), Verdict::Different);
    }

    #[test]
    fn html_markup_folds_like_xml() {
        let g = Grammar::Html;
        assert_eq!(v("<DIV>x</DIV>", "<div>x</div>", g), Verdict::Similar);
        assert_eq!(v("<a HREF=\"x\">y</a>", "<a href=\"x\">y</a>", g), Verdict::Similar);
        assert_eq!(v("<p>Hello</p>", "<p>HELLO</p>", g), Verdict::Similar);
        assert_eq!(v("<a t='X'>y</a>", "<a t='x'>y</a>", g), Verdict::Different);
    }

    #[test]
    fn sql_case_folds_outside_strings() {
        let g = Grammar::Sql;
        assert_eq!(v("SELECT * FROM t1;", "select * from t1;", g), Verdict::Similar);
        assert_eq!(v("SELECT * FROM t1;", "SELECT * FROM T1;", g), Verdict::Similar);
        assert_eq!(v("x = nabccomment", "x = NABCCOMMENT", g), Verdict::Similar);
        // String tokens (content AND the n/N prefix) compare verbatim.
        assert_eq!(v("x = n'abc';", "x = N'abc';", g), Verdict::Different);
        assert_eq!(v("INSERT INTO users VALUES (1, 'alice');",
                     "INSERT INTO users VALUES (1, 'Alice');", g), Verdict::Different);
    }

    #[test]
    fn sql_comments_and_strings() {
        let g = Grammar::Sql;
        assert_eq!(v("SELECT 1; -- alpha", "SELECT 1; -- beta", g), Verdict::Similar);
        // An unterminated quote matches nothing, so `--` stays a comment.
        assert_eq!(v("SELECT 'abc -- x", "SELECT 'abc -- y", g), Verdict::Similar);
        // A matched string absorbs `--` as content.
        assert_eq!(v("SELECT 'a -- b';", "SELECT 'a -- c';", g), Verdict::Different);
        assert_eq!(v("x = 'It''s fine';", "x = 'It''s fine!';", g), Verdict::Different);
        assert_eq!(v("x = 'a\'b';", "x = 'a\'c';", g), Verdict::Different);
        let ls: Vec<String> = ["/*", "body", "*/ SELECT 1;"]
            .iter().map(|s| s.to_string()).collect();
        let rs: Vec<String> = ["/*", "body two", "*/ SELECT 1;"]
            .iter().map(|s| s.to_string()).collect();
        let p = Plan::build(&ls, &rs, g);
        assert_eq!(p.verdict(1, 1), Verdict::Similar);
    }

    // ---------------------------------------------------------------
    // PAS / VB / REG / COBOL / DFM grammars (m53e/m53f probes)
    // ---------------------------------------------------------------

    #[test]
    fn pas_case_folds_directives_are_important() {
        let g = Grammar::Pas;
        assert_eq!(v("Value := 1;", "value := 1;", g), Verdict::Similar);
        assert_eq!(v("BEGIN X := 1; END.", "begin x := 1; end.", g), Verdict::Similar);
        assert_eq!(v("{$X+}", "{$Y+}", g), Verdict::Different);
        assert_eq!(v("{ alpha } x := 1;", "{ beta } x := 1;", g), Verdict::Similar);
        assert_eq!(v("(* alpha *) x := 1;", "(* beta *) x := 1;", g), Verdict::Similar);
    }

    #[test]
    fn pas_comments_span_lines_and_strings_are_complete_matches() {
        let g = Grammar::Pas;
        let ls: Vec<String> = ["{", "body one", "} x := 1;"]
            .iter().map(|s| s.to_string()).collect();
        let rs: Vec<String> = ["{", "body two", "} x := 1;"]
            .iter().map(|s| s.to_string()).collect();
        let p = Plan::build(&ls, &rs, g);
        assert_eq!(p.verdict(1, 1), Verdict::Similar);
        let ls: Vec<String> = ["(*", "body", "*) x := 1;"]
            .iter().map(|s| s.to_string()).collect();
        let rs: Vec<String> = ["(*", "body two", "*) x := 1;"]
            .iter().map(|s| s.to_string()).collect();
        let p = Plan::build(&ls, &rs, g);
        assert_eq!(p.verdict(1, 1), Verdict::Similar);
        // Complete-match strings: `''` doubling inside, no backslash escape.
        assert_eq!(v("x := 'It''s';", "x := 'It''s!';", g), Verdict::Different);
        assert_eq!(v("c := #65;", "c := #66;", g), Verdict::Different);
        // Unterminated `'` falls through; `//` stays a real comment.
        assert_eq!(v("x := 'abc // y", "x := 'abc // z", g), Verdict::Similar);
    }

    #[test]
    fn vb_comments_and_strings() {
        let g = Grammar::Vb;
        assert_eq!(v("Dim X As Integer", "dim x as integer", g), Verdict::Similar);
        assert_eq!(v("x = 1 ' alpha", "x = 1 ' beta", g), Verdict::Similar);
        assert_eq!(v("Rem alpha", "rem beta", g), Verdict::Similar);
        // `rem` matches unanchored: mid-line `rem ` starts a comment.
        assert_eq!(v("x = 1 rem alpha", "x = 1 rem beta", g), Verdict::Similar);
        assert_eq!(v("s = \"a\"\"b\"", "s = \"a\"\"c\"", g), Verdict::Different);
        // EOL-anchored fallback: unterminated `"` absorbs to end of line.
        assert_eq!(v("s = \"abc", "s = \"abd", g), Verdict::Different);
        assert_eq!(v("s = \"x ' a", "s = \"x ' b", g), Verdict::Different);
    }

    #[test]
    fn reg_comments_are_line_anchored() {
        let g = Grammar::Reg;
        assert_eq!(v("; alpha", "; beta", g), Verdict::Similar);
        assert_eq!(v("   ; alpha", "; beta", g), Verdict::Similar);
        // A `;` after content stays unclaimed text.
        assert_eq!(v("x = 1 ; note", "x = 1 ; other", g), Verdict::Different);
        assert_eq!(v("a=\"x\"", "a=\"y\"", g), Verdict::Different);
        // StopEOL strings absorb a later `;`.
        assert_eq!(v("a=\"x ; y", "a=\"x ; z", g), Verdict::Different);
        // `dword` keyword is case-sensitive (no CaseSensitive attribute).
        assert_eq!(v("a=dword:00000001", "a=DWORD:00000001", g), Verdict::Different);
    }

    #[test]
    fn cobol_columns_are_measured() {
        let g = Grammar::Cobol;
        // Sequence-number columns (1-6 and 73-80) are unimportant.
        assert_eq!(v("000100 IDENTIFICATION DIVISION.",
                     "000200 IDENTIFICATION DIVISION.", g), Verdict::Similar);
        let cob72 = format!("{:<72}", "IDENTIFICATION DIVISION.");
        assert_eq!(v(&format!("{cob72}00010001"), &format!("{cob72}00020002"), g),
                   Verdict::Similar);
        // Column-7 `*` comments the line (below); a `*` elsewhere is an
        // operator. Strings carry their content verbatim.
        assert_eq!(v("000100       DISPLAY X * Y.", "000100       DISPLAY X * Z.", g),
                   Verdict::Different);
        assert_eq!(v("000100       DISPLAY 'X'.", "000100       DISPLAY 'Y'.", g),
                   Verdict::Different);
    }

    #[test]
    fn dfm_has_no_comment_element() {
        let g = Grammar::Dfm;
        assert_eq!(v("object A: B", "OBJECT A: B", g), Verdict::Similar);
        assert_eq!(v("Text = #65", "Text = #66", g), Verdict::Different);
        assert_eq!(v("Caption = 'It''s'", "Caption = 'It''x'", g), Verdict::Different);
        assert_eq!(v("{ note }", "{ other }", g), Verdict::Different);
    }

    // ---------------------------------------------------------------
    // PERL grammar (m53g/m53i/m53k/m53l/m53m probes)
    // ---------------------------------------------------------------

    fn verdicts(lines_l: &[&str], lines_r: &[&str], g: Grammar) -> Vec<Verdict> {
        let ls: Vec<String> = lines_l.iter().map(|s| s.to_string()).collect();
        let rs: Vec<String> = lines_r.iter().map(|s| s.to_string()).collect();
        let p = Plan::build(&ls, &rs, g);
        (0..ls.len()).map(|i| p.verdict(i, i)).collect()
    }

    #[test]
    fn perl_compares_everything_verbatim() {
        let g = Grammar::Perl;
        // CaseSensitive=False changes tokenization only, never comparison
        // (m53m: bare word, $Name, $FOO, @Items ALL different).
        assert_eq!(v("my $Name = 1;", "my $name = 1;", g), Verdict::Different);
        assert_eq!(v("Name = 1;", "name = 1;", g), Verdict::Different);
        assert_eq!(v("@Items = (1);", "@items = (1);", g), Verdict::Different);
        assert_eq!(v("$x = 0x1F;", "$x = 0x1f;", g), Verdict::Different);
        assert_eq!(v("$x = 1; # alpha", "$x = 1; # beta", g), Verdict::Similar);
    }

    #[test]
    fn perl_strings_span_lines_and_absorb_comments() {
        let g = Grammar::Perl;
        // StopText without StopEOL: the `#` is string content and the span
        // carries to the next line (m53g `perl-dquote-multi-hash`).
        assert_eq!(
            verdicts(&["$x = \"a", "# b"], &["$x = \"a", "# c"], g),
            vec![Verdict::Same, Verdict::Different]
        );
        assert_eq!(
            verdicts(&["$x = 'a", "# b"], &["$x = 'a", "# c"], g),
            vec![Verdict::Same, Verdict::Different]
        );
        // A close at column 0 of the next line ends the span; the `#` after
        // it is a real comment (m53k `str-closed-next-line` = similar).
        assert_eq!(
            verdicts(&["$x = \"a", "b\"; # one", "code();"],
                     &["$x = \"a", "b\"; # two", "code();"], g),
            vec![Verdict::Same, Verdict::Similar, Verdict::Same]
        );
        // Escaped quote inside, then a real comment after the close (m53l).
        assert_eq!(v("$x = 'a\\'b';", "$x = 'a\\'c';", g), Verdict::Different);
    }

    #[test]
    fn perl_pod_blocks_stop_at_line_start() {
        let g = Grammar::Perl;
        assert_eq!(
            verdicts(&["=pod", "body one", "=cut", "code();"],
                     &["=pod", "body two", "=cut", "code();"], g),
            vec![Verdict::Same, Verdict::Similar, Verdict::Same, Verdict::Same]
        );
        // The stop line belongs to the comment in full (m53k `pod-stop-tail`).
        assert_eq!(
            verdicts(&["=pod", "b", "=cut Z1", "code();"],
                     &["=pod", "b", "=cut Z2", "code();"], g),
            vec![Verdict::Same, Verdict::Same, Verdict::Similar, Verdict::Same]
        );
        // A stop marker mid-line does NOT close the block (m53g
        // `perl-pod-mid-cut`): line 3 stays comment content -> similar.
        assert_eq!(
            verdicts(&["=pod", "x =cut y", "z"],
                     &["=pod", "x =cut y", "w"], g),
            vec![Verdict::Same, Verdict::Same, Verdict::Similar]
        );
        assert_eq!(
            verdicts(&["=over", "body one", "=back"],
                     &["=over", "body two", "=back"], g),
            vec![Verdict::Same, Verdict::Similar, Verdict::Same]
        );
    }

    #[test]
    fn perl_quote_like_and_regex_forms() {
        let g = Grammar::Perl;
        // The division-shaped `/[^/]*/` element is real: `/ b /` pairs as a
        // string (m53g `perl-regex-division` = different).
        assert_eq!(v("$x = a / b / c;", "$x = a / d / c;", g), Verdict::Different);
        // `/.../` absorbs `#` (m53g `perl-regex-hash` = different).
        assert_eq!(v("$s = /a # b/;", "$s = /a # c/;", g), Verdict::Different);
        // `q(...)` is a string (m53g `perl-q-paren` = different).
        assert_eq!(v("$w = q(alpha);", "$w = q(beta);", g), Verdict::Different);
        assert_eq!(v("$w = q(a # b);", "$w = q(a # c);", g), Verdict::Different);
        // `s/.../.../` absorbs `#` in the first segment (m53l
        // `s-slash-hash` = different).
        assert_eq!(v("s/a # b/c/;", "s/a # b/d/;", g), Verdict::Different);
        // NO `#`-delimiter forms (m53l `s-hash-delim` = similar: the first
        // `#` is a real comment, the tail is comment content on both sides).
        assert_eq!(v("s#a#b#c#d#;", "s#a#b#c#e#;", g), Verdict::Similar);
        // `s/ONE/TWO/` vs `s/one/two/`: everything verbatim (m53g).
        assert_eq!(v("s/ONE/TWO/;", "s/one/two/;", g), Verdict::Different);
    }
}

