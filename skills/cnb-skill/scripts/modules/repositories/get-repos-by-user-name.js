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
 * @Source /users/{username}/repos
 */

/**
 * @description getReposByUserName request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetReposByUserNameRes Success Response Type
 */

/**
 * @description GetReposByUserNameError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-engage:r
* @tags Repositories
* @name getReposByUserName
* @summary 获取指定用户有指定以上权限并且客人态可见的仓库。List repositories where the specified user has the specified permission level or higher and are visible to guests.
* @request get:/users/{username}/repos

----------------------------------
* @param {GetReposByUserNameParams} arg0 - getReposByUserName request params
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
    url: `/users/${username}/repos`,
    _apiTag: "/users/{username}/repos",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/users/{username}/repos",
      path: {
        username
      },
      query: query
    }
  });
}