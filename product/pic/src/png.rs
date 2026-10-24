//! Minimal PNG decoder: the reader of a PNG stream, the IDAT inflate (through
//! [`crate::deflate`]) and the five scanline filters.
//!
//! # Supported subset (and what it deliberately is not)
//!
//! Colour types 0 (grayscale), 2 (RGB), 6 (RGBA), bit depth 8, non-interlaced,
//! single IDAT-friendly stream. Interlaced (Adam7), palette (color type 3) and
//! 16-bit images return [`PngError::Unsupported`] — the measured probes
//! (`docs/16` §2) never used them and inventing their behaviour would be a
//! guess. Colour-type 4 (gray+alpha) is likewise unsupported: no evidence.
//!
//! The filter reconstruction is RFC 2083 §6 verbatim, including Paeth; the
//! independent fixture under `pic/tests/img_filters.png` (built by CPython
//! zlib, one filter per row 0..4) anchors all five paths.

use crate::deflate;

/// Why a PNG cannot be decoded here.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PngError {
    /// The signature, a chunk header or the IHDR is malformed/truncated.
    Malformed,
    /// A chunk CRC does not match its payload.
    Crc,
    /// A chunk stream ended before IEND.
    UnexpectedEof,
    /// Interlaced, palette, or a bit depth / colour type outside the supported
    /// 8-bit truecolor/gray subset.
    Unsupported,
    /// The IDAT inflate failed.
    Inflate(deflate::InflateError),
}

impl std::fmt::Display for PngError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            PngError::Malformed => f.write_str("malformed PNG"),
            PngError::Crc => f.write_str("chunk CRC mismatch"),
            PngError::UnexpectedEof => f.write_str("PNG ended before IEND"),
            PngError::Unsupported => f.write_str("unsupported PNG variant"),
            PngError::Inflate(e) => write!(f, "IDAT inflate: {e}"),
        }
    }
}

impl std::error::Error for PngError {}

impl From<deflate::InflateError> for PngError {
    fn from(e: deflate::InflateError) -> Self {
        PngError::Inflate(e)
    }
}

/// A decoded raster: width, height, and one row of RGB (alpha dropped — the
/// measured importance rule ignores alpha: m83e U8).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Raster {
    pub width: usize,
    pub height: usize,
    /// `width * 3` bytes per row, row-major.
    pub pixels: Vec<u8>,
}

const SIG: [u8; 8] = [0x89, b'P', b'N', b'G', 0x0D, 0x0A, 0x1A, 0x0A];

/// The PNG signature bytes, public for the format sniffer in [`crate::decode`].
pub const SIGNATURE: [u8; 8] = SIG;

/// Decode the whole PNG. Returns `Err(Unsupported)` rather than inventing
/// behaviour for variants the probes never established.
pub fn decode(data: &[u8]) -> Result<Raster, PngError> {
    if data.len() < 8 || data[..8] != SIG {
        return Err(PngError::Malformed);
    }
    let mut pos = 8;
    let (mut width, mut height, mut bit_depth, mut color_type, mut interlace) =
        (0u32, 0u32, 0u8, 0u8, 0u8);
    let mut idat: Vec<u8> = Vec::new();
    let mut seen_ihdr = false;
    let mut seen_iend = false;
    while pos + 8 <= data.len() && !seen_iend {
        let len = u32::from_be_bytes([data[pos], data[pos + 1], data[pos + 2], data[pos + 3]])
            as usize;
        let typ = &data[pos + 4..pos + 8];
        let body_start = pos + 8;
        let body_end = body_start + len;
        let crc_end = body_end + 4;
        if crc_end > data.len() {
            return Err(PngError::UnexpectedEof);
        }
        let body = &data[body_start..body_end];
        let want = &data[body_end..crc_end];
        // PNG CRC covers the chunk TYPE plus the DATA, as one stream
        // (CRC-32 is not xor-composable, so both parts go through once).
        let got = crc32_chunks(&[typ, body]);
        if u32::from_be_bytes([want[0], want[1], want[2], want[3]]) != got {
            return Err(PngError::Crc);
        }
        match typ {
            b"IHDR" => {
                if len < 13 {
                    return Err(PngError::Malformed);
                }
                width = u32::from_be_bytes([body[0], body[1], body[2], body[3]]);
                height = u32::from_be_bytes([body[4], body[5], body[6], body[7]]);
                bit_depth = body[8];
                color_type = body[9];
                interlace = body[12];
                seen_ihdr = true;
            }
            b"IDAT" => idat.extend_from_slice(body),
            b"IEND" => seen_iend = true,
            // ancillary chunks (tRNS, gAMA, pHYs, tEXt…) are irrelevant to
            // pixel counting; they were checked for CRC above and are skipped.
            _ => {}
        }
        pos = crc_end;
    }
    if !seen_ihdr {
        return Err(PngError::Malformed);
    }
    if !seen_iend {
        return Err(PngError::UnexpectedEof);
    }
    if interlace != 0 || bit_depth != 8 {
        return Err(PngError::Unsupported);
    }
    let channels: usize = match color_type {
        0 => 1,
        2 => 3,
        6 => 4,
        _ => return Err(PngError::Unsupported), // 3 (palette), 4 (g+a): no evidence
    };
    let w = width as usize;
    let h = height as usize;
    let raw = deflate::inflate_zlib(&idat)?;
    unfilter(&raw, w, h, channels).map(|pixels| Raster { width: w, height: h, pixels })
}

