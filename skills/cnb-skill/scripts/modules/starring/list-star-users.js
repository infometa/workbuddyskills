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
 * @Source /{slug}/-/stars
 */

/**
 * @description listStarUsers request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListStarUsersRes Success Response Type
 */

/**
 * @description ListStarUsersError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-basic-info:r
* @tags Starring
* @name listStarUsers
* @summary 获取指定仓库的star用户列表。Get the list of users who starred the specified repository.
* @request get:/{slug}/-/stars

----------------------------------
* @param {ListStarUsersParams} arg0 - listStarUsers request params
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
    url: `/${slug}/-/stars`,
    _apiTag: "/{slug}/-/stars",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{slug}/-/stars",
      path: {
        slug
      },
      query: query
    }
  });
}