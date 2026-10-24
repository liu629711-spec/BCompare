//! 24-bit uncompressed BMP decode.
//!
//! Supports exactly what the measured fixtures exercise (`docs/16` §2: m83e
//! U10 ran a 24-bit BMP through the same importance rule): the classic
//! BITMAPINFOHEADER (40-byte DIB), 24 bits per pixel, no compression,
//! bottom-up or top-down rows. Anything else — palettes, RLE, 16/32-bit,
//! other header flavours — returns [`BmpError::Unsupported`] rather than
//! guessing.

/// Why a BMP cannot be decoded here.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BmpError {
    Malformed,
    Unsupported,
}

impl std::fmt::Display for BmpError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            BmpError::Malformed => f.write_str("malformed BMP"),
            BmpError::Unsupported => f.write_str("unsupported BMP variant"),
        }
    }
}

impl std::error::Error for BmpError {}

pub fn decode(data: &[u8]) -> Result<crate::png::Raster, BmpError> {
    if data.len() < 54 || data[0] != b'B' || data[1] != b'M' {
        return Err(BmpError::Malformed);
    }
    let dib_size = u32::from_le_bytes([data[14], data[15], data[16], data[17]]) as usize;
    if dib_size != 40 {
        return Err(BmpError::Unsupported);
    }
    let width = i32::from_le_bytes([data[18], data[19], data[20], data[21]]) as i64;
    let height = i32::from_le_bytes([data[22], data[23], data[24], data[25]]) as i64;
    let planes = u16::from_le_bytes([data[26], data[27]]);
    let bpp = u16::from_le_bytes([data[28], data[29]]);
    let compression = u32::from_le_bytes([data[30], data[31], data[32], data[33]]);
    let bits_offset = u32::from_le_bytes([data[10], data[11], data[12], data[13]]) as usize;
    if planes != 1 || bpp != 24 || compression != 0 || width <= 0 || height == 0 {
        return Err(BmpError::Unsupported);
    }
    let (w, top_down) = (width as usize, height < 0);
    let h = height.unsigned_abs() as usize;
    let row_stride = (w * 3 + 3) & !3;
    if bits_offset + row_stride * h > data.len() {
        return Err(BmpError::Malformed);
    }
    let mut pixels = vec![0u8; w * h * 3];
    for y in 0..h {
        // BMP stores the first row at `bits_offset`; a positive height means
        // that first row is the BOTTOM of the image.
        let src_row = if top_down { y } else { h - 1 - y };
        let src = &data[bits_offset + src_row * row_stride..][..w * 3];
        let dst = &mut pixels[y * w * 3..][..w * 3];
        for (d, s) in dst.chunks_exact_mut(3).zip(src.chunks_exact(3)) {
            d.copy_from_slice(&[s[2], s[1], s[0]]); // BGR -> RGB
        }
    }
    Ok(crate::png::Raster { width: w, height: h, pixels })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn solid_bmp(w: usize, h: usize, rgb: (u8, u8, u8)) -> Vec<u8> {
        let stride = (w * 3 + 3) & !3;
        let mut rows = Vec::new();
        for _ in 0..h {
            let mut row = Vec::with_capacity(stride);
            for _ in 0..w {
                row.extend_from_slice(&[rgb.2, rgb.1, rgb.0]); // BGR
            }
            row.resize(stride, 0);
            rows.extend_from_slice(&row);
        }
        let size = 54 + rows.len();
        let mut out = Vec::new();
        out.extend_from_slice(b"BM");
        out.extend_from_slice(&(size as u32).to_le_bytes());
        out.extend_from_slice(&[0u8; 4]);
        out.extend_from_slice(&54u32.to_le_bytes());
        out.extend_from_slice(&40u32.to_le_bytes());
        out.extend_from_slice(&(w as u32).to_le_bytes());
        out.extend_from_slice(&(h as u32).to_le_bytes());
        out.extend_from_slice(&1u16.to_le_bytes());
        out.extend_from_slice(&24u16.to_le_bytes());
        out.extend_from_slice(&0u32.to_le_bytes());
        out.extend_from_slice(&(rows.len() as u32).to_le_bytes());
        // xppm, yppm, clrused, clrimportant: 16 bytes finish the 40-byte DIB.
        out.extend_from_slice(&[0u8; 16]);
        out.extend_from_slice(&rows);
        out
    }

    #[test]
    fn decodes_a_24bit_bottom_up_bmp() {
        let r = decode(&solid_bmp(4, 4, (10, 20, 30))).expect("decode");
        assert_eq!((r.width, r.height), (4, 4));
        assert_eq!(&r.pixels[..3], &[10, 20, 30]);
        assert_eq!(r.pixels.len(), 4 * 4 * 3);
    }

    #[test]
    fn palette_bmp_is_unsupported() {
        let mut d = solid_bmp(2, 2, (1, 2, 3));
        d[28..30].copy_from_slice(&8u16.to_le_bytes()); // 8bpp
        assert_eq!(decode(&d).unwrap_err(), BmpError::Unsupported);
    }

    #[test]
    fn non_bmp_is_malformed() {
        assert_eq!(decode(b"XX....").unwrap_err(), BmpError::Malformed);
    }
}
