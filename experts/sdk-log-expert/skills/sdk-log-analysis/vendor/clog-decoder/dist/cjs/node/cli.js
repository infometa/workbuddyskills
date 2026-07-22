#!/usr/bin/env node
"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/node/cli.ts
var cli_exports = {};
__export(cli_exports, {
  main: () => main
});
module.exports = __toCommonJS(cli_exports);
var import_fs2 = __toESM(require("fs"));
var import_path2 = __toESM(require("path"));

// src/node/index.ts
var import_fs = __toESM(require("fs"));
var import_path = __toESM(require("path"));

// ../../node_modules/.pnpm/fflate@0.8.3/node_modules/fflate/esm/index.mjs
var import_module = require("module");
var require2 = (0, import_module.createRequire)("/");
var _a;
var Worker;
var isMarkedAsUntransferable;
try {
  _a = require2("worker_threads"), Worker = _a.Worker, isMarkedAsUntransferable = _a.isMarkedAsUntransferable;
} catch (e) {
}
var u8 = Uint8Array;
var u16 = Uint16Array;
var i32 = Int32Array;
var fleb = new u8([
  0,
  0,
  0,
  0,
  0,
  0,
  0,
  0,
  1,
  1,
  1,
  1,
  2,
  2,
  2,
  2,
  3,
  3,
  3,
  3,
  4,
  4,
  4,
  4,
  5,
  5,
  5,
  5,
  0,
  /* unused */
  0,
  0,
  /* impossible */
  0
]);
var fdeb = new u8([
  0,
  0,
  0,
  0,
  1,
  1,
  2,
  2,
  3,
  3,
  4,
  4,
  5,
  5,
  6,
  6,
  7,
  7,
  8,
  8,
  9,
  9,
  10,
  10,
  11,
  11,
  12,
  12,
  13,
  13,
  /* unused */
  0,
  0
]);
var clim = new u8([16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15]);
var freb = function(eb, start) {
  var b = new u16(31);
  for (var i = 0; i < 31; ++i) {
    b[i] = start += 1 << eb[i - 1];
  }
  var r = new i32(b[30]);
  for (var i = 1; i < 30; ++i) {
    for (var j = b[i]; j < b[i + 1]; ++j) {
      r[j] = j - b[i] << 5 | i;
    }
  }
  return { b, r };
};
var _a = freb(fleb, 2);
var fl = _a.b;
var revfl = _a.r;
fl[28] = 258, revfl[258] = 28;
var _b = freb(fdeb, 0);
var fd = _b.b;
var revfd = _b.r;
var rev = new u16(32768);
for (i = 0; i < 32768; ++i) {
  x = (i & 43690) >> 1 | (i & 21845) << 1;
  x = (x & 52428) >> 2 | (x & 13107) << 2;
  x = (x & 61680) >> 4 | (x & 3855) << 4;
  rev[i] = ((x & 65280) >> 8 | (x & 255) << 8) >> 1;
}
var x;
var i;
var hMap = function(cd, mb, r) {
  var s = cd.length;
  var i = 0;
  var l = new u16(mb);
  for (; i < s; ++i) {
    if (cd[i])
      ++l[cd[i] - 1];
  }
  var le = new u16(mb);
  for (i = 1; i < mb; ++i) {
    le[i] = le[i - 1] + l[i - 1] << 1;
  }
  var co;
  if (r) {
    co = new u16(1 << mb);
    var rvb = 15 - mb;
    for (i = 0; i < s; ++i) {
      if (cd[i]) {
        var sv = i << 4 | cd[i];
        var r_1 = mb - cd[i];
        var v = le[cd[i] - 1]++ << r_1;
        for (var m = v | (1 << r_1) - 1; v <= m; ++v) {
          co[rev[v] >> rvb] = sv;
        }
      }
    }
  } else {
    co = new u16(s);
    for (i = 0; i < s; ++i) {
      if (cd[i]) {
        co[i] = rev[le[cd[i] - 1]++] >> 15 - cd[i];
      }
    }
  }
  return co;
};
var flt = new u8(288);
for (i = 0; i < 144; ++i)
  flt[i] = 8;
