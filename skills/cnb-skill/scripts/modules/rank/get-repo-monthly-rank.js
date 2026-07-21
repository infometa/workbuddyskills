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
 * @Source /ranks/repo/monthly
 */

/**
 * @description getRepoMonthlyRank request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetRepoMonthlyRankRes Success Response Type
 */

/**
 * @description GetRepoMonthlyRankError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-basic-info:r
* @tags Rank
* @name getRepoMonthlyRank
* @summary 获取公仓月榜
* @request get:/ranks/repo/monthly

----------------------------------
* @param {GetRepoMonthlyRankParams} arg0 - getRepoMonthlyRank request params
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
    url: "/ranks/repo/monthly",
    _apiTag: "/ranks/repo/monthly",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/ranks/repo/monthly",
      query: query
    }
  });
}