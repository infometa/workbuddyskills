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
 * @Source /{repo}/-/git/archive-compare-changed-files/{base_head}
 */

/**
 * @description getArchiveCompareChangedFiles request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetArchiveCompareChangedFilesRes Success Response Type
 */

/**
 * @description GetArchiveCompareChangedFilesError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Git
* @name getArchiveCompareChangedFiles
* @summary 打包下载两次 ref 之间的变更文件。Download archive of changed files for a compare.
* @request get:/{repo}/-/git/archive-compare-changed-files/{base_head}

----------------------------------
* @param {GetArchiveCompareChangedFilesParams} arg0 - getArchiveCompareChangedFiles request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  base_head
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/archive-compare-changed-files/${base_head}`,
    _apiTag: "/{repo}/-/git/archive-compare-changed-files/{base_head}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/git/archive-compare-changed-files/{base_head}",
      path: {
        repo,
        base_head
      }
    }
  });
}