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
 * @description PutPushLimitSettingsRes Success Response Type
 */

/**
 * @description PutPushLimitSettingsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:rw
* @tags GitSettings
* @name putPushLimitSettings
* @summary 设置仓库推送设置。Set push limit settings.
* @request put:/{repo}/-/settings/push-limit

----------------------------------
* @param {string} arg0
* @param {ApiPushLimitSettings} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, push_limit_form, {
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
    method: "put",
    data: push_limit_form,
    _originParams: {
      method: "put",
      _apiTag: "/{repo}/-/settings/push-limit",
      path: {
        repo
      },
      body: push_limit_form
    }
  });
}