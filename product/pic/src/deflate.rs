//! Minimal DEFLATE (RFC 1951) decoder — the inflate half of zlib, which PNG
//! IDAT streams use.
//!
//! # Why this is here rather than a crate
//!
//! `reacmp-core`, `reacmp-dir` and `reacmp-vfs` are hermetic: zero third-party
//! dependencies, so `cargo test` works offline and the gate never depends on a
//! registry cache existing. The picture channel needs PNG decode, which needs
//! inflate, so this reproduces the algorithm instead of adding a dependency and
//! breaking that invariant for the whole tree (`docs/02`).
//!
//! # Method
//!
//! A direct transcription of the reference "puff" decoder (zlib's `puff.c`):
//! build, per Huffman code, a `count[]` (codes of each length) and a `symbol[]`
//! (symbols ordered by code); then read bits, accumulating a code, and return
//! the symbol as soon as the code falls in the current length's span. The
//! length and distance tables are RFC 1951 §3.2.5 verbatim. Stored, fixed and
//! dynamic blocks are all supported — there is no partial coverage to hide.
//!
//! # Verification
//!
//! The fixtures under `pic/tests/` are produced by CPython's `zlib` (an
//! independent implementation), not by this decoder: `deflate_dynamic.bin`
//! (level 6 → a dynamic block) and `deflate_stored.bin` (level 0 → stored
//! blocks). Passing against those is the correctness anchor.

/// An inflate failure. Every caller either propagates it or treats the image
/// as invalid; the kind is for the message only.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InflateError {
    /// The input ended mid-block, mid-table or mid-symbol.
    UnexpectedEof,
    /// A reserved block type, a bad `NLEN`, a distance past the data written,
    /// or a code the table does not contain.
    Corrupt,
}

impl std::fmt::Display for InflateError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            InflateError::UnexpectedEof => f.write_str("unexpected end of input"),
            InflateError::Corrupt => f.write_str("corrupt deflate stream"),
        }
    }
}

impl std::error::Error for InflateError {}

/// Inflate a zlib stream (PNG's IDAT content): skip the 2-byte header, inflate
/// the raw DEFLATE body, ignore the trailing Adler-32 (as libpng does).
pub fn inflate_zlib(input: &[u8]) -> Result<Vec<u8>, InflateError> {
    if input.len() < 2 {
        return Err(InflateError::UnexpectedEof);
    }
    let cmf = input[0];
    let flg = input[1];
    // CM must be 8 (deflate) and CMF/FLG must satisfy the FCHECK mod-31 rule.
    if cmf & 0x0f != 8 || ((cmf as u16) << 8 | flg as u16) % 31 != 0 {
        return Err(InflateError::Corrupt);
    }
    Deiner::new(&input[2..]).inflate()
}

/// (base, extra-bits) pairs, indexed by symbol-257, RFC 1951 §3.2.5.
/// Checked cell by cell against the RFC table: idx 19 (symbol 276) is base 59
/// with 3 extra bits; the run of 4/5/6-bit groups must not slip.
const LENGTH: [(u16, u8); 29] = [
    (3, 0), (4, 0), (5, 0), (6, 0), (7, 0), (8, 0), (9, 0), (10, 0),
    (11, 1), (13, 1), (15, 1), (17, 1), (19, 2), (23, 2), (27, 2), (31, 2),
    (35, 3), (43, 3), (51, 3), (59, 3), (67, 4), (83, 4), (99, 4), (115, 4),
    (131, 5), (163, 5), (195, 5), (227, 5), (258, 0),
];

const DIST: [(u16, u8); 30] = [
    (1, 0), (2, 0), (3, 0), (4, 0), (5, 1), (7, 1), (9, 2), (13, 2),
    (17, 3), (25, 3), (33, 4), (49, 4), (65, 5), (97, 5), (129, 6), (193, 6),
    (257, 7), (385, 7), (513, 8), (769, 8), (1025, 9), (1537, 9), (2049, 10),
    (3073, 10), (4097, 11), (6145, 11), (8193, 12), (12289, 12), (16385, 13),
    (24577, 13),
];

