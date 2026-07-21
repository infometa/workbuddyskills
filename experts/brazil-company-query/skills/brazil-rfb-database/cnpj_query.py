"""
CNPJ Query Tool — Binary search on COS via HTTP Range
No SCF, no server, zero setup — auto-installs dependencies.
"""
import struct
import json
import sys
import subprocess
import importlib

# Auto-install requests if missing (zero user action required)
def _ensure_requests():
    try:
        importlib.import_module('requests')
    except ImportError:
        print('requests not found. Auto-installing...', file=sys.stderr)
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests', '-q'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print('Done.', file=sys.stderr)

_ensure_requests()
import requests

# COS bucket: maintained by expert author, data sourced from RFB (Receita Federal) public datasets.
# 数据更新时间：跟随 RFB 发布节奏，约每月一次（当前：2026-06）。
# 若 COS 不可达，请回退到 WebSearch 在线查询，或使用 RFB 官方源按需下载。
COS = "https://brazil-businessdevelopment-1448789884.cos.ap-shanghai.myqcloud.com/brazil-cnpj"


def hr(url, start, end):
    """Fetch bytes [start, end] via HTTP Range."""
    r = requests.get(url, headers={"Range": f"bytes={start}-{end}"}, timeout=15)
    if r.status_code in (206, 200):
        return r.content
    raise Exception(f"HTTP {r.status_code}")


def binary_search(idx_url, key, key_w, data_url, data_range=500):
    """Binary search sorted index, return one matching data line."""
    r = requests.head(idx_url, timeout=10)
    fs = int(r.headers.get("Content-Length", 0))
    rs = key_w + 8
    lo, hi = 0, fs // rs - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        d = hr(idx_url, mid * rs, min((mid + 1) * rs - 1, fs - 1))
        k = d[:key_w].decode("ascii").strip()
        off = struct.unpack(">Q", d[key_w:key_w + 8])[0]
        if k < key:
            lo = mid + 1
        elif k > key:
            hi = mid - 1
        else:
            line = hr(data_url, off, off + data_range).split(b"\n")[0].decode("utf-8")
            return line
    return None


def find_all_matching(idx_url, key, key_w, data_url):
    """Find all data records matching key (used for socios)."""
    r = requests.head(idx_url, timeout=10)
    fs = int(r.headers.get("Content-Length", 0))
    rs = key_w + 8
    n = fs // rs
    if n == 0:
        return []

    lo, hi = 0, n - 1
    match_idx = None
    while lo <= hi:
        mid = (lo + hi) // 2
        d = hr(idx_url, mid * rs, min((mid + 1) * rs - 1, fs - 1))
        k = d[:key_w].decode("ascii").strip()
        if k < key:
            lo = mid + 1
        elif k > key:
            hi = mid - 1
        else:
            match_idx = mid
            break

    if match_idx is None:
        return []

    first = match_idx
    while first > 0:
        d = hr(idx_url, (first - 1) * rs, first * rs - 1)
        if d[:key_w].decode("ascii").strip() != key:
            break
        first -= 1

    last = match_idx
    while last < n - 1:
        d = hr(idx_url, (last + 1) * rs, (last + 2) * rs - 1)
        if d[:key_w].decode("ascii").strip() != key:
            break
        last += 1

    d_first = hr(idx_url, first * rs, (first + 1) * rs - 1)
    start_off = struct.unpack(">Q", d_first[key_w:key_w + 8])[0]

    if last == first:
        data = hr(data_url, start_off, start_off + 500)
        return [data.split(b"\n")[0].decode("utf-8")]

    d_last = hr(idx_url, last * rs, (last + 1) * rs - 1)
    end_off = struct.unpack(">Q", d_last[key_w:key_w + 8])[0]

    data = hr(data_url, start_off, end_off + 500)
    return [ln.decode("utf-8") for ln in data.split(b"\n") if ln]


def query(cnpj):
    """Query a CNPJ and return structured result."""
    cnpj = cnpj.strip().replace(".", "").replace("/", "").replace("-", "")
    if len(cnpj) != 14 or not cnpj.isdigit():
        return {"error": "Invalid CNPJ - must be 14 digits"}

    # Estabelecimento
    line = binary_search(f"{COS}/estab.idx", cnpj, 14, f"{COS}/estab.txt", 500)
    if not line:
        return {"error": "CNPJ not found", "cnpj": cnpj}

    f = line.split("|")
    result = {
        "cnpj": f[0] if len(f) > 0 else "",
        "cnpj_base": f[1] if len(f) > 1 else "",
        "nome_fantasia": f[2] if len(f) > 2 else "",
        "uf": f[3] if len(f) > 3 else "",
        "situacao": f[4] if len(f) > 4 else "",
        "cnae": f[5] if len(f) > 5 else "",
        "municipio": f[6] if len(f) > 6 else "",
        "email": f[7] if len(f) > 7 else "",
        "data_inicio": f[8] if len(f) > 8 else "",
    }

    base = result["cnpj_base"]

    # Empresa
    eline = binary_search(f"{COS}/empresa.idx", base, 8, f"{COS}/empresa.txt", 200)
    if eline:
        ef = eline.split("|")
        result.update({
            "razao_social": ef[1] if len(ef) > 1 else "",
            "natureza_juridica": ef[2] if len(ef) > 2 else "",
            "capital_social": ef[3] if len(ef) > 3 else "",
            "porte": ef[4] if len(ef) > 4 else "",
        })

    # Socios
    socios_lines = find_all_matching(f"{COS}/socio.idx", base, 8, f"{COS}/socio.txt")
    result["socios"] = [
        {"nome": sf[1], "qualificacao": sf[2]}
        for s in socios_lines
        for sf in [s.split("|")]
        if len(sf) > 2
    ]

    # Simples
    si = binary_search(f"{COS}/simples.idx", base, 8, f"{COS}/simples.txt", 100)
    if si:
        sif = si.split("|")
        result["opcao_simples"] = sif[1] if len(sif) > 1 else ""
        result["opcao_mei"] = sif[2] if len(sif) > 2 else ""

    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cnpj = sys.argv[1]
    else:
        cnpj = input("CNPJ: ").strip()

    print(json.dumps(query(cnpj), indent=2, ensure_ascii=False))
