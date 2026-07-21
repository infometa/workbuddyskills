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
 * @Source /{repo}/-/settings/cloud-native-build
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PutPipelineSettingsRes Success Response Type
 */

/**
 * @description PutPipelineSettingsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:rw
* @tags GitSettings
* @name putPipelineSettings
* @summary 更新仓库云原生构建设置。Update pipeline settings.
* @request put:/{repo}/-/settings/cloud-native-build

----------------------------------
* @param {string} arg0
* @param {ApiPipelineSettings} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, pipeline_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/settings/cloud-native-build`,
    _apiTag: "/{repo}/-/settings/cloud-native-build",
    method: "put",
    data: pipeline_form,
    _originParams: {
      method: "put",
      _apiTag: "/{repo}/-/settings/cloud-native-build",
      path: {
        repo
      },
      body: pipeline_form
    }
  });
}