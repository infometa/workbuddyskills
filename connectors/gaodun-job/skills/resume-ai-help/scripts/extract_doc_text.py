# -*- coding: utf-8 -*-
"""Extract plain text from legacy Word .doc (Word 97-2003) binary files.
Pure-python: parses the OLE compound document + FIB + CLX piece table.
"""
import struct
import sys
import olefile


def read_cp_map(fc, lcb, stream):
    """Parse CLX: sequence of Prc (0x02) chunks and a Pcdt (0x01) chunk."""
    if lcb <= 0:
        return None
    clx = stream[fc: fc + lcb]
    pos = 0
    pcdt = None
    while pos < len(clx):
        t = clx[pos]
        if t == 0x02:  # Prc
            cb = struct.unpack('<H', clx[pos+1:pos+3])[0]
            pos += 3 + cb
        elif t == 0x01:  # Pcdt
            lcbPcdt = struct.unpack('<I', clx[pos+1:pos+5])[0]
            plcfpcd = clx[pos+5: pos+5+lcbPcdt]
            pcdt = plcfpcd
            pos += 5 + lcbPcdt
        else:
            break
    if pcdt is None:
        return None
    # PlcPcd: n+1 CPs then n PCDs (8 bytes each)
    n = (len(pcdt) - 4) // 12
    if n <= 0:
        return None
    cps = struct.unpack('<%dI' % (n + 1), pcdt[:4*(n+1)])
    pcds = pcdt[4*(n+1):]
    pieces = []
    for i in range(n):
        pcd = pcds[i*8:(i+1)*8]
        fcCompressed = struct.unpack('<I', pcd[2:6])[0]
        isCompressed = bool(fcCompressed & 0x40000000)
        fc = fcCompressed & 0x3FFFFFFF
        pieces.append({
            'cpStart': cps[i],
            'cpEnd': cps[i+1],
            'fc': fc,
            'compressed': isCompressed,
        })
    return pieces


def extract_text(path):
    ole = olefile.OleFileIO(path)
    if not ole.exists('WordDocument'):
        raise RuntimeError('not a Word document (no WordDocument stream)')
    wd = ole.openstream('WordDocument').read()

    fcMin = struct.unpack('<I', wd[0x18:0x1C])[0]
    fcMac = struct.unpack('<I', wd[0x1C:0x20])[0]

    # FIB: fcClx / lcbClx at 0x01A2 / 0x01A6
    fcClx = struct.unpack('<I', wd[0x1A2:0x1A6])[0]
    lcbClx = struct.unpack('<I', wd[0x1A6:0x1AA])[0]

    pieces = read_cp_map(fcClx, lcbClx, wd)
    out = []

    if pieces:
        for p in pieces:
            start = p['fc']
            length = (p['cpEnd'] - p['cpStart']) * (1 if p['compressed'] else 2)
            raw = wd[start: start + length]
            if p['compressed']:
                # 8-bit per char: try utf-8 first, then gbk, then latin-1
                for enc in ('utf-8', 'gbk', 'latin-1'):
                    try:
                        out.append(raw.decode(enc))
                        break
                    except Exception:
                        continue
                else:
                    out.append(raw.decode('latin-1', 'replace'))
            else:
                try:
                    out.append(raw.decode('utf-16-le', 'replace'))
                except Exception:
                    out.append('')
    else:
        # fallback: no piece table -> text from fcMin..fcMac
        raw = wd[fcMin:fcMac]
        try:
            out.append(raw.decode('cp936'))
        except Exception:
            out.append(raw.decode('utf-16-le', 'replace'))

    ole.close()
    text = ''.join(out)
    return text


if __name__ == '__main__':
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else None
    txt = extract_text(src)
    # normalize whitespace
    lines = [ln.rstrip() for ln in txt.split('\r')]
    txt = '\n'.join(lines)
    if dst:
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(txt)
        print('OK:%s chars=%d' % (dst, len(txt)))
    else:
        print(txt)
