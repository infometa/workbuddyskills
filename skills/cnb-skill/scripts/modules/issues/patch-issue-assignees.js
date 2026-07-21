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
 * @description patchIssueAssignees request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PatchIssueAssigneesRes Success Response Type
 */

/**
 * @description PatchIssueAssigneesError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-issue:rw
* @tags Issues
* @name patchIssueAssignees
* @summary 更新 issue 中的处理人。 Updates the assignees of an issue.
* @request patch:/{repo}/-/issues/{number}/assignees

----------------------------------
* @param {PatchIssueAssigneesParams} arg0 - patchIssueAssignees request params
* @param {ApiPatchIssueAssigneesForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number
}, patch_issue_assignees_form, {
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
    method: "patch",
    data: patch_issue_assignees_form,
    _originParams: {
      method: "patch",
      _apiTag: "/{repo}/-/issues/{number}/assignees",
      path: {
        repo,
        number
      },
      body: patch_issue_assignees_form
    }
  });
}