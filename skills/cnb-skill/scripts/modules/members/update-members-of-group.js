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
 * @description updateMembersOfGroup request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description UpdateMembersOfGroupRes Success Response Type
 */

/**
 * @description UpdateMembersOfGroupError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* group-manage:rw
* @tags Members
* @name updateMembersOfGroup
* @summary 更新指定组织的直接成员权限信息。Update permission information for direct members in specified organization.
* @request put:/{group}/-/members/{username}

----------------------------------
* @param {UpdateMembersOfGroupParams} arg0 - updateMembersOfGroup request params
* @param {DtoUpdateMembersRequest} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  group,
  username
}, request, {
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
    method: "put",
    data: request,
    _originParams: {
      method: "put",
      _apiTag: "/{group}/-/members/{username}",
      path: {
        group,
        username
      },
      body: request
    }
  });
}