/// A constructed Huffman code, the `code` struct of puff.c MINUS its `max`
/// field: puff's `decode()` needs `max` to stop its loop, but the decode here
/// walks `count[len]` until the code exhausts the 16 slots, so the value is
/// computed for the overflow check and then dropped.
///
/// `count[len]` is the number of codes of that length; `symbol[]` lists the
/// symbols in code order (by length, then by symbol). `count` has 17 slots so
/// that `decode`'s `count[len + 1]` cannot go out of bounds at `len == 16`.
#[derive(Debug)]
struct Code {
    count: [u32; 17],
    symbol: Vec<u32>,
}

impl Code {
    /// Build from a code-length array (puff.c's `construct()`).
    fn from_lengths(lens: &[u8]) -> Result<Code, InflateError> {
        let mut count = [0u32; 17];
        let mut max = 0u8;
        for &l in lens {
            if l >= 16 {
                return Err(InflateError::Corrupt);
            }
            count[l as usize] += 1;
            if l > max {
                max = l;
            }
        }
        if count[0] == lens.len() as u32 {
            // every symbol length 0 -> no code at all
            return Err(InflateError::Corrupt);
        }
        // A complete code: sum(count[len] << (max-len)) must equal 1 << max.
        // (puff.c's overflow check; an incomplete code is the usual bug.)
        let mut left = 1i64 << max;
        for len in 1..=max as usize {
            left -= (count[len] as i64) << (max as usize - len);
            if left < 0 {
                return Err(InflateError::Corrupt);
            }
        }
        let mut offs = [0u32; 17];
        // Only NON-zero-length symbols occupy the `symbol` array, ordered by
        // (length, symbol). offs[len] is where length-`len` symbols start, so
        // offs[1] is 0 (NOT count[0] — the zero-length symbols are skipped).
        for len in 1..16 {
            offs[len + 1] = offs[len] + count[len];
        }
        let total = offs[16] + count[16];
        let mut symbol = vec![0u32; total as usize];
        for (sym, &l) in lens.iter().enumerate() {
            if l != 0 {
                symbol[offs[l as usize] as usize] = sym as u32;
                offs[l as usize] += 1;
            }
        }
        Ok(Code { count, symbol })
    }

    /// The fixed literal/length and distance codes (RFC 1951 §3.2.6).
    fn fixed() -> (Code, Code) {
        let mut lit = vec![0u8; 288];
        for (i, v) in lit.iter_mut().enumerate() {
            *v = match i {
                0..=143 => 8,
                144..=255 => 9,
                256..=279 => 7,
                _ => 8,
            };
        }
        let dist = vec![5u8; 30];
        (
            Code::from_lengths(&lit).expect("fixed lit table is valid"),
            Code::from_lengths(&dist).expect("fixed dist table is valid"),
        )
    }

    /// A valid code holding the single symbol 0 (puff.c's `ret_ok`) for an
    /// empty distance tree: no distance symbol will ever decode against it.
    fn single_zero() -> Code {
        Code { count: [0u32; 17], symbol: Vec::new() }
    }
}

/// Inflate state: the bit reader, the output, and the two current codes.
struct Deiner<'a> {
    data: &'a [u8],
    pos: usize,
    bitbuf: u32,
    left: u8,
    out: Vec<u8>,
}

impl<'a> Deiner<'a> {
    fn new(data: &'a [u8]) -> Self {
        Deiner { data, pos: 0, bitbuf: 0, left: 0, out: Vec::new() }
    }

