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
 * @Source /users/{username}/following
 */

/**
 * @description getFollowingByUserID request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetFollowingByUserIDRes Success Response Type
 */

/**
 * @description GetFollowingByUserIDError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-engage:r
* @tags Followers
* @name getFollowingByUserID
* @summary 获取指定用户的关注人列表。Get the list of users that the specified user is following.
* @request get:/users/{username}/following

----------------------------------
* @param {GetFollowingByUserIDParams} arg0 - getFollowingByUserID request params
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
    url: `/users/${username}/following`,
    _apiTag: "/users/{username}/following",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/users/{username}/following",
      path: {
        username
      },
      query: query
    }
  });
}