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
 * @Source /{slug}/-/settings
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetGroupSettingRes Success Response Type
 */

/**
 * @description GetGroupSettingError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* group-manage:r
* @tags Organizations
* @name getGroupSetting
* @summary 获取指定组织的配置详情。Get the configuration details for the specified organization.
* @request get:/{slug}/-/settings

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
    url: `/${slug}/-/settings`,
    _apiTag: "/{slug}/-/settings",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{slug}/-/settings",
      path: {
        slug
      }
    }
  });
}