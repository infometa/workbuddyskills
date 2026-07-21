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
 * @Source /{repo}/-/git/commit-statuses/{commitish}
 */

/**
 * @description getCommitStatuses request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetCommitStatusesRes Success Response Type
 */

/**
 * @description GetCommitStatusesError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Git
* @name getCommitStatuses
* @summary 查询指定 commit 的提交状态。List commit check statuses.
* @request get:/{repo}/-/git/commit-statuses/{commitish}

----------------------------------
* @param {GetCommitStatusesParams} arg0 - getCommitStatuses request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  commitish
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/commit-statuses/${commitish}`,
    _apiTag: "/{repo}/-/git/commit-statuses/{commitish}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/git/commit-statuses/{commitish}",
      path: {
        repo,
        commitish
      }
    }
  });
}