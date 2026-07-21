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
 * @Source /search/public-repos
 */

/**
 * @description listPublicRepos request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListPublicReposRes Success Response Type
 */

/**
 * @description ListPublicReposError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-base-info:r
* @tags Search
* @name listPublicRepos
* @summary Search resource with the key
* @request get:/search/public-repos

----------------------------------
* @param {ListPublicReposParams} arg0 - listPublicRepos request params
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
    url: "/search/public-repos",
    _apiTag: "/search/public-repos",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/search/public-repos",
      query: query
    }
  });
}