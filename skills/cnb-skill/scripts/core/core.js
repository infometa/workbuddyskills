"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;
var _fs = _interopRequireDefault(require("fs"));
var _path = _interopRequireDefault(require("path"));
var _os = _interopRequireDefault(require("os"));
var _fetchResponseHandler = require("./fetch-response-handler");
var _generateUniqueId = require("./utils/generate-unique-id");
function _interopRequireDefault(e) { return e && e.__esModule ? e : { default: e }; }
async function formatResponse(data, response) {
  const responseData = {
    status: response.status,
    trace: response.headers.get('traceparent'),
    header: {
      'x-cnb-page': response.headers.get('x-cnb-page'),
      'x-cnb-page-size': response.headers.get('x-cnb-page-size'),
      'x-cnb-total': response.headers.get('x-cnb-total')
    },
    data: null
  };
  const contentType = response.headers.get('content-type') || '';
  const isJson = ['application/vnd.cnb.api+json', 'application/json', 'text/json'].some(t => contentType.includes(t));
  const isText = contentType.startsWith('text/') || contentType.includes('xml');
  const isImage = contentType.startsWith('image/');
  try {
    if (isJson) {
      responseData.data = await response.json();
    } else if (isText) {
      responseData.data = await response.text();
    } else if (isImage) {
      const arrayBuffer = await response.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);

      // 确定文件扩展名
      let extension = '.bin';
      if (contentType.includes('png')) extension = '.png';else if (contentType.includes('jpeg') || contentType.includes('jpg')) extension = '.jpg';else if (contentType.includes('gif')) extension = '.gif';else if (contentType.includes('webp')) extension = '.webp';else if (contentType.includes('svg')) extension = '.svg';
      // 可以根据需要添加更多类型

      // 构建本地保存路径
      // 注意：请确保 './downloads' 目录存在，或者使用 fs.mkdirSync 创建它
      const tempDir = _os.default.tmpdir();
      const uploadDir = _path.default.join(tempDir, 'cnb-skill');
      if (!_fs.default.existsSync(uploadDir)) {
        _fs.default.mkdirSync(uploadDir, {
          recursive: true
        });
      }
      const fileName = `${(0, _generateUniqueId.generateUniqueId)()}${extension}`;
      const filePath = _path.default.join(uploadDir, fileName);
      _fs.default.writeFileSync(filePath, buffer);
      responseData.data = filePath;
    } else {
      // 其他二进制数据保持原有的 Base64 逻辑，或者也可以按需保存
      const arrayBuffer = await response.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      const base64String = buffer.toString('base64');
      responseData.data = {
        type: 'base64',
        data: base64String,
        mimeType: contentType || 'application/octet-stream'
      };
    }
  } catch (err) {
    responseData.data = err?.message || 'Unknown Error';
  }
  if (responseData.status >= 200 && responseData.status < 300) {
    return await (0, _fetchResponseHandler.fetchResponseHandler)(data._originParams, responseData);
  }
  return responseData;
}
async function clientFetch(data) {
  const domain = process.env.CNB_API_ENDPOINT || 'https://api.cnb.cool';
  const url = `${domain}${data.url}`;
  const urlParse = new URL(url);
  if (data.params) {
    // eslint-disable-next-line no-restricted-syntax
    for (const key in data.params) {
      urlParse.searchParams.append(key, data.params[key]);
    }
  }
  const response = await fetch(urlParse.href, {
    method: data.method.toUpperCase(),
    body: data.data ? JSON.stringify(data.data) : undefined,
    headers: {
      Authorization: `Bearer ${process.env.CNB_TOKEN}`,
      Accept: 'application/vnd.cnb.api+json',
      ...(data?.header || {})
    }
  });
  return await formatResponse(data, response);
}
var _default = exports.default = {
  request: clientFetch
};