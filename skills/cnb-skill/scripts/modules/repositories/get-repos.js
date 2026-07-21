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
 * @Source /user/repos
 */

/**
 * @description getRepos request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetReposRes Success Response Type
 */

/**
 * @description GetReposError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-engage:r
* @tags Repositories
* @name getRepos
* @summary 获取当前用户拥有指定权限及其以上权限的仓库。List repositories owned by the current user with the specified permissions or higher.
* @request get:/user/repos

----------------------------------
* @param {GetReposParams} arg0 - getRepos request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
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
    url: "/user/repos",
    _apiTag: "/user/repos",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/user/repos",
      query: query
    }
  });
}