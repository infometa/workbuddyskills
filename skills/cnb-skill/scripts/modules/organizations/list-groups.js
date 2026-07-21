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
 * @Source /user/groups/{slug}
 */

/**
 * @description listGroups request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListGroupsRes Success Response Type
 */

/**
 * @description ListGroupsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-engage:r
* @tags Organizations
* @name listGroups
* @summary 查询当前用户在指定组织下拥有指定权限的子组织列表。Get the list of sub-organizations that the current user has access to in the specified organization.
* @request get:/user/groups/{slug}

----------------------------------
* @param {ListGroupsParams} arg0 - listGroups request params
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
    url: `/user/groups/${slug}`,
    _apiTag: "/user/groups/{slug}",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/user/groups/{slug}",
      path: {
        slug
      },
      query: query
    }
  });
}