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
 * @Source /{repo}/-/top-activity-users
 */

/**
 * @description topContributors request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description TopContributorsRes Success Response Type
 */

/**
 * @description TopContributorsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-base-info:r
* @tags Activities
* @name topContributors
* @summary 获取仓库 top 活跃用户。List the top active users
* @request get:/{repo}/-/top-activity-users

----------------------------------
* @param {TopContributorsParams} arg0 - topContributors request params
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
    url: `/${repo}/-/top-activity-users`,
    _apiTag: "/{repo}/-/top-activity-users",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/top-activity-users",
      path: {
        repo
      },
      query: query
    }
  });
}