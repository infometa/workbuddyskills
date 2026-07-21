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
 * @Source /{mission}/-/mission/view-list
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PutMissionViewListRes Success Response Type
 */

/**
 * @description PutMissionViewListError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* mission-manage:rw
* @tags Missions
* @name putMissionViewList
* @summary 添加、修改任务集视图。Update a mission view or add a new one.
* @request put:/{mission}/-/mission/view-list

----------------------------------
* @param {string} arg0
* @param {DtoMissionView} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(mission, request, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${mission}/-/mission/view-list`,
    _apiTag: "/{mission}/-/mission/view-list",
    method: "put",
    data: request,
    _originParams: {
      method: "put",
      _apiTag: "/{mission}/-/mission/view-list",
      path: {
        mission
      },
      body: request
    }
  });
}