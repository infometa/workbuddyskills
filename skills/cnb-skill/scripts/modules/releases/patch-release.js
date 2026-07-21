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
 * @Source /{repo}/-/releases/{release_id}
 */

/**
 * @description patchRelease request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PatchReleaseRes Success Response Type
 */

/**
 * @description PatchReleaseError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags Releases
* @name patchRelease
* @summary 更新 release。Update a release.
* @request patch:/{repo}/-/releases/{release_id}

----------------------------------
* @param {PatchReleaseParams} arg0 - patchRelease request params
* @param {OpenapiPatchReleaseForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  release_id
}, patch_release_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/releases/${release_id}`,
    _apiTag: "/{repo}/-/releases/{release_id}",
    method: "patch",
    data: patch_release_form,
    _originParams: {
      method: "patch",
      _apiTag: "/{repo}/-/releases/{release_id}",
      path: {
        repo,
        release_id
      },
      body: patch_release_form
    }
  });
}