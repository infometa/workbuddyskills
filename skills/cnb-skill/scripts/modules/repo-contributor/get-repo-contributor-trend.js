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
 * @Source /{slug}/-/contributor/trend
 */

/**
 * @description getRepoContributorTrend request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetRepoContributorTrendRes Success Response Type
 */

/**
 * @description GetRepoContributorTrendError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags RepoContributor
* @name getRepoContributorTrend
* @summary 查询仓库贡献者前 100 名的详细趋势数据。Query detailed trend data for top 100 contributors of the repository.
* @request get:/{slug}/-/contributor/trend

----------------------------------
* @param {GetRepoContributorTrendParams} arg0 - getRepoContributorTrend request params
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
    url: `/${slug}/-/contributor/trend`,
    _apiTag: "/{slug}/-/contributor/trend",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{slug}/-/contributor/trend",
      path: {
        slug
      },
      query: query
    }
  });
}