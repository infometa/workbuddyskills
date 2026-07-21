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
 * @Source /{group}/-/members/{username}
 */

/**
 * @description deleteMembersOfGroup request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteMembersOfGroupRes Success Response Type
 */

/**
 * @description DeleteMembersOfGroupError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* group-manage:rw
* @tags Members
* @name deleteMembersOfGroup
* @summary 删除指定组织的直接成员。Remove direct members from specified organization.
* @request delete:/{group}/-/members/{username}

----------------------------------
* @param {DeleteMembersOfGroupParams} arg0 - deleteMembersOfGroup request params
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
    url: `/${group}/-/members/${username}`,
    _apiTag: "/{group}/-/members/{username}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{group}/-/members/{username}",
      path: {
        group,
        username
      }
    }
  });
}