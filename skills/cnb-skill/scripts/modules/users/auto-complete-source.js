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
 * @Source /user/autocomplete_source
 */

/**
 * @description autoCompleteSource request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description AutoCompleteSourceRes Success Response Type
 */

/**
 * @description AutoCompleteSourceError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-engage:r
* @tags Users
* @name autoCompleteSource
* @summary 查询当前用户用户拥有指定权限的所有资源列表。List resources that the current user has specified permissions for.
* @request get:/user/autocomplete_source

----------------------------------
* @param {AutoCompleteSourceParams} arg0 - autoCompleteSource request params
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
    url: "/user/autocomplete_source",
    _apiTag: "/user/autocomplete_source",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/user/autocomplete_source",
      query: query
    }
  });
}