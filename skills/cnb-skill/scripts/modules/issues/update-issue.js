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
 * @Source /{repo}/-/issues/{number}
 */

/**
 * @description updateIssue request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description UpdateIssueRes Success Response Type
 */

/**
 * @description UpdateIssueError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-issue:rw
* @tags Issues
* @name updateIssue
* @summary 更新一个 Issue。Update an issue.
* @request patch:/{repo}/-/issues/{number}

----------------------------------
* @param {UpdateIssueParams} arg0 - updateIssue request params
* @param {ApiPatchIssueForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number
}, patch_issue_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/issues/${number}`,
    _apiTag: "/{repo}/-/issues/{number}",
    method: "patch",
    data: patch_issue_form,
    _originParams: {
      method: "patch",
      _apiTag: "/{repo}/-/issues/{number}",
      path: {
        repo,
        number
      },
      body: patch_issue_form
    }
  });
}