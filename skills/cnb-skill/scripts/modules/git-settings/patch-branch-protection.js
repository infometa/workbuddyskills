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
 * @Source /{repo}/-/settings/branch-protections/{id}
 */

/**
 * @description patchBranchProtection request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PatchBranchProtectionRes Success Response Type
 */

/**
 * @description PatchBranchProtectionError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:rw
* @tags GitSettings
* @name patchBranchProtection
* @summary 更新仓库保护分支规则。Update branch protection rule.
* @request patch:/{repo}/-/settings/branch-protections/{id}

----------------------------------
* @param {PatchBranchProtectionParams} arg0 - patchBranchProtection request params
* @param {ApiBranchProtection} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  id
}, branch_protection_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/settings/branch-protections/${id}`,
    _apiTag: "/{repo}/-/settings/branch-protections/{id}",
    method: "patch",
    data: branch_protection_form,
    _originParams: {
      method: "patch",
      _apiTag: "/{repo}/-/settings/branch-protections/{id}",
      path: {
        repo,
        id
      },
      body: branch_protection_form
    }
  });
}