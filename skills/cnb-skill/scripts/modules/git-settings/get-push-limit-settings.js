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
 * @Source /{repo}/-/settings/push-limit
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetPushLimitSettingsRes Success Response Type
 */

/**
 * @description GetPushLimitSettingsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:r
* @tags GitSettings
* @name getPushLimitSettings
* @summary 查询仓库推送设置。List push limit settings.
* @request get:/{repo}/-/settings/push-limit

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
    url: `/${repo}/-/settings/push-limit`,
    _apiTag: "/{repo}/-/settings/push-limit",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/settings/push-limit",
      path: {
        repo
      }
    }
  });
}