    /// Read `n` bits (0 <= n <= 25), LSB-first within each byte.
    fn bits(&mut self, n: u8) -> Result<u32, InflateError> {
        if n == 0 {
            return Ok(0);
        }
        while self.left < n {
            if self.pos >= self.data.len() {
                return Err(InflateError::UnexpectedEof);
            }
            self.bitbuf |= (self.data[self.pos] as u32) << self.left;
            self.pos += 1;
            self.left += 8;
        }
        let mask = (1u32 << n) - 1;
        let v = self.bitbuf & mask;
        self.bitbuf >>= n;
        self.left -= n;
        Ok(v)
    }

    /// Decode one symbol (puff.c's `decode()`): accumulate a code MSB-first
    /// while it stays inside the code space of the current length.
    fn decode(&mut self, code: &Code) -> Result<u32, InflateError> {
        let (mut len, mut first, mut index) = (0u32, 0u32, 0u32);
        let mut word = 0u32;
        loop {
            word |= self.bits(1)?;
            let count = code.count[(len + 1) as usize];
            if (word - first) < count {
                return code
                    .symbol
                    .get((index + (word - first)) as usize)
                    .copied()
                    .ok_or(InflateError::Corrupt);
            }
            first += count;
            first <<= 1;
            word <<= 1;
            index += count;
            len += 1;
            if len > 15 {
                return Err(InflateError::Corrupt);
            }
        }
    }

    fn stored(&mut self) -> Result<(), InflateError> {
        // Discard the remainder of the current byte, then LEN/NLEN.
        self.bitbuf = 0;
        self.left = 0;
        let len = self.bits(16)? as usize;
        let nlen = self.bits(16)? as usize;
        if len ^ nlen != 0xFFFF {
            return Err(InflateError::Corrupt);
        }
        if self.pos + len > self.data.len() {
            return Err(InflateError::UnexpectedEof);
        }
        self.out.extend_from_slice(&self.data[self.pos..self.pos + len]);
        self.pos += len;
        Ok(())
    }

    fn dynamic(&mut self) -> Result<(Code, Code), InflateError> {
        let nlen = self.bits(5)? as usize + 257;
        let ndist = self.bits(5)? as usize + 1;
        let ncode = self.bits(4)? as usize + 4;
        if nlen > 286 || ndist > 30 {
            return Err(InflateError::Corrupt);
        }
        const ORDER: [usize; 19] =
            [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15];
        let mut clens = [0u8; 19];
        for i in 0..ncode {
            clens[ORDER[i]] = self.bits(3)? as u8;
        }
        let code = Code::from_lengths(&clens)?;
        let mut lengths = vec![0u8; nlen + ndist];
        let mut i = 0usize;
        while i < nlen + ndist {
            let sym = self.decode(&code)?;
            if sym < 16 {
                lengths[i] = sym as u8;
                i += 1;
            } else {
                let (rep_bits, base) = match sym {
                    16 => (2, 3),
                    17 => (3, 3),
                    18 => (7, 11),
                    _ => return Err(InflateError::Corrupt),
                };
                let rep = self.bits(rep_bits)? as usize + base;
                if i + rep > lengths.len() {
                    return Err(InflateError::Corrupt);
                }
                let value = if sym == 16 {
                    if i == 0 {
                        return Err(InflateError::Corrupt);
                    }
                    lengths[i - 1]
                } else {
                    0
                };
                for _ in 0..rep {
                    lengths[i] = value;
                    i += 1;
                }
            }
        }
        // Reject a literal tree that has no end-of-block symbol (puff.c does).
        if lengths.iter().take(nlen).all(|&x| x == 0) || lengths[256] == 0 {
            return Err(InflateError::Corrupt);
        }
        let lit = Code::from_lengths(&lengths[..nlen])?;
        // An all-zero distance tree is valid when no match ever uses it; the
        // fallback mirrors puff.c's `ret_ok`.
        let dist = Code::from_lengths(&lengths[nlen..]).unwrap_or_else(|_| Code::single_zero());
        Ok((lit, dist))
    }

