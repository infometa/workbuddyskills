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
 * @Source /{registry}
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteRegistryRes Success Response Type
 */

/**
 * @description DeleteRegistryError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* registry-delete:rw
* @tags Registries
* @name deleteRegistry
* @summary 删除制品库。Delete the registry.
* @request delete:/{registry}

----------------------------------
* @param {string} arg0
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default(registry, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${registry}`,
    _apiTag: "/{registry}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{registry}",
      path: {
        registry
      }
    }
  });
}