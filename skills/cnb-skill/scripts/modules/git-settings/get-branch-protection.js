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
 * @description getBranchProtection request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetBranchProtectionRes Success Response Type
 */

/**
 * @description GetBranchProtectionError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:r
* @tags GitSettings
* @name getBranchProtection
* @summary 查询仓库保护分支规则。Get branch protection rule.
* @request get:/{repo}/-/settings/branch-protections/{id}

----------------------------------
* @param {GetBranchProtectionParams} arg0 - getBranchProtection request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  id
}, {
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
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/settings/branch-protections/{id}",
      path: {
        repo,
        id
      }
    }
  });
}