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
 * @Source /{slug}/-/packages/{type}/{name}
 */

/**
 * @description getPackage request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetPackageRes Success Response Type
 */

/**
 * @description GetPackageError Error Response Type
 */

/**
* @description 制品详情页
* 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* registry-package:r
* @tags Registries
* @name getPackage
* @summary 获取指定制品的详细信息。 Get the package detail.
* @request get:/{slug}/-/packages/{type}/{name}

----------------------------------
* @param {GetPackageParams} arg0 - getPackage request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  slug,
  type,
  name
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${slug}/-/packages/${type}/${name}`,
    _apiTag: "/{slug}/-/packages/{type}/{name}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{slug}/-/packages/{type}/{name}",
      path: {
        slug,
        type,
        name
      }
    }
  });
}