    fn inflate(mut self) -> Result<Vec<u8>, InflateError> {
        loop {
            let last = self.bits(1)?;
            match self.bits(2)? {
                0 => self.stored()?,
                1 => {
                    let (lit, dist) = Code::fixed();
                    self.block(&lit, &dist)?;
                }
                2 => {
                    let (lit, dist) = self.dynamic()?;
                    self.block(&lit, &dist)?;
                }
                _ => return Err(InflateError::Corrupt),
            }
            if last == 1 {
                return Ok(self.out);
            }
        }
    }

    fn block(&mut self, lit: &Code, dist: &Code) -> Result<(), InflateError> {
        loop {
            let sym = self.decode(lit)?;
            if sym < 256 {
                self.out.push(sym as u8);
            } else if sym == 256 {
                return Ok(());
            } else {
                let idx = sym - 257;
                if idx as usize >= LENGTH.len() {
                    return Err(InflateError::Corrupt);
                }
                let (base, extra) = LENGTH[idx as usize];
                let length = base as usize + self.bits(extra)? as usize;
                let dsym = self.decode(dist)?;
                if dsym as usize >= DIST.len() {
                    return Err(InflateError::Corrupt);
                }
                let (dbase, dextra) = DIST[dsym as usize];
                let distance = dbase as usize + self.bits(dextra)? as usize;
                if distance > self.out.len() {
                    return Err(InflateError::Corrupt);
                }
                let start = self.out.len() - distance;
                for k in 0..length {
                    let b = self.out[start + k];
                    self.out.push(b);
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn pattern() -> Vec<u8> {
        b"ReaCompare deflate fixture. ".repeat(4)
    }

    #[test]
    fn stored_block_round_trips() {
        // zlib header (0x78,0x01: FCHECK-valid, CM=8), one final stored block
        // of "hello": LEN=5, NLEN=0xFFFA, then the bytes.
        let z = [0x78u8, 0x01, 0x01, 0x05, 0x00, 0xFA, 0xFF, b'h', b'e', b'l', b'l', b'o'];
        assert_eq!(inflate_zlib(&z).unwrap(), b"hello");
    }

    #[test]
    fn inflates_a_real_dynamic_zlib_stream() {
        let got = inflate_zlib(include_bytes!("../tests/deflate_dynamic.bin")).unwrap();
        assert_eq!(got, pattern());
    }

    #[test]
    fn inflates_real_dynamic_streams_at_every_length_group() {
        // CPython `zlib.compress(level 6/8/9)` fixtures. `rep28`/`rep100`
        // contain a match of length 28 and 283 — symbols whose extra-bit
        // groups (3-bit then 4-bit/5-bit) are exactly where a mis-transcribed
        // LENGTH table slips, so they anchor the boundary cases that the
        // single-block probes above never reach.
        let cases: &[(&str, &[u8], usize)] = &[
            ("simple", include_bytes!("../tests/probe_simple.bin"), 59),
            ("rep28", include_bytes!("../tests/probe_rep28.bin"), 112),
            ("rep100", include_bytes!("../tests/probe_rep100.bin"), 2800),
            ("rep28_l8", include_bytes!("../tests/probe_rep28_l8.bin"), 112),
            ("rep28_l9", include_bytes!("../tests/probe_rep28_l9.bin"), 112),
        ];
        for (name, data, want_len) in cases {
            let v = inflate_zlib(data).unwrap_or_else(|e| panic!("{name}: {e}"));
            assert_eq!(v.len(), *want_len, "{name} length");
        }
    }

    #[test]
    fn inflates_a_real_stored_zlib_stream() {
        // CPython's zlib.compress(pattern, 0) — stored blocks only.
        let got = inflate_zlib(include_bytes!("../tests/deflate_stored.bin")).unwrap();
        assert_eq!(got, pattern());
    }

    #[test]
    fn bad_fc_header_is_corrupt() {
        assert_eq!(inflate_zlib(&[0x00, 0x00, 0x00]).unwrap_err(), InflateError::Corrupt);
    }
}