var i;
for (i = 144; i < 256; ++i)
  flt[i] = 9;
var i;
for (i = 256; i < 280; ++i)
  flt[i] = 7;
var i;
for (i = 280; i < 288; ++i)
  flt[i] = 8;
var i;
var fdt = new u8(32);
for (i = 0; i < 32; ++i)
  fdt[i] = 5;
var i;
var flrm = /* @__PURE__ */ hMap(flt, 9, 1);
var fdrm = /* @__PURE__ */ hMap(fdt, 5, 1);
var max = function(a) {
  var m = a[0];
  for (var i = 1; i < a.length; ++i) {
    if (a[i] > m)
      m = a[i];
  }
  return m;
};
var bits = function(d, p, m) {
  var o = p / 8 | 0;
  return (d[o] | d[o + 1] << 8) >> (p & 7) & m;
};
var bits16 = function(d, p) {
  var o = p / 8 | 0;
  return (d[o] | d[o + 1] << 8 | d[o + 2] << 16) >> (p & 7);
};
var shft = function(p) {
  return (p + 7) / 8 | 0;
};
var slc = function(v, s, e) {
  if (s == null || s < 0)
    s = 0;
  if (e == null || e > v.length)
    e = v.length;
  return new u8(v.subarray(s, e));
};
var ec = [
  "unexpected EOF",
  "invalid block type",
  "invalid length/literal",
  "invalid distance",
  "stream finished",
  "no stream handler",
  ,
  // determined by compression function
  "no callback",
  "invalid UTF-8 data",
  "extra field too long",
  "date not in range 1980-2099",
  "filename too long",
  "stream finishing",
  "invalid zip data"
  // determined by unknown compression method
];
var err = function(ind, msg, nt) {
  var e = new Error(msg || ec[ind]);
  e.code = ind;
  if (Error.captureStackTrace)
    Error.captureStackTrace(e, err);
  if (!nt)
    throw e;
  return e;
};
var inflt = function(dat, st, buf, dict) {
  var sl = dat.length, dl = dict ? dict.length : 0;
  if (!sl || st.f && !st.l)
    return buf || new u8(0);
  var noBuf = !buf;
  var resize = noBuf || st.i != 2;
  var noSt = st.i;
  if (noBuf)
    buf = new u8(sl * 3);
  var cbuf = function(l2) {
    var bl = buf.length;
    if (l2 > bl) {
      var nbuf = new u8(Math.max(bl * 2, l2));
      nbuf.set(buf);
      buf = nbuf;
    }
  };
  var final = st.f || 0, pos = st.p || 0, bt = st.b || 0, lm = st.l, dm = st.d, lbt = st.m, dbt = st.n;
  var tbts = sl * 8;
  do {
    if (!lm) {
      final = bits(dat, pos, 1);
      var type = bits(dat, pos + 1, 3);
      pos += 3;
      if (!type) {
        var s = shft(pos) + 4, l = dat[s - 4] | dat[s - 3] << 8, t = s + l;
        if (t > sl) {
          if (noSt)
            err(0);
          break;
        }
        if (resize)
          cbuf(bt + l);
        buf.set(dat.subarray(s, t), bt);
        st.b = bt += l, st.p = pos = t * 8, st.f = final;
        continue;
      } else if (type == 1)
        lm = flrm, dm = fdrm, lbt = 9, dbt = 5;
      else if (type == 2) {
        var hLit = bits(dat, pos, 31) + 257, hcLen = bits(dat, pos + 10, 15) + 4;
        var tl = hLit + bits(dat, pos + 5, 31) + 1;
        pos += 14;
        var ldt = new u8(tl);
        var clt = new u8(19);
        for (var i = 0; i < hcLen; ++i) {
          clt[clim[i]] = bits(dat, pos + i * 3, 7);
        }
        pos += hcLen * 3;
        var clb = max(clt), clbmsk = (1 << clb) - 1;
        var clm = hMap(clt, clb, 1);
        for (var i = 0; i < tl; ) {
          var r = clm[bits(dat, pos, clbmsk)];
          pos += r & 15;
          var s = r >> 4;
          if (s < 16) {
            ldt[i++] = s;
          } else {
            var c = 0, n = 0;
            if (s == 16)
              n = 3 + bits(dat, pos, 3), pos += 2, c = ldt[i - 1];
            else if (s == 17)
              n = 3 + bits(dat, pos, 7), pos += 3;
            else if (s == 18)
              n = 11 + bits(dat, pos, 127), pos += 7;
            while (n--)
              ldt[i++] = c;
          }
        }
        var lt = ldt.subarray(0, hLit), dt = ldt.subarray(hLit);
        lbt = max(lt);
        dbt = max(dt);
        lm = hMap(lt, lbt, 1);
        dm = hMap(dt, dbt, 1);
      } else
        err(1);
      if (pos > tbts) {
        if (noSt)
          err(0);
        break;
      }
    }
    if (resize)
      cbuf(bt + 131072);
    var lms = (1 << lbt) - 1, dms = (1 << dbt) - 1;
    var lpos = pos;
    for (; ; lpos = pos) {
      var c = lm[bits16(dat, pos) & lms], sym = c >> 4;
      pos += c & 15;
      if (pos > tbts) {
        if (noSt)
          err(0);
        break;
      }
      if (!c)
        err(2);
      if (sym < 256)
        buf[bt++] = sym;
      else if (sym == 256) {
        lpos = pos, lm = null;
        break;
      } else {
        var add = sym - 254;
        if (sym > 264) {
          var i = sym - 257, b = fleb[i];
          add = bits(dat, pos, (1 << b) - 1) + fl[i];
          pos += b;
        }
        var d = dm[bits16(dat, pos) & dms], dsym = d >> 4;
        if (!d)
          err(3);
        pos += d & 15;
        var dt = fd[dsym];
        if (dsym > 3) {
          var b = fdeb[dsym];
          dt += bits16(dat, pos) & (1 << b) - 1, pos += b;
        }
        if (pos > tbts) {
          if (noSt)
            err(0);
          break;
        }
        if (resize)
          cbuf(bt + 131072);
        var end = bt + add;
        if (bt < dt) {
          var shift = dl - dt, dend = Math.min(dt, end);
          if (shift + bt < 0)
            err(3);
          for (; bt < dend; ++bt)
            buf[bt] = dict[shift + bt];
        }
        for (; bt < end; ++bt)
          buf[bt] = buf[bt - dt];
      }
    }
    st.l = lm, st.p = lpos, st.b = bt, st.f = final;
    if (lm)
      final = 1, st.m = lbt, st.d = dm, st.n = dbt;
  } while (!final);
  return bt != buf.length && noBuf ? slc(buf, 0, bt) : buf.subarray(0, bt);
};
var et = /* @__PURE__ */ new u8(0);
var Inflate = /* @__PURE__ */ function() {
  function Inflate2(opts, cb) {
    if (typeof opts == "function")
      cb = opts, opts = {};
    this.ondata = cb;
    var dict = opts && opts.dictionary && opts.dictionary.subarray(-32768);
    this.s = { i: 0, b: dict ? dict.length : 0 };
    this.o = new u8(32768);
    this.p = new u8(0);
    if (dict)
      this.o.set(dict);
  }
  Inflate2.prototype.e = function(c) {
    if (!this.ondata)
      err(5);
    if (this.d)
      err(4);
    if (!this.p.length)
      this.p = c;
    else if (c.length) {
      var n = new u8(this.p.length + c.length);
      n.set(this.p), n.set(c, this.p.length), this.p = n;
    }
  };
  Inflate2.prototype.c = function(final) {
    this.s.i = +(this.d = final || false);
    var bts = this.s.b;
    var dt = inflt(this.p, this.s, this.o);
    this.ondata(slc(dt, bts, this.s.b), this.d);
    this.o = slc(dt, this.s.b - 32768), this.s.b = this.o.length;
    this.p = slc(this.p, this.s.p / 8 | 0), this.s.p &= 7;
  };
  Inflate2.prototype.push = function(chunk, final) {
    this.e(chunk), this.c(final);
  };
  return Inflate2;
}();
var td = typeof TextDecoder != "undefined" && /* @__PURE__ */ new TextDecoder();
var tds = 0;
try {
  td.decode(et, { stream: true });
  tds = 1;
} catch (e) {
}

