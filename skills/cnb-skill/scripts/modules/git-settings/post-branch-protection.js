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
 * @Source /{repo}/-/settings/branch-protections
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PostBranchProtectionRes Success Response Type
 */

/**
 * @description PostBranchProtectionError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:rw
* @tags GitSettings
* @name postBranchProtection
* @summary 新增仓库保护分支规则。Create branch protection rule.
* @request post:/{repo}/-/settings/branch-protections

----------------------------------
* @param {string} arg0
* @param {ApiBranchProtection} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, branch_protection_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/settings/branch-protections`,
    _apiTag: "/{repo}/-/settings/branch-protections",
    method: "post",
    data: branch_protection_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/settings/branch-protections",
      path: {
        repo
      },
      body: branch_protection_form
    }
  });
}