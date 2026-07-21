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
 * @Source /{mission}/-/members/{username}
 */

/**
 * @description addMembersOfMission request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description AddMembersOfMissionRes Success Response Type
 */

/**
 * @description AddMembersOfMissionError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* mission-manage:rw
* @tags Members
* @name addMembersOfMission
* @summary 添加成员。Add members.
* @request post:/{mission}/-/members/{username}

----------------------------------
* @param {AddMembersOfMissionParams} arg0 - addMembersOfMission request params
* @param {DtoUpdateMembersRequest} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  mission,
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
    url: `/${mission}/-/members/${username}`,
    _apiTag: "/{mission}/-/members/{username}",
    method: "post",
    data: request,
    _originParams: {
      method: "post",
      _apiTag: "/{mission}/-/members/{username}",
      path: {
        mission,
        username
      },
      body: request
    }
  });
}