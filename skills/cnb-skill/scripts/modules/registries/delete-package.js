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
 * @description deletePackage request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeletePackageRes Success Response Type
 */

/**
 * @description DeletePackageError Error Response Type
 */

/**
* @description 制品详情页-删除制品
* 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* registry-package-delete:rw
* @tags Registries
* @name deletePackage
* @summary 删除制品。 Delete the specific package.
* @request delete:/{slug}/-/packages/{type}/{name}

----------------------------------
* @param {DeletePackageParams} arg0 - deletePackage request params
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
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{slug}/-/packages/{type}/{name}",
      path: {
        slug,
        type,
        name
      }
    }
  });
}