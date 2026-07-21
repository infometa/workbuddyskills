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
 * @Source /{repo}/-/members/{username}
 */

/**
 * @description addMembersOfRepo request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description AddMembersOfRepoRes Success Response Type
 */

/**
 * @description AddMembersOfRepoError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:rw
* @tags Members
* @name addMembersOfRepo
* @summary 添加成员。Add members.
* @request post:/{repo}/-/members/{username}

----------------------------------
* @param {AddMembersOfRepoParams} arg0 - addMembersOfRepo request params
* @param {DtoUpdateMembersRequest} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
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
    url: `/${repo}/-/members/${username}`,
    _apiTag: "/{repo}/-/members/{username}",
    method: "post",
    data: request,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/members/{username}",
      path: {
        repo,
        username
      },
      body: request
    }
  });
}