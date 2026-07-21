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
 * @Source /{repo}/-/issues
 */

/**
 * @description Other reuqest params
 */

/**
 * @description CreateIssueRes Success Response Type
 */

/**
 * @description CreateIssueError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-issue:rw
* @tags Issues
* @name createIssue
* @summary 创建一个 Issue。Create an issue.
* @request post:/{repo}/-/issues

----------------------------------
* @param {string} arg0
* @param {ApiPostIssueForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, post_issue_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/issues`,
    _apiTag: "/{repo}/-/issues",
    method: "post",
    data: post_issue_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/issues",
      path: {
        repo
      },
      body: post_issue_form
    }
  });
}