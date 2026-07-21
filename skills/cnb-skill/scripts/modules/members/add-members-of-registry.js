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
 * @Source /{registry}/-/members/{username}
 */

/**
 * @description addMembersOfRegistry request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description AddMembersOfRegistryRes Success Response Type
 */

/**
 * @description AddMembersOfRegistryError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* registry-manage:rw
* @tags Members
* @name addMembersOfRegistry
* @summary 添加成员。Add members.
* @request post:/{registry}/-/members/{username}

----------------------------------
* @param {AddMembersOfRegistryParams} arg0 - addMembersOfRegistry request params
* @param {DtoUpdateMembersRequest} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  registry,
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
    url: `/${registry}/-/members/${username}`,
    _apiTag: "/{registry}/-/members/{username}",
    method: "post",
    data: request,
    _originParams: {
      method: "post",
      _apiTag: "/{registry}/-/members/{username}",
      path: {
        registry,
        username
      },
      body: request
    }
  });
}