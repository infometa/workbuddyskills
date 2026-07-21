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
 * @Source /{repo}/-/pull-in-batch
 */

/**
 * @description listPullsByNumbers request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListPullsByNumbersRes Success Response Type
 */

/**
 * @description ListPullsByNumbersError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-pr:r
* @tags Pulls
* @name listPullsByNumbers
* @summary 根据 number 列表查询合并请求列表。List pull requests by numbers.
* @request get:/{repo}/-/pull-in-batch

----------------------------------
* @param {ListPullsByNumbersParams} arg0 - listPullsByNumbers request params
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
    url: `/${repo}/-/pull-in-batch`,
    _apiTag: "/{repo}/-/pull-in-batch",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/pull-in-batch",
      path: {
        repo
      },
      query: query
    }
  });
}