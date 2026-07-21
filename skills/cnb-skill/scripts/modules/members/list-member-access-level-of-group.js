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
 * @Source /{group}/-/members/{username}/access-level
 */

/**
 * @description listMemberAccessLevelOfGroup request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListMemberAccessLevelOfGroupRes Success Response Type
 */

/**
 * @description ListMemberAccessLevelOfGroupError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* group-manage:r
* @tags Members
* @name listMemberAccessLevelOfGroup
* @summary 获取指定组织内指定成员的权限信息, 结果按组织层级来展示, 包含上层组织的权限继承信息。Get specified member's permissions with organizational hierarchy.
* @request get:/{group}/-/members/{username}/access-level

----------------------------------
* @param {ListMemberAccessLevelOfGroupParams} arg0 - listMemberAccessLevelOfGroup request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  group,
  username
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${group}/-/members/${username}/access-level`,
    _apiTag: "/{group}/-/members/{username}/access-level",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{group}/-/members/{username}/access-level",
      path: {
        group,
        username
      }
    }
  });
}