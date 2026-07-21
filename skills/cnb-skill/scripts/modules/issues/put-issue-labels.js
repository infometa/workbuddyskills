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
 * @description putIssueLabels request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PutIssueLabelsRes Success Response Type
 */

/**
 * @description PutIssueLabelsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-issue:rw
* @tags Issues
* @name putIssueLabels
* @summary 设置 issue 标签。 Set the new labels for an issue.
* @request put:/{repo}/-/issues/{number}/labels

----------------------------------
* @param {PutIssueLabelsParams} arg0 - putIssueLabels request params
* @param {ApiPutIssueLabelsForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number
}, put_issue_labels_form, {
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
    method: "put",
    data: put_issue_labels_form,
    _originParams: {
      method: "put",
      _apiTag: "/{repo}/-/issues/{number}/labels",
      path: {
        repo,
        number
      },
      body: put_issue_labels_form
    }
  });
}