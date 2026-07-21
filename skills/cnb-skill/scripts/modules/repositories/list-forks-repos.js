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
 * @Source /{repo}/-/forks
 */

/**
 * @description listForksRepos request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListForksReposRes Success Response Type
 */

/**
 * @description ListForksReposError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-base-info:r
* @tags Repositories
* @name listForksRepos
* @summary 获取指定仓库的 fork 列表。Get fork list for specified repository.
* @request get:/{repo}/-/forks

----------------------------------
* @param {ListForksReposParams} arg0 - listForksRepos request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
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
    url: `/${repo}/-/forks`,
    _apiTag: "/{repo}/-/forks",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/forks",
      path: {
        repo
      },
      query: query
    }
  });
}