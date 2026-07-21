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
 * @Source /{slug}/-/code/issues/{record_id}
 */

/**
 * @description getCodeIssueDetailOpenAPI request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetCodeIssueDetailOpenAPIRes Success Response Type
 */

/**
 * @description GetCodeIssueDetailOpenAPIError Error Response Type
 */

/**
* @description 根据问题记录ID获取源码扫描问题的详细信息，包括问题位置、责任人、规则描述等
* 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags RepoCodeIssue
* @name getCodeIssueDetailOpenAPI
* @summary 获取源码扫描问题详情
* @request get:/{slug}/-/code/issues/{record_id}

----------------------------------
* @param {GetCodeIssueDetailOpenAPIParams} arg0 - getCodeIssueDetailOpenAPI request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  slug,
  record_id
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${slug}/-/code/issues/${record_id}`,
    _apiTag: "/{slug}/-/code/issues/{record_id}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{slug}/-/code/issues/{record_id}",
      path: {
        slug,
        record_id
      }
    }
  });
}