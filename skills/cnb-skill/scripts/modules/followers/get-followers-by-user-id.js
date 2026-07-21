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
 * @Source /users/{username}/followers
 */

/**
 * @description getFollowersByUserID request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetFollowersByUserIDRes Success Response Type
 */

/**
 * @description GetFollowersByUserIDError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-engage:r
* @tags Followers
* @name getFollowersByUserID
* @summary 获取指定用户的粉丝列表。Get the followers list of specified user.
* @request get:/users/{username}/followers

----------------------------------
* @param {GetFollowersByUserIDParams} arg0 - getFollowersByUserID request params
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
    url: `/users/${username}/followers`,
    _apiTag: "/users/{username}/followers",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/users/{username}/followers",
      path: {
        username
      },
      query: query
    }
  });
}