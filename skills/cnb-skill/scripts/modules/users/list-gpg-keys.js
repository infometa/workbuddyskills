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
 * @Source /user/gpg-keys
 */

/**
 * @description listGPGKeys request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListGPGKeysRes Success Response Type
 */

/**
 * @description ListGPGKeysError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-profile:r
* @tags Users
* @name listGPGKeys
* @summary 获取用户 GPG keys 列表。List GPG Keys.
* @request get:/user/gpg-keys

----------------------------------
* @param {ListGPGKeysParams} arg0 - listGPGKeys request params
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
    url: "/user/gpg-keys",
    _apiTag: "/user/gpg-keys",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/user/gpg-keys",
      query: query
    }
  });
}