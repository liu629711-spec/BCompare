//! Pixel classification and counting — the measured Picture Compare model.
//!
//! Every rule below is a `docs/16` citation; none is a guess.
//!
//! Categories (line order FIXED by the m83h/m83i/m83j measurements):
//! `相同` → `不重要` → `左边独有` → `右边独有` → `重要`. A category with a
//! count of zero prints no line (m83b Q1).
//!
//! Per overlapping pixel (`min(w) x min(h)` region):
//! * RGB identical → same (alpha ignored — m83e U8, 64 same);
//! * otherwise, if any of the three channels differs by at least
//!   [`IMPORTANCE_THRESHOLD`] → important (m83e U2: Δ31, U5: Δ32 important;
//!   U4/T-d24: Δ24/25 unimportant);
//! * otherwise → unimportant.
//! Pixels beyond the overlap on the larger side are that side's own
//! (m83j: 36 same + 12 left-only + 12 right-only; m83e R7/U10 per-side).
//!
//! Two size rules from the same batch of measurements: the sum of all five
//! counts always equals `max(w*h, ...)` pixels of the two images — never
//! double-counted — and `options:ignore-unimportant` renames the unimportant
//! line's label without changing any number (m83i V2: `忽略的不重要`).

/// The measured per-channel boundary: a difference of THIS value or more is
/// "important". (The Oracle's own threshold sits between 25 and 26 — every
/// cell at ≤25 came back unimportant and every cell at ≥26 important, m83e
/// U3/U4 and m83f. WHY 26 is BC's number is not derivable from these probes
/// and is recorded as a residual unknown in `docs/16` §5; the constant is not
/// a guess — it is the smallest value the measurements prove.)
pub const IMPORTANCE_THRESHOLD: u8 = 26;

/// The knobs the report takes from the script's `options:` list.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct CompareOptions {
    /// `ignore-unimportant` was given: the unimportant category prints with
    /// the 忽略 label (the count itself is unchanged — m83i V2).
    pub ignore_unimportant: bool,
}

/// The five measured counts, in printing order.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct PictureCounts {
    pub same: usize,
    pub unimportant: usize,
    pub left_only: usize,
    pub right_only: usize,
    pub important: usize,
}

impl PictureCounts {
    /// The non-zero lines in the measured order, as `(label-key, count)`
    /// pairs for the report renderer. `label-key` is one of the five names;
    /// the renderer maps it to the localized text (and the 忽略 variant).
    pub fn lines(&self, o: &CompareOptions) -> Vec<(&'static str, usize)> {
        let mut out = Vec::new();
        if self.same != 0 {
            out.push(("same", self.same));
        }
        if self.unimportant != 0 {
            out.push((if o.ignore_unimportant { "ignored-unimportant" } else { "unimportant" },
                      self.unimportant));
        }
        if self.left_only != 0 {
            out.push(("left-only", self.left_only));
        }
        if self.right_only != 0 {
            out.push(("right-only", self.right_only));
        }
        if self.important != 0 {
            out.push(("important", self.important));
        }
        out
    }
}

