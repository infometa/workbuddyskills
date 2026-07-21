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
 * @Source /{repo}/-/issues/{number}/labels/{name}
 */

/**
 * @description deleteIssueLabel request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteIssueLabelRes Success Response Type
 */

/**
 * @description DeleteIssueLabelError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-issue:rw
* @tags Issues
* @name deleteIssueLabel
* @summary 删除 issue 标签。Remove a label from an issue.
* @request delete:/{repo}/-/issues/{number}/labels/{name}

----------------------------------
* @param {DeleteIssueLabelParams} arg0 - deleteIssueLabel request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  number,
  name
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/issues/${number}/labels/${name}`,
    _apiTag: "/{repo}/-/issues/{number}/labels/{name}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/issues/{number}/labels/{name}",
      path: {
        repo,
        number,
        name
      }
    }
  });
}