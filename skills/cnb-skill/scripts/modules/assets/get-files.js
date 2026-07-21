"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = _default;
var _core = _interopRequireDefault(require("../../core/core.js"));
function _interopRequireDefault(e) { return e && e.__esModule ? e : { default: e }; }
// @ts-nocheck
/* tslint:disable */
/* eslint-disable */
/*
 * -------------------------------------------------------------------------
 * ## THIS FILE WAS GENERATED VIA CNB-API-GENERATE                        ##
 * ##                                                                     ##
 * ## AUTHOR: bapelin                                                     ##
 * ## SOURCE: https://cnb.woa.com/cnb/frontend-science/cnb-api-generate   ##
 * -------------------------------------------------------------------------
 * @Version 2.2.5
 * @Source /{repo}/-/files/{filePath}
 */

/**
 * @description getFiles request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetFilesRes Success Response Type
 */

/**
 * @description GetFilesError Error Response Type
 */

/**
* @description 注意：后续版本该接口可能将被移出 Assets 分类
* 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-contents:r
* @tags Assets,Pulls,Issues
* @name getFiles
* @summary 获取 issue 文件或合并请求文件的请求，返回文件二进制内容。Request to retrieve file of issues and pull requests, returns binary content.
* @request get:/{repo}/-/files/{filePath}

----------------------------------
* @param {GetFilesParams} arg0 - getFiles request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  filePath
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/files/${filePath}`,
    _apiTag: "/{repo}/-/files/{filePath}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/files/{filePath}",
      path: {
        repo,
        filePath
      }
    }
  });
}