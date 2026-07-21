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
 * @Source /{repo}/-/git/raw/{ref_with_path}
 */

/**
 * @description getRaw request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetRawRes Success Response Type
 */

/**
 * @description GetRawError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Git
* @name getRaw
* @summary 获得仓库指定文件内容
* @request get:/{repo}/-/git/raw/{ref_with_path}

----------------------------------
* @param {GetRawParams} arg0 - getRaw request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  ref_with_path,
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
    url: `/${repo}/-/git/raw/${ref_with_path}`,
    _apiTag: "/{repo}/-/git/raw/{ref_with_path}",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/git/raw/{ref_with_path}",
      path: {
        repo,
        ref_with_path
      },
      query: query
    }
  });
}