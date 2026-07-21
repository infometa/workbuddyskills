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
 * @Source /workspace/list
 */

/**
 * @description listWorkspaces request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListWorkspacesRes Success Response Type
 */

/**
 * @description ListWorkspacesError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-engage:r
* @tags Workspace
* @name listWorkspaces
* @summary 获取我的云原生开发环境列表。List my workspaces.
* @request get:/workspace/list

----------------------------------
* @param {ListWorkspacesParams} arg0 - listWorkspaces request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
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
    url: "/workspace/list",
    _apiTag: "/workspace/list",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/workspace/list",
      query: query
    }
  });
}