//! BC-compatible script front end and executor (M4).
//!
//! # Layout of this module
//!
//! | file | owner | contents |
//! |---|---|---|
//! | `ast.rs` | frozen (main session) | the command types, shared by all three |
//! | `lex.rs` | task A | logical-line joining (`&` continuation, `#` comments) |
//! | `parse.rs` | task A | logical lines -> [`Command`]s |
//! | `exec.rs` | task B | [`Command`]s -> reports + exit code |
//!
//! # Why the AST is frozen
//!
//! Three work packages are being implemented in parallel and they only meet at
//! these types.  Changing a field here means changing all three, so the shape is
//! settled by `product/docs/09-m4-interfaces.md` and by the observed Oracle
//! behaviour in `product/verify/probes/U5-FINDINGS.md`.  Any change must update
//! that document first.

pub mod ast;
pub mod exec;
pub mod lex;
pub mod parse;

pub use ast::{Command, ExpandPaths, LogMode, ReportSpec, ScriptError};
pub use exec::{run_script, ScriptOutcome};
pub use lex::logical_lines;
pub use parse::parse_script;
