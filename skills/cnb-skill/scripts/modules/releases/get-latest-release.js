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
 * @Source /{repo}/-/releases/latest
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetLatestReleaseRes Success Response Type
 */

/**
 * @description GetLatestReleaseError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Releases
* @name getLatestRelease
* @summary 查询最新的 release。Query the latest release.
* @request get:/{repo}/-/releases/latest

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
    url: `/${repo}/-/releases/latest`,
    _apiTag: "/{repo}/-/releases/latest",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/releases/latest",
      path: {
        repo
      }
    }
  });
}