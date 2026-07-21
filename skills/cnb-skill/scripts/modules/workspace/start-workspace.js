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
 * @Source /{repo}/-/workspace/start
 */

/**
 * @description Other reuqest params
 */

/**
 * @description StartWorkspaceRes Success Response Type
 */

/**
 * @description StartWorkspaceError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-cnb-trigger:rw
* @tags Workspace
* @name startWorkspace
* @summary 启动云原生开发环境，已存在环境则直接打开，否则重新创建开发环境。Start cloud-native dev. Opens existing env or creates a new one.
* @request post:/{repo}/-/workspace/start

----------------------------------
* @param {string} arg0
* @param {DtoStartWorkspaceReq} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, request, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/workspace/start`,
    _apiTag: "/{repo}/-/workspace/start",
    method: "post",
    data: request,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/workspace/start",
      path: {
        repo
      },
      body: request
    }
  });
}