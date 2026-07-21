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
 * @Source /users/{username}/pinned-repos
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetPinnedRepoByIDRes Success Response Type
 */

/**
 * @description GetPinnedRepoByIDError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-engage:r
* @tags Repositories
* @name getPinnedRepoByID
* @summary 获取指定用户的用户仓库墙。 Get a list of repositories that the specified user has pinned.
* @request get:/users/{username}/pinned-repos

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
    url: `/users/${username}/pinned-repos`,
    _apiTag: "/users/{username}/pinned-repos",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/users/{username}/pinned-repos",
      path: {
        username
      }
    }
  });
}