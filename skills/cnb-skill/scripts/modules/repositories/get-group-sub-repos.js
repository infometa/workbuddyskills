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
 * @Source /{slug}/-/repos
 */

/**
 * @description getGroupSubRepos request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetGroupSubReposRes Success Response Type
 */

/**
 * @description GetGroupSubReposError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* group-resource:r
* @tags Repositories
* @name getGroupSubRepos
* @summary 查询组织下访问用户有权限查看到仓库。List the repositories that the user has access to.
* @request get:/{slug}/-/repos

----------------------------------
* @param {GetGroupSubReposParams} arg0 - getGroupSubRepos request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  slug,
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
    url: `/${slug}/-/repos`,
    _apiTag: "/{slug}/-/repos",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{slug}/-/repos",
      path: {
        slug
      },
      query: query
    }
  });
}