/**
 * CRC64-ECMA182 implementation for Tencent SVP/COS
 * Polynomial: 0x142F0E1EBA9EA3693
 * Standard: ECMA-182
 * Output: Unsigned 64-bit integer as decimal string
 */

// ECMA-182 polynomial (reversed for LSB-first processing)
const POLY = 0xC96C5795D7870F42n; // Bit-reversed 0x142F0E1EBA9EA3693
const XOR_OUT = 0xFFFFFFFFFFFFFFFFn;

// Pre-computed lookup table for ECMA-182
let crcTable = null;

function reverseBits64(n) {
  let result = 0n;
  for (let i = 0; i < 64; i++) {
    result = (result << 1n) | ((n >> BigInt(i)) & 1n);
  }
  return result;
}

function initTable() {
  if (crcTable) return crcTable;
  
  crcTable = new BigUint64Array(256);
  for (let i = 0; i < 256; i++) {
    let crc = BigInt(i);
    for (let j = 0; j < 8; j++) {
      if (crc & 1n) {
        crc = (crc >> 1n) ^ POLY;
      } else {
        crc = crc >> 1n;
      }
    }
    crcTable[i] = crc;
  }
  return crcTable;
}

/**
 * Calculate CRC64-ECMA182
 * @param {Buffer|Uint8Array} buffer - Input data
 * @returns {string} CRC64 value as unsigned 64-bit decimal string
 */
export function crc64(buffer) {
  const table = initTable();
  let crc = XOR_OUT; // Initial value
  
  for (let i = 0; i < buffer.length; i++) {
    const byte = BigInt(buffer[i]);
    const idx = Number((crc ^ byte) & 0xFFn);
    crc = table[idx] ^ (crc >> 8n);
  }
  
  // Final XOR
  crc = crc ^ XOR_OUT;
  
  // Return as unsigned 64-bit decimal string
  return crc.toString(10);
}

// Test with known value: "123456789" should be "11051210869376104954"
if (import.meta.url === `file://${process.argv[1]}`) {
  const testBuf = Buffer.from("123456789");
  const result = crc64(testBuf);
  console.log("Test '123456789':", result);
  console.log("Expected:        ", "11051210869376104954");
  console.log("Match:", result === "11051210869376104954");
}
