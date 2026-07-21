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
 * @Source /{slug}/-/charge/special-amount
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetSpecialAmountRes Success Response Type
 */

/**
 * @description GetSpecialAmountError Error Response Type
 */

/**
* @description 查看根组织的特权额度，需要根组织的 master 以上权限才可以查看
* 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* group-resource:r
* @tags Charge
* @name getSpecialAmount
* @summary 查看特权额度
* @request get:/{slug}/-/charge/special-amount

----------------------------------
* @param {string} arg0
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default(slug, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${slug}/-/charge/special-amount`,
    _apiTag: "/{slug}/-/charge/special-amount",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{slug}/-/charge/special-amount",
      path: {
        slug
      }
    }
  });
}