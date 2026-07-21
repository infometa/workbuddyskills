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
 * @Source /{repo}/-/settings/pull-request
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetPullRequestSettingsRes Success Response Type
 */

/**
 * @description GetPullRequestSettingsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:r
* @tags GitSettings
* @name getPullRequestSettings
* @summary 查询仓库合并请求设置。List pull request settings.
* @request get:/{repo}/-/settings/pull-request

----------------------------------
* @param {string} arg0
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default(repo, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/settings/pull-request`,
    _apiTag: "/{repo}/-/settings/pull-request",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/settings/pull-request",
      path: {
        repo
      }
    }
  });
}