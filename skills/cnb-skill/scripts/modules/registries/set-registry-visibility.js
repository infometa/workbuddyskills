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
 * @Source /{registry}/-/settings/set_visibility
 */

/**
 * @description setRegistryVisibility request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description SetRegistryVisibilityRes Success Response Type
 */

/**
 * @description SetRegistryVisibilityError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* registry-manage:rw
* @tags Registries
* @name setRegistryVisibility
* @summary 改变制品仓库可见性。Update visibility of registry.
* @request post:/{registry}/-/settings/set_visibility

----------------------------------
* @param {SetRegistryVisibilityParams} arg0 - setRegistryVisibility request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  registry,
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
    url: `/${registry}/-/settings/set_visibility`,
    _apiTag: "/{registry}/-/settings/set_visibility",
    method: "post",
    params: query,
    _originParams: {
      method: "post",
      _apiTag: "/{registry}/-/settings/set_visibility",
      path: {
        registry
      },
      query: query
    }
  });
}