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
 * @Source /{repo}/-/security/overview
 */

/**
 * @description getRepoSecurityOverview request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetRepoSecurityOverviewRes Success Response Type
 */

/**
 * @description GetRepoSecurityOverviewError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-security:r
* @tags Security
* @name getRepoSecurityOverview
* @summary 查询仓库安全模块概览数据。Query the security overview data of a repository
* @request get:/{repo}/-/security/overview

----------------------------------
* @param {GetRepoSecurityOverviewParams} arg0 - getRepoSecurityOverview request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  ...query
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/security/overview`,
    _apiTag: "/{repo}/-/security/overview",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/security/overview",
      path: {
        repo
      },
      query: query
    }
  });
}