// src/adapters/fflate.ts
var fflateAdapter = {
  inflateRaw,
  inflateRawWithConsumed
};
function inflateRaw(input) {
  return inflateRawBestEffort(input);
}
function inflateRawWithConsumed(input) {
  if (input.byteLength === 0) {
    return { output: new Uint8Array(), consumedBytes: 0 };
  }
  const output = inflateRawBestEffort(input);
  if (output.byteLength === 0) {
    throw new Error("Raw inflate produced no output");
  }
  return {
    output,
    consumedBytes: findConsumedBytes(input, output)
  };
}
function inflateRawBestEffort(input) {
  const chunks = [];
  const inflator = new Inflate((chunk) => {
    chunks.push(chunk.slice());
  });
  inflator.push(input, false);
  return concatUint8Arrays(chunks);
}
function findConsumedBytes(input, expectedOutput) {
  let low = 1;
  let high = input.byteLength;
  let candidate = input.byteLength;
  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    const output = tryInflate(input.subarray(0, mid));
    if (output && output.byteLength >= expectedOutput.byteLength) {
      if (output.byteLength === expectedOutput.byteLength && uint8ArrayEquals(output, expectedOutput)) {
        candidate = mid;
      }
      high = mid - 1;
    } else {
      low = mid + 1;
    }
  }
  return candidate;
}
function tryInflate(input) {
  try {
    return inflateRawBestEffort(input);
  } catch {
    return null;
  }
}
function concatUint8Arrays(chunks) {
  const totalSize = chunks.reduce((sum, chunk) => sum + chunk.byteLength, 0);
  const output = new Uint8Array(totalSize);
  let offset = 0;
  chunks.forEach((chunk) => {
    output.set(chunk, offset);
    offset += chunk.byteLength;
  });
  return output;
}
function uint8ArrayEquals(a, b) {
  if (a.byteLength !== b.byteLength) {
    return false;
  }
  for (let i = 0; i < a.byteLength; i++) {
    if (a[i] !== b[i]) {
      return false;
    }
  }
  return true;
}

