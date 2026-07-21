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
 * @description UpdateGroupSettingRes Success Response Type
 */

/**
 * @description UpdateGroupSettingError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* group-manage:rw
* @tags Organizations
* @name updateGroupSetting
* @summary 更新指定组织的配置。Updates the configuration for the specified organization.
* @request put:/{slug}/-/settings

----------------------------------
* @param {string} arg0
* @param {DtoGroupSettingReq} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(slug, request, {
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
    method: "put",
    data: request,
    _originParams: {
      method: "put",
      _apiTag: "/{slug}/-/settings",
      path: {
        slug
      },
      body: request
    }
  });
}