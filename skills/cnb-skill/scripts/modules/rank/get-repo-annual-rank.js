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
 * @Source /ranks/repo/annual
 */

/**
 * @description getRepoAnnualRank request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetRepoAnnualRankRes Success Response Type
 */

/**
 * @description GetRepoAnnualRankError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-basic-info:r
* @tags Rank
* @name getRepoAnnualRank
* @summary 获取公仓年榜
* @request get:/ranks/repo/annual

----------------------------------
* @param {GetRepoAnnualRankParams} arg0 - getRepoAnnualRank request params
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
    url: "/ranks/repo/annual",
    _apiTag: "/ranks/repo/annual",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/ranks/repo/annual",
      query: query
    }
  });
}