// src/adapters/node-zlib.ts
var import_node_zlib = require("node:zlib");
var nodeZlibAdapter = {
  inflateRaw: inflateRaw2,
  inflateRawWithConsumed: inflateRawWithConsumed2
};
function inflateRaw2(input) {
  return new Uint8Array((0, import_node_zlib.inflateRawSync)(input, { finishFlush: import_node_zlib.constants.Z_SYNC_FLUSH }));
}
function inflateRawWithConsumed2(input) {
  return inflateRawWithConsumedBinarySearch(input);
}
function inflateRawWithConsumedBinarySearch(input) {
  const output = inflateRaw2(input);
  if (output.byteLength === 0) {
    throw new Error("Raw inflate produced no output");
  }
  return {
    output,
    consumedBytes: findConsumedBytesWithZlib(input, output)
  };
}
function findConsumedBytesWithZlib(input, expectedOutput) {
  let low = 1;
  let high = input.byteLength;
  let candidate = input.byteLength;
  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    const output = tryInflate2(input.subarray(0, mid));
    if (output && output.byteLength >= expectedOutput.byteLength) {
      if (output.byteLength === expectedOutput.byteLength && uint8ArrayEquals2(output, expectedOutput)) {
        candidate = mid;
      }
      high = mid - 1;
    } else {
      low = mid + 1;
    }
  }
  return candidate;
}
function tryInflate2(input) {
  try {
    return inflateRaw2(input);
  } catch {
    return null;
  }
}
function uint8ArrayEquals2(a, b) {
  if (a.byteLength !== b.byteLength) {
    return false;
  }
  for (let i = 0; i < a.byteLength; i += 1) {
    if (a[i] !== b[i]) {
      return false;
    }
  }
  return true;
}

