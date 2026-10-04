import { sha256 } from '../lib/kernel-utils.mjs';
import zlib from 'node:zlib';

const crcTable = (() => {
  const table = new Uint32Array(256);
  for (let index = 0; index < 256; index += 1) {
    let value = index;
    for (let bit = 0; bit < 8; bit += 1) value = (value & 1) ? (0xedb88320 ^ (value >>> 1)) : (value >>> 1);
    table[index] = value >>> 0;
  }
  return table;
})();
const crc32 = (bytes) => {
  let crc = 0xffffffff;
  for (const byte of bytes) crc = crcTable[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
};
const findSignature = (bytes, signature, from = bytes.length - 4) => {
  for (let index = from; index >= 0; index -= 1) if (bytes.readUInt32LE(index) === signature) return index;
  return -1;
};
const safeZipPath = (value) => typeof value === 'string' && value.length > 0 && !value.includes('\\') && !value.startsWith('/') && !/^[A-Za-z]:/u.test(value) && value.split('/').every((segment) => segment && segment !== '.' && segment !== '..');

function xmlWellFormed(text, expectedRoot) {
  if (typeof text !== 'string' || text.includes('\u0000') || text.includes('\uFFFD') || /<!DOCTYPE|<!ENTITY/iu.test(text)) return false;
  const stack = [];
  let root = null;
  const tokens = text.match(/<[^>]+>/gu) ?? [];
  for (const token of tokens) {
    if (/^<\?xml|^<!--|^<\?[^>]+\?>$/u.test(token)) continue;
    if (/^<\//u.test(token)) {
      const name = /^<\/\s*([^\s>]+)/u.exec(token)?.[1];
      if (!name || stack.pop() !== name) return false;
    } else if (!/^<!/u.test(token)) {
      const name = /^<\s*([^\s/>]+)/u.exec(token)?.[1];
      if (!name) return false;
      if (!root) root = name;
      if (!/\/\s*>$/u.test(token)) stack.push(name);
    }
  }
  return stack.length === 0 && root === expectedRoot;
}

export function inspectDocx(bytes, expected = {}) {
  const issues = [];
  if (!Buffer.isBuffer(bytes) || bytes.length < 64) return { ok: false, status: 'not_openable', issues: ['docx_too_short'], metrics: {} };
  if (expected.byteLength !== undefined && expected.byteLength !== bytes.length) issues.push('artifact_byte_length_mismatch');
  if (expected.sha256 && expected.sha256 !== sha256(bytes)) issues.push('artifact_hash_mismatch');
  const endOffset = findSignature(bytes, 0x06054b50);
  if (endOffset < 0 || endOffset + 22 > bytes.length) return { ok: false, status: 'not_openable', issues: [...issues, 'docx_eocd_missing'], metrics: {} };
  const entryCount = bytes.readUInt16LE(endOffset + 10);
  const centralSize = bytes.readUInt32LE(endOffset + 12);
  const centralOffset = bytes.readUInt32LE(endOffset + 16);
  if (centralOffset + centralSize > endOffset) issues.push('docx_central_directory_invalid');
  const entries = new Map();
  let cursor = centralOffset;
  for (let index = 0; index < entryCount; index += 1) {
    if (cursor + 46 > bytes.length || bytes.readUInt32LE(cursor) !== 0x02014b50) { issues.push('docx_central_entry_invalid'); break; }
    const flags = bytes.readUInt16LE(cursor + 8);
    const method = bytes.readUInt16LE(cursor + 10);
    const crc = bytes.readUInt32LE(cursor + 16);
    const compressedSize = bytes.readUInt32LE(cursor + 20);
    const uncompressedSize = bytes.readUInt32LE(cursor + 24);
    const nameLength = bytes.readUInt16LE(cursor + 28);
    const extraLength = bytes.readUInt16LE(cursor + 30);
    const commentLength = bytes.readUInt16LE(cursor + 32);
    const localOffset = bytes.readUInt32LE(cursor + 42);
    const name = bytes.subarray(cursor + 46, cursor + 46 + nameLength).toString('utf8');
    if (!safeZipPath(name)) issues.push(`docx_unsafe_path:${name}`);
    if ((flags & 0x1) !== 0) issues.push(`docx_encrypted_entry_forbidden:${name}`);
    if (![0, 8].includes(method)) issues.push(`docx_unsupported_compression:${name}`);
    if (entries.has(name)) issues.push(`docx_duplicate_entry:${name}`);
    if (localOffset + 30 > bytes.length || bytes.readUInt32LE(localOffset) !== 0x04034b50) issues.push(`docx_local_entry_invalid:${name}`);
    else {
      const localFlags = bytes.readUInt16LE(localOffset + 6);
      const localMethod = bytes.readUInt16LE(localOffset + 8);
      const localNameLength = bytes.readUInt16LE(localOffset + 26);
      const localExtraLength = bytes.readUInt16LE(localOffset + 28);
      const localName = bytes.subarray(localOffset + 30, localOffset + 30 + localNameLength).toString('utf8');
      const dataStart = localOffset + 30 + localNameLength + localExtraLength;
      const compressed = bytes.subarray(dataStart, dataStart + compressedSize);
      let data = null;
      if (localName !== name || localMethod !== method || localFlags !== flags) issues.push(`docx_local_central_mismatch:${name}`);
      if (compressed.length !== compressedSize) issues.push(`docx_entry_size_invalid:${name}`);
      else {
        try { data = method === 8 ? zlib.inflateRawSync(compressed) : compressed; }
        catch { issues.push(`docx_entry_inflate_failed:${name}`); }
      }
      if (data && (data.length !== uncompressedSize || crc32(data) !== crc)) issues.push(`docx_entry_crc_invalid:${name}`);
      if (data) entries.set(name, data);
    }
    cursor += 46 + nameLength + extraLength + commentLength;
  }
  for (const required of ['[Content_Types].xml', '_rels/.rels', 'word/document.xml']) if (!entries.has(required)) issues.push(`docx_required_entry_missing:${required}`);
  const relationships = entries.get('_rels/.rels')?.toString('utf8') ?? '';
  const document = entries.get('word/document.xml')?.toString('utf8') ?? '';
  const contentTypes = entries.get('[Content_Types].xml')?.toString('utf8') ?? '';
  if (!xmlWellFormed(contentTypes, 'Types') || !/PartName=["']\/word\/document\.xml["']/u.test(contentTypes)) issues.push('docx_content_types_invalid');
  if (!xmlWellFormed(relationships, 'Relationships')) issues.push('docx_relationships_xml_invalid');
  if (!xmlWellFormed(document, 'w:document')) issues.push('docx_document_xml_invalid');
  const relationshipTargets = [...relationships.matchAll(/\bTarget\s*=\s*["']([^"']+)["']/giu)].map((match) => match[1]);
  if (/TargetMode\s*=\s*["']External["']/iu.test(relationships) || relationshipTargets.some((target) => /^(?:https?:|file:|\\\\)/iu.test(target))) issues.push('docx_external_relationship_forbidden');
  if (!document.includes('<w:body') || !/<w:t(?:\s[^>]*)?>[^<]+<\/w:t>/u.test(document)) issues.push('docx_document_content_missing');
  return { ok: issues.length === 0, status: issues.length ? 'not_openable' : 'openable', issues, metrics: { entryCount: entries.size, textNodeCount: (document.match(/<w:t(?:\s[^>]*)?>/gu) ?? []).length, byteLength: bytes.length, sha256: sha256(bytes) } };
}

export function inspectPdf(bytes, expected = {}) {
  const issues = [];
  if (!Buffer.isBuffer(bytes) || bytes.length < 64) return { ok: false, status: 'not_openable', issues: ['pdf_too_short'], metrics: {} };
  if (expected.byteLength !== undefined && expected.byteLength !== bytes.length) issues.push('artifact_byte_length_mismatch');
  if (expected.sha256 && expected.sha256 !== sha256(bytes)) issues.push('artifact_hash_mismatch');
  const text = bytes.toString('binary');
  if (!text.startsWith('%PDF-')) issues.push('pdf_header_missing');
  if (!/%%EOF\s*$/u.test(text)) issues.push('pdf_eof_missing');
  const startMatch = /startxref\s+([0-9]+)\s+%%EOF/u.exec(text);
  if (!startMatch) issues.push('pdf_startxref_missing');
  else {
    const xrefOffset = Number(startMatch[1]);
    if (!Number.isInteger(xrefOffset) || bytes.subarray(xrefOffset, xrefOffset + 4).toString('ascii') !== 'xref') issues.push('pdf_xref_invalid');
    else {
      const xrefText = text.slice(xrefOffset);
      const header = /^xref\s+([0-9]+)\s+([0-9]+)\s+/u.exec(xrefText);
      if (!header) issues.push('pdf_xref_header_invalid');
      else {
        const firstObject = Number(header[1]);
        const count = Number(header[2]);
        const linesStart = header[0].length;
        const trailerIndex = xrefText.indexOf('trailer', linesStart);
        const lines = trailerIndex < 0 ? [] : xrefText.slice(linesStart, trailerIndex).trim().split(/\r?\n/u).filter(Boolean);
        if (firstObject !== 0 || lines.length !== count) issues.push('pdf_xref_entry_count_invalid');
        const objects = new Map();
        lines.forEach((line, index) => {
          const match = /^(\d{10})\s+(\d{5})\s+([nf])\s*$/u.exec(line);
          if (!match) { issues.push(`pdf_xref_entry_invalid:${index}`); return; }
          if (match[3] !== 'n') return;
          const objectNumber = firstObject + index;
          const offset = Number(match[1]);
          const generation = Number(match[2]);
          const prefix = `${objectNumber} ${generation} obj`;
          if (text.slice(offset, offset + prefix.length) !== prefix) { issues.push(`pdf_object_offset_invalid:${objectNumber}`); return; }
          const end = text.indexOf('endobj', offset + prefix.length);
          if (end < 0) { issues.push(`pdf_object_unterminated:${objectNumber}`); return; }
          objects.set(objectNumber, text.slice(offset + prefix.length, end));
        });
        const trailer = trailerIndex < 0 ? '' : xrefText.slice(trailerIndex, xrefText.indexOf('startxref', trailerIndex));
        const size = /\/Size\s+(\d+)/u.exec(trailer);
        const root = /\/Root\s+(\d+)\s+0\s+R/u.exec(trailer);
        if (!size || Number(size[1]) !== count || !root || !objects.has(Number(root[1]))) issues.push('pdf_trailer_invalid');
        const catalog = root ? objects.get(Number(root[1])) ?? '' : '';
        const pagesRef = /\/Type\s+\/Catalog\b[\s\S]*?\/Pages\s+(\d+)\s+0\s+R/u.exec(catalog);
        const pages = pagesRef ? objects.get(Number(pagesRef[1])) ?? '' : '';
        const kids = /\/Kids\s*\[([^\]]*)\]/u.exec(pages);
        const declaredPageCount = /\/Count\s+(\d+)/u.exec(pages);
        const pageRefs = kids ? [...kids[1].matchAll(/(\d+)\s+0\s+R/gu)].map((match) => Number(match[1])) : [];
        if (!pagesRef || !/\/Type\s+\/Pages\b/u.test(pages) || !declaredPageCount || Number(declaredPageCount[1]) !== pageRefs.length || pageRefs.length < 1) issues.push('pdf_page_tree_invalid');
        for (const pageRef of pageRefs) {
          const page = objects.get(pageRef) ?? '';
          const contentsRef = /\/Type\s+\/Page\b[\s\S]*?\/Contents\s+(\d+)\s+0\s+R/u.exec(page);
          if (!contentsRef || !objects.has(Number(contentsRef[1]))) { issues.push(`pdf_page_contents_invalid:${pageRef}`); continue; }
          const streamObject = objects.get(Number(contentsRef[1]));
          const lengthMatch = /\/Length\s+(\d+)/u.exec(streamObject);
          const streamMatch = /stream\r?\n([\s\S]*?)endstream/u.exec(streamObject);
          if (!lengthMatch || !streamMatch || Buffer.from(streamMatch[1], 'binary').length !== Number(lengthMatch[1])) issues.push(`pdf_stream_length_invalid:${contentsRef[1]}`);
        }
      }
    }
  }
  const pageCount = (text.match(/\/Type \/Page\b/gu) ?? []).length;
  if (pageCount < 1) issues.push('pdf_page_missing');
  const streams = [...text.matchAll(/stream\r?\n([\s\S]*?)endstream/gu)].map((match) => match[1]);
  if (streams.length === 0 || !streams.some((stream) => /<FEFF[0-9A-F]+>\s*Tj/u.test(stream))) issues.push('pdf_text_content_missing');
  if (!text.includes('/Subtype /Type0') || !text.includes('/Encoding /UniGB-UCS2-H')) issues.push('pdf_unicode_font_mapping_missing');
  return { ok: issues.length === 0, status: issues.length ? 'not_openable' : 'openable', issues, metrics: { pageCount, streamCount: streams.length, byteLength: bytes.length, sha256: sha256(bytes) } };
}

export function inspectBinaryArtifact(format, bytes, expected = {}) {
  if (format === 'docx') return inspectDocx(bytes, expected);
  if (format === 'pdf') return inspectPdf(bytes, expected);
  return { ok: false, status: 'not_evaluable', issues: ['unsupported_binary_format'], metrics: {} };
}