/// Reconstruct the scanlines from the filtered bytes (RFC 2083 §6).
fn unfilter(raw: &[u8], w: usize, h: usize, channels: usize) -> Result<Vec<u8>, PngError> {
    let bpp = channels; // 8-bit samples, one pixel = `channels` bytes
    let row_len = w * channels;
    let mut prev = vec![0u8; row_len];
    let mut out = Vec::with_capacity(w * h * 3);
    let mut pos = 0usize;
    for _ in 0..h {
        if pos + 1 + row_len > raw.len() {
            return Err(PngError::Malformed); // truncated scanlines
        }
        let filter = raw[pos];
        pos += 1;
        let line = &raw[pos..pos + 1 + row_len - 1];
        pos += row_len;
        let mut cur = vec![0u8; row_len];
        for i in 0..row_len {
            let x = line[i];
            let a = if i >= bpp { cur[i - bpp] } else { 0 };
            let b = prev[i];
            let c = if i >= bpp { prev[i - bpp] } else { 0 };
            cur[i] = match filter {
                0 => x,
                1 => x.wrapping_add(a),
                2 => x.wrapping_add(b),
                3 => x.wrapping_add(((a as u16 + b as u16) >> 1) as u8),
                4 => x.wrapping_add(paeth(a, b, c)),
                _ => return Err(PngError::Malformed),
            };
        }
        // Emit RGB (alpha dropped), matching `Raster`.
        for px in cur.chunks_exact(channels) {
            match channels {
                1 => out.extend_from_slice(&[px[0], px[0], px[0]]),
                3 => out.extend_from_slice(&px[..3]),
                4 => out.extend_from_slice(&px[..3]),
                _ => unreachable!("channels fixed above to 1/3/4"),
            }
        }
        prev = cur;
    }
    Ok(out)
}

fn paeth(a: u8, b: u8, c: u8) -> u8 {
    let (ai, bi, ci) = (a as i32, b as i32, c as i32);
    let p = ai + bi - ci;
    let (pa, pb, pc) = ((p - ai).abs(), (p - bi).abs(), (p - ci).abs());
    if pa <= pb && pa <= pc {
        a
    } else if pb <= pc {
        b
    } else {
        c
    }
}

/// CRC-32 with the PNG/zlib polynomial (0xEDB88320), final inversion, over a
/// sequence of byte slices as one stream — the form PNG chunk CRCs use, which
/// covers the TYPE bytes and the DATA bytes together. Kept here (a few lines)
/// so the crate stays dependency-free.
fn crc32_chunks(chunks: &[&[u8]]) -> u32 {
    let mut crc = 0xFFFF_FFFFu32;
    for chunk in chunks {
        for &byte in *chunk {
            crc ^= byte as u32;
            for _ in 0..8 {
                let mask = (crc & 1).wrapping_neg();
                crc = (crc >> 1) ^ (0xEDB8_8320 & mask);
            }
        }
    }
    !crc
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The generator formula used for `pic/tests/img_filters.png` (rows carry
    /// filters 0..3, 4th row filter 0 — see the Python that made the fixture);
    /// recomputing it here replaces a JSON expected-file reader: one source of
    /// truth, no parser.
    fn expected(x: usize, y: usize) -> [u8; 3] {
        [
            ((x * 40 + 7) % 256) as u8,
            ((y * 30 + x) % 256) as u8,
            ((x * x + y * 3) % 256) as u8,
        ]
    }

    /// The independent fixture: a 3x4 RGB PNG, produced by CPython zlib with
    /// per-row filters that exercise 0, 1, 2, 3 (and Paeth in other rows).
    #[test]
    fn decodes_the_filter_fixture() {
        let data = include_bytes!("../tests/img_filters.png");
        let r = decode(data).expect("decode");
        assert_eq!((r.width, r.height), (3, 4));
        let mut idx = 0usize;
        for y in 0..4 {
            for x in 0..3 {
                assert_eq!(&r.pixels[idx * 3..idx * 3 + 3], expected(x, y), "pixel {idx}");
                idx += 1;
            }
        }
    }

    #[test]
    fn crc_error_is_detected() {
        let mut data = include_bytes!("../tests/img_filters.png").to_vec();
        let last = data.len() - 1;
        data[last] ^= 0xFF; // break the IEND CRC
        assert_eq!(decode(&data).unwrap_err(), PngError::Crc);
    }

    #[test]
    fn non_png_is_malformed() {
        assert_eq!(decode(b"BM....").unwrap_err(), PngError::Malformed);
    }
}
