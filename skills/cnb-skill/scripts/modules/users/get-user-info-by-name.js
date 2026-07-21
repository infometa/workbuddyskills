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
 * @Source /users/{username}
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetUserInfoByNameRes Success Response Type
 */

/**
 * @description GetUserInfoByNameError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-profile:r
* @tags Users
* @name getUserInfoByName
* @summary 获取指定用户的详情信息。Get detailed information for a specified user.
* @request get:/users/{username}

----------------------------------
* @param {string} arg0
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default(username, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/users/${username}`,
    _apiTag: "/users/{username}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/users/{username}",
      path: {
        username
      }
    }
  });
}