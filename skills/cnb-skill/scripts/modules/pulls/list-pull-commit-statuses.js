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
 * @Source /{repo}/-/pulls/{number}/commit-statuses
 */

/**
 * @description listPullCommitStatuses request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListPullCommitStatusesRes Success Response Type
 */

/**
 * @description ListPullCommitStatusesError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-pr:r
* @tags Pulls
* @name listPullCommitStatuses
* @summary 查询 Pull Request 的状态检查
* @request get:/{repo}/-/pulls/{number}/commit-statuses

----------------------------------
* @param {ListPullCommitStatusesParams} arg0 - listPullCommitStatuses request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  number
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/pulls/${number}/commit-statuses`,
    _apiTag: "/{repo}/-/pulls/{number}/commit-statuses",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/pulls/{number}/commit-statuses",
      path: {
        repo,
        number
      }
    }
  });
}