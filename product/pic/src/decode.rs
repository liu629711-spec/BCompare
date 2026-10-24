//! Format sniffing: one entry point that turns bytes into a [`Raster`] or a
//! measured error kind.
//!
//! The two error strings are the ones the Oracle itself prints
//! (`docs/16` §1): `不被支持的类型` for content with no picture signature
//! (m83 P12, a 4-byte `.bin`), and `无效图像` for a file whose signature says
//! picture but whose payload does not decode (m83i V3, a malformed GIF).

use crate::{bmp, png, Raster};

/// Why an input file is not a decodable picture.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ImageError {
    /// No known picture signature (the Oracle's 不被支持的类型).
    NotSupported,
    /// A picture signature was found but the payload does not decode, or the
    /// variant is outside the implemented decoder set (the Oracle's 无效图像).
    ///
    /// Known signatures recognized here are PNG, BMP, GIF and JPEG. GIF and
    /// JPEG are decoded by neither: a VALID GIF/JPEG would produce counts in
    /// the Oracle but yields this error here — recorded as a limitation
    /// (`docs/16` §5), because the measured cells never supplied a valid GIF
    /// or JPEG to compare against.
    Invalid,
}

impl std::fmt::Display for ImageError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ImageError::NotSupported => f.write_str("not a supported image type"),
            ImageError::Invalid => f.write_str("invalid image"),
        }
    }
}

impl std::error::Error for ImageError {}

/// Sniff and decode. Dispatch is by signature, exactly the two strings
/// measured on the Oracle.
pub fn decode_image(data: &[u8]) -> Result<Raster, ImageError> {
    if data.len() >= 8 && data[..8] == png::SIGNATURE {
        return png::decode(data).map_err(|_| ImageError::Invalid);
    }
    if data.starts_with(b"BM") {
        return bmp::decode(data).map_err(|_| ImageError::Invalid);
    }
    // GIF87a/GIF89a and JPEG SOI are picture signatures BC knows (m83i V3's
    // malformed GIF answered 无效图像, not 不被支持的类型) — this build has no
    // decoder for them, so they answer Invalid like an un-decodable payload.
    if data.starts_with(b"GIF87a") || data.starts_with(b"GIF89a") || data.starts_with(b"\xFF\xD8\xFF")
    {
        return Err(ImageError::Invalid);
    }
    Err(ImageError::NotSupported)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bin_is_not_supported() {
        assert_eq!(decode_image(b"\x00\x01\x02\x03").unwrap_err(), ImageError::NotSupported);
    }

    #[test]
    fn malformed_gif_is_invalid() {
        assert_eq!(decode_image(b"GIF89a\x01\x00garbage").unwrap_err(), ImageError::Invalid);
    }

    #[test]
    fn png_signature_routes_to_the_png_decoder() {
        let r = decode_image(include_bytes!("../tests/img_gray.png")).expect("decode");
        assert_eq!((r.width, r.height), (2, 2));
    }

    #[test]
    fn corrupted_png_body_is_invalid_not_unsupported() {
        let mut data = include_bytes!("../tests/img_gray.png").to_vec();
        data[30] ^= 0xFF; // break the IDAT payload (a CRC-valid other chunk?
                          // IDAT CRC will mismatch -> Invalid by the map above)
        assert_eq!(decode_image(&data).unwrap_err(), ImageError::Invalid);
    }
}
