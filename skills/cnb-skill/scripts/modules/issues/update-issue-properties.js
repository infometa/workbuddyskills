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
 * @Source /{repo}/-/issues/{number}/property
 */

/**
 * @description updateIssueProperties request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description UpdateIssuePropertiesRes Success Response Type
 */

/**
 * @description UpdateIssuePropertiesError Error Response Type
 */

/**
* @description 为指定Issue批量更新多个自定义属性的值，要求属性 key 必须已存在，允许部分失败
* 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-issue:rw
* @tags Issues
* @name updateIssueProperties
* @summary 批量更新Issue自定义属性值
* @request patch:/{repo}/-/issues/{number}/property

----------------------------------
* @param {UpdateIssuePropertiesParams} arg0 - updateIssueProperties request params
* @param {OpenapiIssuePropertiesForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number
}, issue_properties_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/issues/${number}/property`,
    _apiTag: "/{repo}/-/issues/{number}/property",
    method: "patch",
    data: issue_properties_form,
    _originParams: {
      method: "patch",
      _apiTag: "/{repo}/-/issues/{number}/property",
      path: {
        repo,
        number
      },
      body: issue_properties_form
    }
  });
}