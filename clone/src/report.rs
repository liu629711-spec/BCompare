//! XML report writer matching BC's observable format.
//! Golden-verified: header, CRLF body, tab indent, decimal charrefs for
//! control chars, ltid/rtid numbering (1-based, per-file).

use crate::align::{Group, Status};

fn esc(s: &str) -> String {
    let mut o = String::new();
    for c in s.chars() {
        match c {
            '&' => o.push_str("&amp;"),
            '<' => o.push_str("&lt;"),
            '>' => o.push_str("&gt;"),
            c if (c as u32) < 0x20 && c != '\t' => o.push_str(&format!("&#{};", c as u32)),
            c => o.push(c),
        }
    }
    o
}

pub fn to_xml(groups: &[Group], lines_l: &[String], lines_r: &[String]) -> String {
    let mut o = String::new();
    o.push_str("<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n");
    o.push_str("<bcreport>\r\n");
    o.push_str("\t<filecomparison>\r\n");
    for g in groups {
        let status = match g.status {
            Status::Same => "same",
            Status::Similar => "similar",
            Status::Different => "different",
            Status::LeftOrphan => "leftorphan",
            Status::RightOrphan => "rightorphan",
        };
        o.push_str(&format!("\t\t<linecomp status=\"{}\">\r\n", status));
        match (g.left, g.right) {
            (Some(li), Some(ri)) if g.status == Status::Same => {
                o.push_str(&format!(
                    "\t\t\t<text ltid=\"{}\" rtid=\"{}\">{}</text>\r\n",
                    li + 1, ri + 1, esc(&lines_l[li])
                ));
            }
            (Some(li), Some(ri)) => {
                o.push_str(&format!(
                    "\t\t\t<text ltid=\"{}\">{}</text>\r\n",
                    li + 1, esc(&lines_l[li])
                ));
                o.push_str(&format!(
                    "\t\t\t<text rtid=\"{}\">{}</text>\r\n",
                    ri + 1, esc(&lines_r[ri])
                ));
            }
            (Some(li), None) => {
                o.push_str(&format!(
                    "\t\t\t<text ltid=\"{}\">{}</text>\r\n",
                    li + 1, esc(&lines_l[li])
                ));
            }
            (None, Some(ri)) => {
                o.push_str(&format!(
                    "\t\t\t<text rtid=\"{}\">{}</text>\r\n",
                    ri + 1, esc(&lines_r[ri])
                ));
            }
            (None, None) => {}
        }
        o.push_str("\t\t</linecomp>\r\n");
    }
    o.push_str("\t</filecomparison>\r\n</bcreport>\r\n");
    o
}
