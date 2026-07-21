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
 * @description deleteIssueLabels request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteIssueLabelsRes Success Response Type
 */

/**
 * @description DeleteIssueLabelsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-issue:rw
* @tags Issues
* @name deleteIssueLabels
* @summary 清空 issue 标签。Remove all labels from an issue.
* @request delete:/{repo}/-/issues/{number}/labels

----------------------------------
* @param {DeleteIssueLabelsParams} arg0 - deleteIssueLabels request params
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
    url: `/${repo}/-/issues/${number}/labels`,
    _apiTag: "/{repo}/-/issues/{number}/labels",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/issues/{number}/labels",
      path: {
        repo,
        number
      }
    }
  });
}