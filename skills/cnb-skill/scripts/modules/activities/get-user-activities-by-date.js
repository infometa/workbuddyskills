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
 * @Source /users/{username}/activities
 */

/**
 * @description getUserActivitiesByDate request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetUserActivitiesByDateRes Success Response Type
 */

/**
 * @description GetUserActivitiesByDateError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-engage:r
* @tags Activities
* @name getUserActivitiesByDate
* @summary 获取个人动态活跃详情汇总。Get user activities by date.
* @request get:/users/{username}/activities

----------------------------------
* @param {GetUserActivitiesByDateParams} arg0 - getUserActivitiesByDate request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  username,
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
    url: `/users/${username}/activities`,
    _apiTag: "/users/{username}/activities",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/users/{username}/activities",
      path: {
        username
      },
      query: query
    }
  });
}