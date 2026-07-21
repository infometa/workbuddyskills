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
 * @Source /{repo}/-/git/contents/{file_path}
 */

/**
 * @description getContent request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetContentRes Success Response Type
 */

/**
 * @description GetContentError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Git
* @name getContent
* @summary 查询仓库文件列表或文件。List repository files or file.
* @request get:/{repo}/-/git/contents/{file_path}

----------------------------------
* @param {GetContentParams} arg0 - getContent request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  file_path,
  ...query
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/contents/${file_path}`,
    _apiTag: "/{repo}/-/git/contents/{file_path}",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/git/contents/{file_path}",
      path: {
        repo,
        file_path
      },
      query: query
    }
  });
}