// src/core/bytes.ts
function concatUint8Arrays2(chunks) {
  const totalSize = chunks.reduce((sum, chunk) => sum + chunk.byteLength, 0);
  const output = new Uint8Array(totalSize);
  let offset = 0;
  chunks.forEach((chunk) => {
    output.set(chunk, offset);
    offset += chunk.byteLength;
  });
  return output;
}
function readUint16LE(buffer, offset) {
  ensureReadable(buffer, offset, 2);
  return buffer[offset] | buffer[offset + 1] << 8;
}
function readUint32LE(buffer, offset) {
  ensureReadable(buffer, offset, 4);
  return (buffer[offset] | buffer[offset + 1] << 8 | buffer[offset + 2] << 16 | buffer[offset + 3] << 24) >>> 0;
}
function getExtension(fileName) {
  const baseName = fileName.split(/[\\/]/).pop() || "";
  const dotIndex = baseName.lastIndexOf(".");
  if (dotIndex < 0 || dotIndex === baseName.length - 1) {
    return "";
  }
  return baseName.slice(dotIndex + 1).toLowerCase();
}
function ensureReadable(buffer, offset, size) {
  if (offset < 0 || offset + size > buffer.byteLength) {
    throw new RangeError(`Cannot read ${size} bytes at offset ${offset}`);
  }
}

// src/core/types.ts
var DecodeLogError = class extends Error {
  constructor(message, fileName) {
    super(fileName ? `${fileName}: ${message}` : message);
    this.fileName = fileName;
    this.name = "DecodeLogError";
  }
};

// src/core/clog.ts
function decodeClog(input, adapter = fflateAdapter) {
  const chunks = [];
  let offset = 0;
  offset = skipZeroPadding(input, offset);
  if (offset >= input.byteLength) {
    return new Uint8Array();
  }
  while (offset < input.byteLength) {
    offset = skipZeroPadding(input, offset);
    if (offset >= input.byteLength) {
      break;
    }
    const remaining = input.subarray(offset);
    try {
      const result = adapter.inflateRawWithConsumed(remaining);
      if (result.output.byteLength > 0) {
        chunks.push(result.output);
      }
      if (result.consumedBytes === 0) {
        break;
      }
      offset += result.consumedBytes;
    } catch (err2) {
      if (offset + 1 < input.byteLength) {
        offset += 1;
        continue;
      }
      if (chunks.length > 0) {
        break;
      }
      throw new DecodeLogError(err2?.message || "Failed to decode clog");
    }
  }
  return concatUint8Arrays2(chunks);
}
function skipZeroPadding(input, offset) {
  let current = offset;
  while (current < input.byteLength && input[current] === 0) {
    current += 1;
  }
  return current;
}

// src/core/detect.ts
function detectBufferType(buffer, maxBytes = 256, percentBin = 0.1) {
  if (percentBin < 0) {
    return "unknown" /* Unknown */;
  }
  const length = Math.min(buffer.byteLength, maxBytes);
  if (length === 0) {
    return "text" /* Text */;
  }
  let textCount = 0;
  for (let i = 0; i < length; i += 1) {
    const byte = buffer[i];
    if (byte >= 32 && byte <= 127 || byte === 10 || byte === 13 || byte === 9) {
      textCount += 1;
    }
  }
  const binaryRatio = (length - textCount) / length;
  return binaryRatio >= percentBin ? "binary" /* Binary */ : "text" /* Text */;
}

