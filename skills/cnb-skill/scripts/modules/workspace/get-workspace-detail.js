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
 * @Source /{repo}/-/workspace/detail/{sn}
 */

/**
 * @description getWorkspaceDetail request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetWorkspaceDetailRes Success Response Type
 */

/**
 * @description GetWorkspaceDetailError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-cnb-detail:r
* @tags Workspace
* @name getWorkspaceDetail
* @summary 根据流水线sn查询云原生开发访问地址。Query cloud-native development access address by pipeline SN.
* @request get:/{repo}/-/workspace/detail/{sn}

----------------------------------
* @param {GetWorkspaceDetailParams} arg0 - getWorkspaceDetail request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  sn
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/workspace/detail/${sn}`,
    _apiTag: "/{repo}/-/workspace/detail/{sn}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/workspace/detail/{sn}",
      path: {
        repo,
        sn
      }
    }
  });
}