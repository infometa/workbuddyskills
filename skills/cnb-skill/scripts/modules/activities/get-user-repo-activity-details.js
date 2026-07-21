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
 * @Source /users/{username}/repo-activities/{activityType}
 */

/**
 * @description getUserRepoActivityDetails request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetUserRepoActivityDetailsRes Success Response Type
 */

/**
 * @description GetUserRepoActivityDetailsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-engage:r
* @tags Activities
* @name getUserRepoActivityDetails
* @summary 个人仓库动态详情列表。List of personal repository activity details.
* @request get:/users/{username}/repo-activities/{activityType}

----------------------------------
* @param {GetUserRepoActivityDetailsParams} arg0 - getUserRepoActivityDetails request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  username,
  activityType,
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
    url: `/users/${username}/repo-activities/${activityType}`,
    _apiTag: "/users/{username}/repo-activities/{activityType}",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/users/{username}/repo-activities/{activityType}",
      path: {
        username,
        activityType
      },
      query: query
    }
  });
}