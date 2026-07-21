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
 * @Source /user
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetUserInfoRes Success Response Type
 */

/**
 * @description GetUserInfoError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-profile:r
* @tags Users
* @name getUserInfo
* @summary 获取指定用户的详情信息。Get detailed information for a specified user.
* @request get:/user

----------------------------------
* @param {RequestConfig} arg0 - Other reuqest params
*/
async function _default({
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: "/user",
    _apiTag: "/user",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/user"
    }
  });
}