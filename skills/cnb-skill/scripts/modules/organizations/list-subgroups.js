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
 * @Source /{slug}/-/sub-groups
 */

/**
 * @description listSubgroups request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListSubgroupsRes Success Response Type
 */

/**
 * @description ListSubgroupsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* group-resource:r
* @tags Organizations
* @name listSubgroups
* @summary 获取指定组织下的子组织列表。Get the list of sub-organizations under the specified organization.
* @request get:/{slug}/-/sub-groups

----------------------------------
* @param {ListSubgroupsParams} arg0 - listSubgroups request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  slug,
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
    url: `/${slug}/-/sub-groups`,
    _apiTag: "/{slug}/-/sub-groups",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{slug}/-/sub-groups",
      path: {
        slug
      },
      query: query
    }
  });
}