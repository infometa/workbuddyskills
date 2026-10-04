#!/usr/bin/env python3
"""Export validated PROPDB report or curve-image datasets to CSV or XLSX."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable, Optional
from xml.sax.saxutils import escape, quoteattr

from render_curve_image import CurveImageDataError, validate_curve_image_data
from render_report import ReportDataError, validate_report_data


FIXED_TIMESTAMP = (2026, 8, 19, 0, 0, 0)


def dataset_name(section: dict[str, Any], index: int) -> str:
    return section.get("heading") or ({"table": "结果数据", "line-chart": "曲线数据"}.get(section["kind"], "数据")) + f" {index}"


def header(label: str, unit: str = "") -> str:
    return f"{label} ({unit})" if unit else label


def extract_datasets(data: dict[str, Any]) -> list[dict[str, Any]]:
    datasets = []
    if "panels" in data:
        for index, panel in enumerate(data["panels"], start=1):
            datasets.append({
                "name": panel["title"] or f"曲线数据 {index}",
                "headers": [header(panel["xLabel"], panel["xUnit"])] + [header(series["name"], panel["yUnit"]) for series in panel["series"]],
                "rows": [
                    [x_value] + [series["values"][point_index] for series in panel["series"]]
                    for point_index, x_value in enumerate(panel["xValues"])
                ],
            })
        return datasets
    for index, section in enumerate(data["sections"], start=1):
        if section["kind"] == "table":
            columns = section["columns"]
            datasets.append({
                "name": dataset_name(section, index),
                "headers": [header(column["label"], column.get("unit", "")) for column in columns],
                "rows": [[row.get(column["key"]) for column in columns] for row in section["rows"]],
            })
        elif section["kind"] == "line-chart":
            datasets.append({
                "name": dataset_name(section, index),
                "headers": [header(section["xLabel"], section["xUnit"])] + [header(series["name"], section["yUnit"]) for series in section["series"]],
                "rows": [
                    [x_value] + [series["values"][point_index] for series in section["series"]]
                    for point_index, x_value in enumerate(section["xValues"])
                ],
            })
    if not datasets:
        raise ReportDataError("报告没有可导出的表格或曲线数据")
    return datasets


def csv_text(dataset: dict[str, Any]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(dataset["headers"])
    for row in dataset["rows"]:
        writer.writerow(["" if value is None else value for value in row])
    return "\ufeff" + buffer.getvalue()


def column_name(index: int) -> str:
    value = index + 1
    result = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        result = chr(65 + remainder) + result
    return result


def cell_xml(reference: str, value: Any, *, header_cell: bool = False) -> str:
    style = ' s="1"' if header_cell else ""
    if value is None:
        return f'<c r="{reference}"{style}/>'
    if isinstance(value, bool):
        text = "TRUE" if value else "FALSE"
        return f'<c r="{reference}" t="inlineStr"{style}><is><t>{text}</t></is></c>'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and not math.isfinite(value):
            raise ReportDataError("导出数据不能包含 NaN 或无穷值")
        return f'<c r="{reference}"{style}><v>{value}</v></c>'
    text = escape(str(value))
    preserve = ' xml:space="preserve"' if text[:1].isspace() or text[-1:].isspace() else ""
    return f'<c r="{reference}" t="inlineStr"{style}><is><t{preserve}>{text}</t></is></c>'


def worksheet_xml(headers: list[str], rows: list[list[Any]]) -> str:
    all_rows = [headers] + rows
    row_xml = []
    for row_index, row in enumerate(all_rows, start=1):
        cells = [cell_xml(f"{column_name(column_index)}{row_index}", value, header_cell=row_index == 1) for column_index, value in enumerate(row)]
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    last_cell = f"{column_name(len(headers) - 1)}{len(all_rows)}"
    widths = "".join(f'<col min="{index}" max="{index}" width="18" customWidth="1"/>' for index in range(1, len(headers) + 1))
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:{last_cell}"/><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        f'<cols>{widths}</cols><sheetData>{"".join(row_xml)}</sheetData><autoFilter ref="A1:{column_name(len(headers) - 1)}{len(all_rows)}"/>'
        '</worksheet>'
    )


def safe_sheet_name(name: str, used: set[str]) -> str:
    base = re.sub(r"[\\/*?:\[\]]", "_", name).strip(" '")[:31] or "数据"
    candidate = base
    number = 2
    while candidate.casefold() in used:
        suffix = f"_{number}"
        candidate = base[:31 - len(suffix)] + suffix
        number += 1
    used.add(candidate.casefold())
    return candidate


def zip_write(archive: zipfile.ZipFile, name: str, content: str) -> None:
    info = zipfile.ZipInfo(name, FIXED_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o644 << 16
    archive.writestr(info, content.encode("utf-8"))


def xlsx_bytes(data: dict[str, Any], datasets: list[dict[str, Any]]) -> bytes:
    report = data.get("report") or data["image"]
    metadata = {
        "name": "报告信息",
        "headers": ["项目", "内容"],
        "rows": [
            ["报告标题", report["title"]], ["分析对象", report["objectLabel"]],
            ["分析范围", report["scopeLabel"]], ["生成时间", report["generatedAt"]],
            ["单位集", report.get("unitSet", "SI")], ["数据完整性", "完整" if report["dataStatus"] == "complete" else "部分"],
        ],
    }
    sheets = [metadata] + datasets
    used: set[str] = set()
    names = [safe_sheet_name(sheet["name"], used) for sheet in sheets]
    workbook_sheets = "".join(f'<sheet name={quoteattr(name)} sheetId="{index}" r:id="rId{index}"/>' for index, name in enumerate(names, start=1))
    relationships = "".join(
        f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        for index in range(1, len(sheets) + 1)
    )
    relationships += f'<Relationship Id="rId{len(sheets) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    overrides = "".join(f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for index in range(1, len(sheets) + 1))
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        f'{overrides}</Types>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets>{workbook_sheets}</sheets></workbook>'
    )
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2"><font><sz val="11"/><name val="Arial"/></font><font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Arial"/></font></fonts>'
        '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF356AE6"/><bgColor indexed="64"/></patternFill></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFill="1" applyFont="1"/></cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        zip_write(archive, "[Content_Types].xml", content_types)
        zip_write(archive, "_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        zip_write(archive, "xl/workbook.xml", workbook)
        zip_write(archive, "xl/_rels/workbook.xml.rels", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{relationships}</Relationships>')
        zip_write(archive, "xl/styles.xml", styles)
        for index, sheet in enumerate(sheets, start=1):
            zip_write(archive, f"xl/worksheets/sheet{index}.xml", worksheet_xml(sheet["headers"], sheet["rows"]))
    return buffer.getvalue()


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export PROPDB report data to CSV or XLSX")
    parser.add_argument("--input", default="-", help="UTF-8 report-data JSON file, or - for stdin")
    parser.add_argument("--output", required=True, type=Path, help="Output .csv or .xlsx file")
    parser.add_argument("--dataset", type=int, help="1-based dataset index for CSV when multiple datasets exist")
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    try:
        ensure_suffix = args.output.suffix.casefold()
        if ensure_suffix not in {".csv", ".xlsx"}:
            raise ReportDataError("--output 必须使用 .csv 或 .xlsx 扩展名")
        if args.output.exists():
            raise ReportDataError("输出文件已存在；请使用新的文件名")
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        payload = json.loads(raw)
        if payload.get("templateVersion") == "propdb-curve-image-v1.0":
            data = validate_curve_image_data(payload)
        else:
            data = validate_report_data(payload)
        datasets = extract_datasets(data)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if ensure_suffix == ".csv":
            if args.dataset is None and len(datasets) != 1:
                raise ReportDataError("报告包含多个数据集；导出 CSV 时必须用 --dataset 指定 1-based 数据集序号")
            selected = 1 if args.dataset is None else args.dataset
            if not 1 <= selected <= len(datasets):
                raise ReportDataError(f"--dataset 必须在 1–{len(datasets)} 之间")
            args.output.write_text(csv_text(datasets[selected - 1]), encoding="utf-8", newline="")
        else:
            args.output.write_bytes(xlsx_bytes(data, datasets))
        print(f"Exported: {args.output}")
        return 0
    except (OSError, json.JSONDecodeError, ReportDataError, CurveImageDataError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
