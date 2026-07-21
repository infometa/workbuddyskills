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
 * @Source /{repo}/-/issues/{number}/assignees
 */

/**
 * @description listIssueAssignees request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListIssueAssigneesRes Success Response Type
 */

/**
 * @description ListIssueAssigneesError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-issue:r
* @tags Issues
* @name listIssueAssignees
* @summary 查询指定 issue 的处理人。 List repository issue assignees.
* @request get:/{repo}/-/issues/{number}/assignees

----------------------------------
* @param {ListIssueAssigneesParams} arg0 - listIssueAssignees request params
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
    url: `/${repo}/-/issues/${number}/assignees`,
    _apiTag: "/{repo}/-/issues/{number}/assignees",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/issues/{number}/assignees",
      path: {
        repo,
        number
      }
    }
  });
}