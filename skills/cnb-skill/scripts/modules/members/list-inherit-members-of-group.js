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
 * @Source /{group}/-/inherit-members
 */

/**
 * @description listInheritMembersOfGroup request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListInheritMembersOfGroupRes Success Response Type
 */

/**
 * @description ListInheritMembersOfGroupError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* group-manage:r
* @tags Members
* @name listInheritMembersOfGroup
* @summary 获取指定组织的继承成员。List inherited members within specified organization
* @request get:/{group}/-/inherit-members

----------------------------------
* @param {ListInheritMembersOfGroupParams} arg0 - listInheritMembersOfGroup request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  group,
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
    url: `/${group}/-/inherit-members`,
    _apiTag: "/{group}/-/inherit-members",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{group}/-/inherit-members",
      path: {
        group
      },
      query: query
    }
  });
}