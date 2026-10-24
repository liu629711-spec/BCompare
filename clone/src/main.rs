mod align;
mod layouts;
mod lines;
mod report;
mod syntax;

use std::path::PathBuf;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        eprintln!("usage: bcx <left> <right> [out.xml] [--opt=<options>]");
        std::process::exit(2);
    }
    let opts = args.iter().find(|a| a.starts_with("--opt=")).cloned().unwrap_or_default();
    let left = std::fs::read(&args[1]).expect("read left");
    let right = std::fs::read(&args[2]).expect("read right");

    let l = lines::split(&left);
    let r = lines::split(&right);
    let aware = syntax::is_syntax_aware(&args[1]);
    let mut groups = align::align(&l, &r, aware);

    // Report options per the official reference:
    //   ignore-unimportant  – treat unimportant differences as matches
    //   display-all|mismatches|context|matches – which lines appear
    if opts.contains("ignore-unimportant") {
        for g in groups.iter_mut() {
            if g.status == align::Status::Similar {
                g.status = align::Status::Same;
            }
        }
    }
    if opts.contains("display-mismatches") {
        groups.retain(|g| g.status != align::Status::Same);
    } else if opts.contains("display-matches") {
        groups.retain(|g| g.status == align::Status::Same);
    }
    let layout = args.iter().find(|a| a.starts_with("--layout="))
        .map(|a| a["--layout=".len()..].to_string())
        .unwrap_or_else(|| "xml".to_string());
    let xml = match layout.as_str() {
        "side-by-side" => layouts::side_by_side(&groups, &l, &r, &args[1], &args[2]),
        "interleaved" | "over-under" => layouts::interleaved(&groups, &l, &r, &args[1], &args[2]),
        "patch" => layouts::patch(&groups, &l, &r, &args[1], &args[2]),
        "summary" => layouts::summary(&groups, &args[1], &args[2]),
        "statistics" => layouts::statistics(&groups, &l, &args[1], &args[2]),
        _ => report::to_xml(&groups, &l, &r),
    };

    match args.get(3).filter(|p| !p.starts_with("--")) {
        Some(p) => std::fs::write(PathBuf::from(p), &xml).expect("write out"),
        None => print!("{xml}"),
    }
}
