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
 * @Source /users/{username}/groups
 */

/**
 * @description getGroupsByUserID request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetGroupsByUserIDRes Success Response Type
 */

/**
 * @description GetGroupsByUserIDError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-engage:r
* @tags Organizations
* @name getGroupsByUserID
* @summary 获取指定用户拥有权限的顶层组织列表。 Get a list of top-level organizations that the specified user has permissions to access.
* @request get:/users/{username}/groups

----------------------------------
* @param {GetGroupsByUserIDParams} arg0 - getGroupsByUserID request params
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
    url: `/users/${username}/groups`,
    _apiTag: "/users/{username}/groups",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/users/{username}/groups",
      path: {
        username
      },
      query: query
    }
  });
}