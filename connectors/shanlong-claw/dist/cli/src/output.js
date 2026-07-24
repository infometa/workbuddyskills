"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.extractPayload = extractPayload;
exports.formatOutput = formatOutput;
function asRecord(value) {
    return value && typeof value === 'object' && !Array.isArray(value)
        ? value
        : null;
}
function stripInternalFields(record) {
    const { _httpStatus, ...rest } = record;
    return rest;
}
function extractPayload(data) {
    const record = asRecord(data);
    if (!record) {
        return data;
    }
    const cleaned = stripInternalFields(record);
    if (cleaned.code === '0' || cleaned.code === '200' || cleaned.code === 0 || cleaned.code === 200) {
        return cleaned.data !== undefined ? cleaned.data : cleaned;
    }
    return cleaned;
}
function normalizeFilter(raw) {
    if (!raw) {
        return [];
    }
    if (Array.isArray(raw)) {
        return raw.filter((item) => typeof item === 'string' && item.trim()).map((item) => item.trim());
    }
    if (raw.enabled === false) {
        return [];
    }
    const fields = raw.fields || raw.include || raw.paths || [];
    return fields.filter((item) => typeof item === 'string' && item.trim()).map((item) => item.trim());
}
function readOutputFilter(cmd) {
    if (!cmd) {
        return [];
    }
    const configured = normalizeFilter(cmd.output_filter);
    if (configured.length > 0) {
        return configured;
    }
    const responseFilter = normalizeFilter(cmd.response_filter);
    if (responseFilter.length > 0) {
        return responseFilter;
    }
    return [];
}
function readOutputTransform(cmd) {
    const transform = cmd?.output_transform;
    if (transform &&
        typeof transform.source_path === 'string' &&
        transform.source_path.trim() &&
        typeof transform.output_key === 'string' &&
        transform.output_key.trim()) {
        return transform;
    }
    return undefined;
}
function isFailurePayload(rawData) {
    const record = asRecord(rawData);
    if (!record) {
        return false;
    }
    if (record.success === false) {
        return true;
    }
    const code = record.code;
    if (code === undefined || code === null) {
        return false;
    }
    return code !== '0' && code !== '200' && code !== 0 && code !== 200;
}
function readPathSegment(segment) {
    const trimmed = segment.trim();
    if (trimmed.endsWith('[]')) {
        return { key: trimmed.slice(0, -2), array: true };
    }
    return { key: trimmed, array: false };
}
function collectByPath(value, path) {
    const segments = path.split('.').filter(Boolean).map(readPathSegment);
    const visit = (current, index) => {
        if (index >= segments.length) {
            return Array.isArray(current) ? current : [current];
        }
        const segment = segments[index];
        const record = asRecord(current);
        if (!record || !(segment.key in record)) {
            return [];
        }
        const next = record[segment.key];
        if (segment.array) {
            if (!Array.isArray(next)) {
                return [];
            }
            return next.flatMap((item) => visit(item, index + 1));
        }
        return visit(next, index + 1);
    };
    return visit(value, 0);
}
function applyOutputTransform(data, transform) {
    if (!transform) {
        return data;
    }
    const rows = collectByPath(data, transform.source_path);
    const output = {
        [transform.output_key]: rows,
    };
    if (transform.count_key) {
        output[transform.count_key] = rows.length;
    }
    if (transform.include_page_info !== false) {
        const pageInfoPath = transform.page_info_path || 'pageInfo';
        const pageInfo = getByPath(data, pageInfoPath);
        if (pageInfo !== undefined) {
            output.pageInfo = pageInfo;
        }
    }
    return output;
}
function getByPath(value, path) {
    const parts = path.split('.').filter(Boolean);
    let current = value;
    for (const part of parts) {
        const record = asRecord(current);
        if (!record || !(part in record)) {
            return undefined;
        }
        current = record[part];
    }
    return current;
}
function setByPath(target, path, value) {
    const parts = path.split('.').filter(Boolean);
    if (parts.length === 0) {
        return;
    }
    let current = target;
    for (const part of parts.slice(0, -1)) {
        const next = current[part];
        if (!asRecord(next)) {
            current[part] = {};
        }
        current = current[part];
    }
    current[parts[parts.length - 1]] = value;
}
function pickFields(value, fields) {
    const record = asRecord(value);
    if (!record) {
        return value;
    }
    const picked = {};
    for (const field of fields) {
        const parts = field.split('.').filter(Boolean);
        if (parts.length > 1) {
            const [first, ...restParts] = parts;
            const nested = record[first];
            if (Array.isArray(nested)) {
                const rest = restParts.join('.');
                const prev = Array.isArray(picked[first]) ? picked[first] : [];
                picked[first] = nested.map((item, index) => ({
                    ...(asRecord(prev[index]) || {}),
                    ...(asRecord(pickFields(item, [rest])) || {}),
                }));
                continue;
            }
        }
        let selected = getByPath(record, field);
        let outputPath = field;
        if (selected === undefined && field.startsWith('data.')) {
            outputPath = field.slice('data.'.length);
            selected = getByPath(record, outputPath);
        }
        if (selected !== undefined) {
            setByPath(picked, outputPath, selected);
        }
    }
    return picked;
}
function applyOutputFilter(data, fields) {
    if (fields.length === 0) {
        return data;
    }
    if (Array.isArray(data)) {
        return data.map((item) => pickFields(item, fields));
    }
    const record = asRecord(data);
    if (!record) {
        return data;
    }
    if (Array.isArray(record.rows)) {
        return { ...record, rows: record.rows.map((item) => pickFields(item, fields)) };
    }
    if (Array.isArray(record.list)) {
        return { ...record, list: record.list.map((item) => pickFields(item, fields)) };
    }
    if (Array.isArray(record.data)) {
        return { ...record, data: record.data.map((item) => pickFields(item, fields)) };
    }
    if (Array.isArray(record.billList)) {
        return { ...record, billList: record.billList.map((item) => pickFields(item, fields)) };
    }
    if (Array.isArray(record.itemList)) {
        return { ...record, itemList: record.itemList.map((item) => pickFields(item, fields)) };
    }
    if (Array.isArray(record.areaList)) {
        return { ...record, areaList: record.areaList.map((item) => pickFields(item, fields)) };
    }
    if (Array.isArray(record.pointList)) {
        return { ...record, pointList: record.pointList.map((item) => pickFields(item, fields)) };
    }
    if (Array.isArray(record.settleList)) {
        return { ...record, settleList: record.settleList.map((item) => pickFields(item, fields)) };
    }
    if (Array.isArray(record.discountList)) {
        return { ...record, discountList: record.discountList.map((item) => pickFields(item, fields)) };
    }
    if (Array.isArray(record.fulloffList)) {
        return { ...record, fulloffList: record.fulloffList.map((item) => pickFields(item, fields)) };
    }
    if (Array.isArray(record.promoteList)) {
        return { ...record, promoteList: record.promoteList.map((item) => pickFields(item, fields)) };
    }
    if (Array.isArray(record.itemMethodList)) {
        return { ...record, itemMethodList: record.itemMethodList.map((item) => pickFields(item, fields)) };
    }
    if (Array.isArray(record.itemIncomeList)) {
        return { ...record, itemIncomeList: record.itemIncomeList.map((item) => pickFields(item, fields)) };
    }
    if (Array.isArray(record.ticketDataList)) {
        return { ...record, ticketDataList: record.ticketDataList.map((item) => pickFields(item, fields)) };
    }
    if ((Array.isArray(record.item_qty_summary) || Array.isArray(record.item_qty_summary_by_name)) &&
        !Array.isArray(record.itemList)) {
        const next = { ...record };
        if (Array.isArray(record.item_qty_summary)) {
            next.item_qty_summary = record.item_qty_summary.map((item) => pickFields(item, fields));
        }
        if (Array.isArray(record.item_qty_summary_by_name)) {
            next.item_qty_summary_by_name = record.item_qty_summary_by_name.map((item) => pickFields(item, fields));
        }
        return next;
    }
    return pickFields(record, fields);
}
function formatOutput(rawData, format, cmd) {
    const payload = extractPayload(rawData);
    const failed = isFailurePayload(rawData);
    const transformed = failed ? payload : applyOutputTransform(payload, readOutputTransform(cmd));
    const outputFilter = readOutputFilter(cmd);
    const data = outputFilter.length > 0 && !failed ? applyOutputFilter(transformed, outputFilter) : transformed;
    if (format === 'json') {
        console.log(JSON.stringify(data, null, 2));
        return;
    }
    if (format === 'csv') {
        const record = asRecord(data);
        const rows = Array.isArray(data)
            ? data
            : Array.isArray(record?.rows)
                ? record.rows
                : Array.isArray(record?.list)
                    ? record.list
                    : Array.isArray(record?.itemList)
                        ? record.itemList
                        : Array.isArray(record?.areaList)
                            ? record.areaList
                            : Array.isArray(record?.pointList)
                                ? record.pointList
                                : Array.isArray(record?.settleList)
                                    ? record.settleList
                                    : Array.isArray(record?.discountList)
                                        ? record.discountList
                                        : Array.isArray(record?.fulloffList)
                                            ? record.fulloffList
                                            : Array.isArray(record?.promoteList)
                                                ? record.promoteList
                                                : Array.isArray(record?.itemMethodList)
                                                    ? record.itemMethodList
                                                    : Array.isArray(record?.itemIncomeList)
                                                        ? record.itemIncomeList
                                                        : Array.isArray(record?.ticketDataList)
                                                            ? record.ticketDataList
                                                            : Array.isArray(record?.item_qty_summary_by_name)
                                                                ? record.item_qty_summary_by_name
                                                                : Array.isArray(record?.item_qty_summary)
                                                                    ? record.item_qty_summary
                                                                    : null;
        if (rows && rows.length > 0 && typeof rows[0] === 'object' && rows[0] !== null) {
            const first = rows[0];
            console.log(Object.keys(first).join(','));
            rows.forEach((row) => {
                const item = row;
                console.log(Object.values(item).join(','));
            });
            return;
        }
        console.log(JSON.stringify(data));
        return;
    }
    if (Array.isArray(data)) {
        if (data.length === 0) {
            console.log('(空结果)');
            return;
        }
        console.table(data.slice(0, 50));
        if (data.length > 50) {
            console.log(`... 共 ${data.length} 条，仅显示前50条`);
        }
        return;
    }
    const record = asRecord(data);
    if (Array.isArray(record?.rows)) {
        formatOutput({ code: '0', data: record.rows }, format);
        return;
    }
    if (Array.isArray(record?.list)) {
        formatOutput({ code: '0', data: record.list }, format);
        return;
    }
    if (Array.isArray(record?.itemList)) {
        formatOutput({ code: '0', data: record.itemList }, format);
        return;
    }
    if (Array.isArray(record?.settleList)) {
        formatOutput({ code: '0', data: record.settleList }, format);
        return;
    }
    if (Array.isArray(record?.discountList)) {
        formatOutput({ code: '0', data: record.discountList }, format);
        return;
    }
    if (Array.isArray(record?.fulloffList)) {
        formatOutput({ code: '0', data: record.fulloffList }, format);
        return;
    }
    if (Array.isArray(record?.promoteList)) {
        formatOutput({ code: '0', data: record.promoteList }, format);
        return;
    }
    if (Array.isArray(record?.itemMethodList)) {
        formatOutput({ code: '0', data: record.itemMethodList }, format);
        return;
    }
    if (Array.isArray(record?.itemIncomeList)) {
        formatOutput({ code: '0', data: record.itemIncomeList }, format);
        return;
    }
    if (Array.isArray(record?.ticketDataList)) {
        formatOutput({ code: '0', data: record.ticketDataList }, format);
        return;
    }
    if (Array.isArray(record?.item_qty_summary_by_name)) {
        formatOutput({ code: '0', data: record.item_qty_summary_by_name }, format);
        return;
    }
    if (Array.isArray(record?.item_qty_summary)) {
        formatOutput({ code: '0', data: record.item_qty_summary }, format);
        return;
    }
    if (record && Array.isArray(record.data)) {
        formatOutput({ code: '0', data: record.data }, format);
        return;
    }
    if (record) {
        console.log(JSON.stringify(record, null, 2));
        return;
    }
    console.log(data);
}
