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
 * @Source /{repo}/-/issues/{number}/labels
 */

/**
 * @description postIssueLabels request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PostIssueLabelsRes Success Response Type
 */

/**
 * @description PostIssueLabelsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-issue:rw
* @tags Issues
* @name postIssueLabels
* @summary 新增 issue 标签。Add labels to an issue.
* @request post:/{repo}/-/issues/{number}/labels

----------------------------------
* @param {PostIssueLabelsParams} arg0 - postIssueLabels request params
* @param {ApiPostIssueLabelsForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number
}, post_issue_labels_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/issues/${number}/labels`,
    _apiTag: "/{repo}/-/issues/{number}/labels",
    method: "post",
    data: post_issue_labels_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/issues/{number}/labels",
      path: {
        repo,
        number
      },
      body: post_issue_labels_form
    }
  });
}