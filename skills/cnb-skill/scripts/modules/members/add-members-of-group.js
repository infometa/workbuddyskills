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
 * @description addMembersOfGroup request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description AddMembersOfGroupRes Success Response Type
 */

/**
 * @description AddMembersOfGroupError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* group-manage:rw
* @tags Members
* @name addMembersOfGroup
* @summary 添加成员。Add members.
* @request post:/{group}/-/members/{username}

----------------------------------
* @param {AddMembersOfGroupParams} arg0 - addMembersOfGroup request params
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
    method: "post",
    data: request,
    _originParams: {
      method: "post",
      _apiTag: "/{group}/-/members/{username}",
      path: {
        group,
        username
      },
      body: request
    }
  });
}