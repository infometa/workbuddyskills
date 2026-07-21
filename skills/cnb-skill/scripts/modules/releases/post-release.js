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
 * @Source /{repo}/-/releases
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PostReleaseRes Success Response Type
 */

/**
 * @description PostReleaseError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags Releases
* @name postRelease
* @summary 新增一个 release。Create a release.
* @request post:/{repo}/-/releases

----------------------------------
* @param {string} arg0
* @param {OpenapiPostReleaseForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, create_release_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/releases`,
    _apiTag: "/{repo}/-/releases",
    method: "post",
    data: create_release_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/releases",
      path: {
        repo
      },
      body: create_release_form
    }
  });
}