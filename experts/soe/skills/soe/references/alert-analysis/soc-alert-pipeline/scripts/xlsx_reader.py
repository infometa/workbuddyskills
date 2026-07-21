"""通用 xlsx 读取器 - 绕过 openpyxl 的 dimension bug

问题背景:
  openpyxl.load_workbook() 读取 SOC 导出 xlsx 时, dimensions 显示 "A1",
  但实际有 10000+ 行数据, openpyxl 只会读 1 行.

解决方案:
  直接解压 xlsx (本质是 zip), 读 xl/worksheets/sheet1.xml + xl/sharedStrings.xml

返回格式:
  (header: list[str], rows: list[dict])
  - header: 列名 (按列字母顺序)
  - rows: 每行一个 dict, 缺失列填空字符串

使用:
  from xlsx_reader import read_xlsx
  header, rows = read_xlsx("esSearch_xxx.xlsx")
"""
from __future__ import annotations
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _col_letter_to_idx(letter: str) -> int:
    """A -> 1, B -> 2, ..., AA -> 27"""
    n = 0
    for ch in letter:
        n = n * 26 + (ord(ch.upper()) - 64)
    return n


def _read_shared_strings(z: zipfile.ZipFile) -> list[str]:
    """读 sharedStrings.xml, 返回字符串列表"""
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    with z.open("xl/sharedStrings.xml") as f:
        root = ET.parse(f).getroot()
    strings = []
    for si in root.findall("s:si", NS):
        # 兼容富文本: si 下可能有多个 t 节点
        parts = []
        for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"):
            if t.text:
                parts.append(t.text)
        strings.append("".join(parts) if parts else "")
    return strings


def _read_sheet(z: zipfile.ZipFile, sheet_name: str = "sheet1.xml") -> tuple[list[str], list[dict]]:
    """读 sheet xml, 返回 (header, rows)

    实现细节:
      - 列字母排序: 用 _col_letter_to_idx 数值排序, 而非字母序 (避免 AB < A 的问题)
      - 单元格类型 t="s" 是 sharedStrings 的 index, "str" 是内联字符串
      - 单元格类型 t="inlineStr" (is 节点) 直接读 t.text
    """
    path = f"xl/worksheets/{sheet_name}"
    if path not in z.namelist():
        # 备选: 试一下 worksheets 目录下其他 sheet
        for name in z.namelist():
            if name.startswith("xl/worksheets/") and name.endswith(".xml"):
                path = name
                break
        else:
            return [], []

    with z.open(path) as f:
        root = ET.parse(f).getroot()

    header: list[str] = []
    col_letters: list[str] = []
    rows: list[dict] = []

    for row_el in root.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
        r_idx_str = row_el.attrib.get("r", "0")
        try:
            r_idx = int(r_idx_str)
        except ValueError:
            continue

        # 收集本行所有 cell, 按列字母分组
        cells: dict[str, str] = {}
        for c in row_el.findall("s:c", NS):
            ref = c.attrib.get("r", "")
            col = "".join(ch for ch in ref if ch.isalpha())
            if not col:
                continue
            cell_type = c.attrib.get("t", "n")
            v = c.find("s:v", NS)
            is_node = c.find("s:is", NS)

            val = ""
            if v is not None and v.text is not None:
                val = v.text
                if cell_type == "s":
                    # sharedStrings index, 在外层解引用
                    cells[col] = f"__SHAREDSTR_{val}__"
                else:
                    cells[col] = val
            elif is_node is not None:
                t = is_node.find("s:t", NS)
                cells[col] = t.text if t is not None and t.text else ""

        if r_idx == 1:
            # 表头行
            col_letters = sorted(cells.keys(), key=_col_letter_to_idx)
            header = [cells.get(c, "") for c in col_letters]
        else:
            # 数据行
            row_dict = {header[i]: cells.get(col_letters[i], "") for i in range(len(header))}
            rows.append(row_dict)

    return header, rows


def read_xlsx(path: str | Path, sheet_name: str = "sheet1.xml") -> tuple[list[str], list[dict]]:
    """读取 xlsx, 自动处理 sharedStrings 解引用

    Args:
        path: xlsx 文件路径
        sheet_name: sheet 文件名 (默认 sheet1.xml)

    Returns:
        (header, rows) - header 是列名列表, rows 是 dict 列表
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"xlsx 文件不存在: {p}")

    with zipfile.ZipFile(p) as z:
        shared_strings = _read_shared_strings(z)
        header, rows = _read_sheet(z, sheet_name)

    # 解引用 sharedStrings
    def resolve(val):
        if isinstance(val, str) and val.startswith("__SHAREDSTR_") and val.endswith("__"):
            try:
                idx = int(val[len("__SHAREDSTR_"):-2])
                return shared_strings[idx] if 0 <= idx < len(shared_strings) else ""
            except ValueError:
                return val
        return val

    header = [resolve(h) for h in header]
    for row in rows:
        resolved = {resolve(k): resolve(v) for k, v in row.items()}
        row.clear()
        row.update(resolved)

    return header, rows


# ==================== 独立测试入口 ====================

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: xlsx_reader.py <xlsx_path> [--max-rows N]")
        sys.exit(1)

    p = Path(sys.argv[1])
    max_rows = 5
    if "--max-rows" in sys.argv:
        idx = sys.argv.index("--max-rows")
        max_rows = int(sys.argv[idx + 1])

    header, rows = read_xlsx(p)
    print(f"FILE: {p.name}")
    print(f"COLUMNS ({len(header)}): {header}")
    print(f"ROWS: {len(rows)} (showing first {max_rows})")
    print("=" * 80)
    for i, row in enumerate(rows[:max_rows]):
        print(f"--- R{i+1} ---")
        for k, v in row.items():
            disp = v if len(v) <= 100 else v[:50] + "..." + v[-30:]
            print(f"  {k:25s}: {disp}")
        print()