// src/core/xlog.ts
var MAGIC_NO_COMPRESS_START = 3;
var MAGIC_COMPRESS_START = 4;
var MAGIC_COMPRESS_START_1 = 5;
var MAGIC_END = 0;
var HEADER_LENGTH = 1 + 2 + 1 + 1 + 4 + 4;
var MAGIC_BYTES = /* @__PURE__ */ new Set([
  MAGIC_NO_COMPRESS_START,
  MAGIC_COMPRESS_START,
  MAGIC_COMPRESS_START_1
]);
function decodeXlog(input, adapter = fflateAdapter) {
  if (detectBufferType(input, 256, 0.1) === "text" /* Text */) {
    return input;
  }
  const startPos = findLogStartPos(input, 0, 2);
  if (startPos < 0) {
    throw new DecodeLogError("Unable to locate xlog start position");
  }
  const state = { lastSeq: 0 };
  const chunks = [];
  let offset = startPos;
  while (offset >= 0 && offset < input.byteLength) {
    const nextOffset = decodeFrame(input, offset, state, chunks, adapter);
    if (nextOffset < 0) {
      break;
    }
    offset = nextOffset;
  }
  return concatUint8Arrays2(chunks);
}
function decodeFrame(input, initialOffset, state, chunks, adapter) {
  let offset = initialOffset;
  if (!isGoodLogBuffer(input, offset, 1)) {
    const fixPos = findLogStartPos(input, offset, 1);
    if (fixPos < 0) {
      return -1;
    }
    chunks.push(encodeText(`[F]TRTCDecodeLog::decodeBuffer decode error len=${fixPos - offset}
`));
    offset = fixPos;
  }
  if (offset + HEADER_LENGTH > input.byteLength || !MAGIC_BYTES.has(input[offset])) {
    return -1;
  }
  const magicByte = input[offset];
  const length = readUint32LE(input, offset + HEADER_LENGTH - 4 - 4);
  const seq = readUint16LE(input, offset + HEADER_LENGTH - 4 - 4 - 2 - 2);
  if (seq !== 0 && seq !== 1 && state.lastSeq !== 0 && seq !== state.lastSeq + 1) {
    chunks.push(encodeText(`[F]TRTCDecodeLog::decodeBuffer log seq:${state.lastSeq + 1}-${seq - 1} is missing
`));
  }
  if (seq !== 0) {
    state.lastSeq = seq;
  }
  const payloadStart = offset + HEADER_LENGTH;
  const payloadEnd = payloadStart + length;
  const payload = input.subarray(payloadStart, payloadEnd);
  const output = decodePayload(magicByte, payload, adapter);
  if (output.byteLength > 0) {
    if (output.includes(0)) {
      chunks.push(encodeText(`[F]TRTCDecodeLog::decodeBuffer tmpBuffer = '' tmpBufferSize = ${output.byteLength}
`));
    } else {
      chunks.push(output);
    }
  }
  return payloadEnd + 1;
}
function decodePayload(magicByte, payload, adapter) {
  if (magicByte === MAGIC_NO_COMPRESS_START) {
    return payload;
  }
  if (magicByte === MAGIC_COMPRESS_START) {
    return adapter.inflateRaw(payload);
  }
  if (magicByte === MAGIC_COMPRESS_START_1) {
    return adapter.inflateRaw(mergeCompressedChunks(payload));
  }
  throw new DecodeLogError(`Unsupported xlog magic byte: ${magicByte}`);
}
function mergeCompressedChunks(payload) {
  const chunks = [];
  let readPos = 0;
  while (readPos < payload.byteLength) {
    if (payload.byteLength - readPos < 2) {
      throw new DecodeLogError(`Invalid xlog chunk header length: ${payload.byteLength}`);
    }
    const singleLogLen = readUint16LE(payload, readPos);
    readPos += 2;
    if (singleLogLen > payload.byteLength - readPos) {
      throw new DecodeLogError(`Invalid xlog chunk body length: ${singleLogLen}`);
    }
    chunks.push(payload.subarray(readPos, readPos + singleLogLen));
    readPos += singleLogLen;
  }
  return concatUint8Arrays2(chunks);
}
function findLogStartPos(input, startOffset, count) {
  for (let offset = startOffset; offset < input.byteLength; offset++) {
    if (MAGIC_BYTES.has(input[offset]) && isGoodLogBuffer(input, offset, count)) {
      return offset;
    }
  }
  return -1;
}
function isGoodLogBuffer(input, offset, count) {
  if (offset === input.byteLength) {
    return true;
  }
  if (offset < 0 || offset >= input.byteLength || !MAGIC_BYTES.has(input[offset])) {
    return false;
  }
  if (offset + HEADER_LENGTH + 1 > input.byteLength) {
    return false;
  }
  const length = readUint32LE(input, offset + HEADER_LENGTH - 4 - 4);
  const endOffset = offset + HEADER_LENGTH + length;
  if (endOffset + 1 > input.byteLength) {
    return false;
  }
  if (input[endOffset] !== MAGIC_END) {
    return false;
  }
  if (count <= 1) {
    return true;
  }
  return isGoodLogBuffer(input, endOffset + 1, count - 1);
}
function encodeText(text) {
  return new TextEncoder().encode(text);
}

