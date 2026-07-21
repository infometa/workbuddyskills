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
 * @Source /{repo}/-/git/archive/{ref_with_path}
 */

/**
 * @description getArchive request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetArchiveRes Success Response Type
 */

/**
 * @description GetArchiveError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Git
* @name getArchive
* @summary 下载仓库内容
* @request get:/{repo}/-/git/archive/{ref_with_path}

----------------------------------
* @param {GetArchiveParams} arg0 - getArchive request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  ref_with_path
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/archive/${ref_with_path}`,
    _apiTag: "/{repo}/-/git/archive/{ref_with_path}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/git/archive/{ref_with_path}",
      path: {
        repo,
        ref_with_path
      }
    }
  });
}