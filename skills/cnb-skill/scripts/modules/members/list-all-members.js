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
 * @Source /{slug}/-/list-members
 */

/**
 * @description listAllMembers request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListAllMembersRes Success Response Type
 */

/**
 * @description ListAllMembersError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:r
* @tags Members
* @name listAllMembers
* @summary 获取指定仓库内的有效成员列表，包含继承成员。List active members in specified repository including inherited members.
* @request get:/{slug}/-/list-members

----------------------------------
* @param {ListAllMembersParams} arg0 - listAllMembers request params
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
    url: `/${slug}/-/list-members`,
    _apiTag: "/{slug}/-/list-members",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{slug}/-/list-members",
      path: {
        slug
      },
      query: query
    }
  });
}