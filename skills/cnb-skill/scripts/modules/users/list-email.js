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
 * @Source /user/emails
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListEmailRes Success Response Type
 */

/**
 * @description ListEmailError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-email:r
* @tags Users
* @name listEmail
* @summary 获取用户邮箱列表
* @request get:/user/emails

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
    url: "/user/emails",
    _apiTag: "/user/emails",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/user/emails"
    }
  });
}