// src/core/decode.ts
function decodeLogBuffer(input, options) {
  const { fileName, inflateAdapter = fflateAdapter } = options;
  const fileType = detectBufferType(input, 256, 0.1);
  if (fileType === "text" /* Text */) {
    return input;
  }
  const ext = getExtension(fileName);
  if (ext === "clog") {
    return decodeClog(input, inflateAdapter);
  }
  if (ext === "xlog") {
    return decodeXlog(input, inflateAdapter);
  }
  throw new DecodeLogError(`Unsupported binary log extension: ${ext || "(none)"}`, fileName);
}

// src/node/index.ts
function decodeLogToFileSync(inputPath, outputPath) {
  return decodeLogToFileWithAdapterSync(inputPath, outputPath, nodeZlibAdapter);
}
function decodeLogToFileBaselineSync(inputPath, outputPath) {
  return decodeLogToFileWithAdapterSync(inputPath, outputPath, fflateAdapter);
}
function decodeLogToFileWithAdapterSync(inputPath, outputPath, inflateAdapter) {
  if (!import_fs.default.existsSync(inputPath)) {
    throw new Error(`Input file not found: ${inputPath}`);
  }
  const input = import_fs.default.readFileSync(inputPath);
  const output = decodeLogBuffer(new Uint8Array(input), {
    fileName: import_path.default.basename(inputPath),
    inflateAdapter
  });
  import_fs.default.mkdirSync(import_path.default.dirname(outputPath), { recursive: true });
  import_fs.default.writeFileSync(outputPath, output);
  return true;
}

