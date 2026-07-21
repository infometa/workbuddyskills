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
 * @Source /{slug}/-/packages/{type}/{name}/-/tags
 */

/**
 * @description listPackageTags request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListPackageTagsRes Success Response Type
 */

/**
 * @description ListPackageTagsError Error Response Type
 */

/**
* @description 制品详情页-版本列表
* 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* registry-package:r
* @tags Registries
* @name listPackageTags
* @summary 查询制品标签列表。 List all tags under specific package.
* @request get:/{slug}/-/packages/{type}/{name}/-/tags

----------------------------------
* @param {ListPackageTagsParams} arg0 - listPackageTags request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  slug,
  type,
  name,
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
    url: `/${slug}/-/packages/${type}/${name}/-/tags`,
    _apiTag: "/{slug}/-/packages/{type}/{name}/-/tags",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{slug}/-/packages/{type}/{name}/-/tags",
      path: {
        slug,
        type,
        name
      },
      query: query
    }
  });
}