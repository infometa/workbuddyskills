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
 * @Source /{repo}/-/git/compare/{base_head}
 */

/**
 * @description getCompareCommits request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetCompareCommitsRes Success Response Type
 */

/**
 * @description GetCompareCommitsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Git
* @name getCompareCommits
* @summary 比较两个提交、分支或标签之间差异的接口。Compare two commits, branches, or tags.
* @request get:/{repo}/-/git/compare/{base_head}

----------------------------------
* @param {GetCompareCommitsParams} arg0 - getCompareCommits request params
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
    url: `/${repo}/-/git/compare/${base_head}`,
    _apiTag: "/{repo}/-/git/compare/{base_head}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/git/compare/{base_head}",
      path: {
        repo,
        base_head
      }
    }
  });
}