// src/node/cli.ts
var supportedExtensions = /* @__PURE__ */ new Set([".clog", ".xlog"]);
var supportsColor = Boolean(process.env.FORCE_COLOR || process.stdout.isTTY && !process.env.NO_COLOR);
var colors = {
  green: (s) => supportsColor ? `\x1B[32m${s}\x1B[0m` : s,
  red: (s) => supportsColor ? `\x1B[31m${s}\x1B[0m` : s,
  yellow: (s) => supportsColor ? `\x1B[33m${s}\x1B[0m` : s,
  cyan: (s) => supportsColor ? `\x1B[36m${s}\x1B[0m` : s,
  dim: (s) => supportsColor ? `\x1B[2m${s}\x1B[0m` : s
};
function printUsage() {
  console.log(`
${colors.cyan("TRTC Log Decoder JS")} - Decode clog/xlog files to readable text

${colors.yellow("Usage:")}
  clog-decoder-js [--baseline] <input> [output]
  clog-decoder-js [--baseline] <input1> <input2> ...
  clog-decoder-js [--baseline] <directory>

${colors.yellow("Arguments:")}
  input     Path to .clog or .xlog file(s), or a directory
  output    Path to output file (optional, defaults to <input>.log)

${colors.yellow("Options:")}
  --baseline  Use cross-platform fflate baseline instead of Node fast path
`);
}
function isSupportedFile(filePath) {
  return supportedExtensions.has(import_path2.default.extname(filePath).toLowerCase());
}
function getDefaultOutputPath(inputPath) {
  return import_path2.default.join(import_path2.default.dirname(inputPath), `${import_path2.default.basename(inputPath)}.log`);
}
function collectFiles(inputPath) {
  const resolved = import_path2.default.resolve(inputPath);
  if (!import_fs2.default.existsSync(resolved)) {
    console.error(colors.red(`Error: File or directory not found: ${inputPath}`));
    return [];
  }
  const stat = import_fs2.default.statSync(resolved);
  if (stat.isDirectory()) {
    const files = import_fs2.default.readdirSync(resolved).filter((fileName) => isSupportedFile(fileName)).map((fileName) => import_path2.default.join(resolved, fileName));
    if (files.length === 0) {
      console.error(colors.yellow(`Warning: No .clog/.xlog files found in directory: ${inputPath}`));
    }
    return files;
  }
  if (stat.isFile()) {
    if (!isSupportedFile(resolved)) {
      console.error(colors.yellow(`Warning: Unsupported file extension: ${import_path2.default.extname(inputPath)} (expected .clog or .xlog)`));
    }
    return [resolved];
  }
  return [];
}
function formatSize(bytes) {
  if (bytes < 1024)
    return `${bytes} B`;
  if (bytes < 1024 * 1024)
    return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
function decodeFile(inputPath, outputPath, options) {
  const inputSize = import_fs2.default.statSync(inputPath).size;
  const inputName = import_path2.default.basename(inputPath);
  const outputName = import_path2.default.basename(outputPath);
  process.stdout.write(`  Decoding ${colors.cyan(inputName)} ${colors.dim(`(${formatSize(inputSize)})`)} ... `);
  const startTime = Date.now();
  try {
    const success = options.baseline ? decodeLogToFileBaselineSync(inputPath, outputPath) : decodeLogToFileSync(inputPath, outputPath);
    const elapsed = Date.now() - startTime;
    if (success && import_fs2.default.existsSync(outputPath)) {
      const outputSize = import_fs2.default.statSync(outputPath).size;
      console.log(`${colors.green("\u2713")} \u2192 ${outputName} ${colors.dim(`(${formatSize(outputSize)}, ${elapsed}ms)`)}`);
      return true;
    }
    console.log(colors.red("\u2717 decode returned false"));
    return false;
  } catch (err2) {
    console.log(colors.red(`\u2717 ${err2?.message || String(err2)}`));
    return false;
  }
}
function main(args = process.argv.slice(2)) {
  const useBaseline = args.includes("--baseline");
  const normalizedArgs = args.filter((arg) => arg !== "--baseline");
  if (normalizedArgs.length === 0 || normalizedArgs.includes("-h") || normalizedArgs.includes("--help")) {
    printUsage();
    return normalizedArgs.length === 0 ? 1 : 0;
  }
  if (normalizedArgs.length === 2 && !import_fs2.default.existsSync(normalizedArgs[1])) {
    const inputPath = import_path2.default.resolve(normalizedArgs[0]);
    const outputPath = import_path2.default.resolve(normalizedArgs[1]);
    if (!import_fs2.default.existsSync(inputPath)) {
      console.error(colors.red(`Error: Input file not found: ${normalizedArgs[0]}`));
      return 1;
    }
    console.log(`
${colors.cyan("TRTC Log Decoder JS")}
`);
    const success = decodeFile(inputPath, outputPath, { baseline: useBaseline });
    console.log("");
    return success ? 0 : 1;
  }
  const files = normalizedArgs.flatMap(collectFiles);
  if (files.length === 0) {
    return 1;
  }
  console.log(`
${colors.cyan("TRTC Log Decoder JS")}
`);
  let successCount = 0;
  for (const filePath of files) {
    if (decodeFile(filePath, getDefaultOutputPath(filePath), { baseline: useBaseline })) {
      successCount += 1;
    }
  }
  console.log(`
${colors.green(`${successCount}`)}/${files.length} file(s) decoded successfully
`);
  return successCount === files.length ? 0 : 1;
}
if (require.main === module) {
  process.exit(main());
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  main
});
//# sourceMappingURL=cli.js.map
