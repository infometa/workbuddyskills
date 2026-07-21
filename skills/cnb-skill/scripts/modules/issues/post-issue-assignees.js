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
 * @description postIssueAssignees request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PostIssueAssigneesRes Success Response Type
 */

/**
 * @description PostIssueAssigneesError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-issue:rw
* @tags Issues
* @name postIssueAssignees
* @summary 添加处理人到指定的 issue。  Adds up to assignees to a issue, Users already assigned to an issue are not replaced.
* @request post:/{repo}/-/issues/{number}/assignees

----------------------------------
* @param {PostIssueAssigneesParams} arg0 - postIssueAssignees request params
* @param {ApiPostIssueAssigneesForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number
}, post_issue_assignees_form, {
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
    method: "post",
    data: post_issue_assignees_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/issues/{number}/assignees",
      path: {
        repo,
        number
      },
      body: post_issue_assignees_form
    }
  });
}