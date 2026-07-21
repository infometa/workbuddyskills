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
 * @Source /ranks/repo/language-list
 */

/**
 * @description getLanguageList request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetLanguageListRes Success Response Type
 */

/**
 * @description GetLanguageListError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-basic-info:r
* @tags Rank
* @name getLanguageList
* @summary 获取排行榜语言
* @request get:/ranks/repo/language-list

----------------------------------
* @param {GetLanguageListParams} arg0 - getLanguageList request params
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
    url: "/ranks/repo/language-list",
    _apiTag: "/ranks/repo/language-list",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/ranks/repo/language-list",
      query: query
    }
  });
}