/// Classify two rasters. Pixels outside the overlap go to the surplus side's
/// "own" count; inside, [`IMPORTANCE_THRESHOLD`]-or-more on any RGB channel is
/// important, any other difference is unimportant.
pub fn compare_rasters(left: &crate::Raster, right: &crate::Raster) -> PictureCounts {
    let mut c = PictureCounts::default();
    let ow = left.width.min(right.width);
    let oh = left.height.min(right.height);
    for y in 0..oh {
        for x in 0..ow {
            let li = (y * left.width + x) * 3;
            let ri = (y * right.width + x) * 3;
            let lp = &left.pixels[li..li + 3];
            let rp = &right.pixels[ri..ri + 3];
            if lp == rp {
                c.same += 1;
            } else if lp.iter().zip(rp).any(|(a, b)| a.abs_diff(*b) >= IMPORTANCE_THRESHOLD) {
                c.important += 1;
            } else {
                c.unimportant += 1;
            }
        }
    }
    let l_total = left.width * left.height;
    let r_total = right.width * right.height;
    let overlap = ow * oh;
    c.left_only = l_total - overlap;
    c.right_only = r_total - overlap;
    c
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::Raster;

    fn raster(w: usize, h: usize, fill: [u8; 3]) -> Raster {
        let mut pixels = Vec::with_capacity(w * h * 3);
        for _ in 0..(w * h) {
            pixels.extend_from_slice(&fill);
        }
        Raster { width: w, height: h, pixels }
    }

    #[test]
    fn equal_images_count_all_same() {
        let c = compare_rasters(&raster(8, 8, [10, 20, 30]), &raster(8, 8, [10, 20, 30]));
        assert_eq!(c, PictureCounts { same: 64, ..Default::default() });
        // m83b Q1: the zero categories print nothing.
        assert_eq!(c.lines(&CompareOptions::default()), vec![("same", 64)]);
    }

    #[test]
    fn boundary_is_exact() {
        // <=25 unimportant, >=26 important (m83e U3/U4, m83f).
        for d in 0..=25u8 {
            let c = compare_rasters(&raster(1, 1, [100, 100, 100]), &raster(1, 1, [100 + d, 100, 100]));
            assert_eq!((c.important, c.unimportant), (if d == 0 { 0 } else { 0 }, if d == 0 { 0 } else { 1 }), "delta {d}");
            assert_eq!((c.same + c.important + c.unimportant), 1, "delta {d}");
            if d == 0 {
                assert_eq!(c.same, 1);
            } else {
                assert_eq!(c.unimportant, 1);
            }
        }
        for d in 26..=155u8 {
            let c = compare_rasters(&raster(1, 1, [100, 100, 100]), &raster(1, 1, [100 + d, 100, 100]));
            assert_eq!(c.important, 1, "delta {d} must be important");
        }
    }

    #[test]
    fn per_channel_not_summed() {
        // m83d T8: two channels of 20 (sum 40) stayed unimportant — the rule
        // is a per-channel maximum, not a sum.
        let c = compare_rasters(
            &raster(1, 1, [100, 100, 100]),
            &raster(1, 1, [120, 120, 100]),
        );
        assert_eq!(c.unimportant, 1);
    }

    #[test]
    fn size_surplus_goes_to_the_larger_side() {
        // m83j: 6x8 vs 8x6 with identical overlap colour -> 36 same + 12 L + 12 R.
        let l = raster(6, 8, [128, 128, 128]);
        let r = raster(8, 6, [128, 128, 128]);
        let c = compare_rasters(&l, &r);
        assert_eq!(
            c,
            PictureCounts { same: 36, left_only: 12, right_only: 12, ..Default::default() }
        );
        assert_eq!(
            c.lines(&CompareOptions::default()),
            vec![("same", 36), ("left-only", 12), ("right-only", 12)]
        );
    }

    #[test]
    fn ignore_renames_without_recounting() {
        // m83i V2: same numbers, the 忽略 label instead.
        let mut counts = PictureCounts::default();
        counts.unimportant = 32;
        counts.important = 16;
        let plain = counts.lines(&CompareOptions::default());
        let ignored = counts.lines(&CompareOptions { ignore_unimportant: true });
        assert_eq!(plain[0], ("unimportant", 32));
        assert_eq!(ignored[0], ("ignored-unimportant", 32));
        assert_eq!(ignored[1], ("important", 16));
    }

    #[test]
    fn measured_four_category_order() {
        // m83h F.all4: same, unimportant, left-only, important in one report.
        let mut c = PictureCounts { same: 12, unimportant: 24, left_only: 16, important: 12, right_only: 0 };
        assert_eq!(
            c.lines(&CompareOptions::default()),
            vec![("same", 12), ("unimportant", 24), ("left-only", 16), ("important", 12)]
        );
        c.right_only = 1;
        assert!(c.lines(&CompareOptions::default())
            .iter()
            .position(|p| p.0 == "right-only")
            .unwrap()
            < c.lines(&CompareOptions::default())
                .iter()
                .position(|p| p.0 == "important")
                .unwrap());
    }
}
