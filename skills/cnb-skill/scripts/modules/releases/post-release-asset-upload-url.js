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
 * @Source /{repo}/-/releases/{release_id}/asset-upload-url
 */

/**
 * @description postReleaseAssetUploadURL request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PostReleaseAssetUploadURLRes Success Response Type
 */

/**
 * @description PostReleaseAssetUploadURLError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags Releases
* @name postReleaseAssetUploadURL
* @summary 新增一个 release 附件。Create a release asset.
* @request post:/{repo}/-/releases/{release_id}/asset-upload-url

----------------------------------
* @param {PostReleaseAssetUploadURLParams} arg0 - postReleaseAssetUploadURL request params
* @param {OpenapiPostReleaseAssetUploadURLForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  release_id
}, create_release_asset_upload_url_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/releases/${release_id}/asset-upload-url`,
    _apiTag: "/{repo}/-/releases/{release_id}/asset-upload-url",
    method: "post",
    data: create_release_asset_upload_url_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/releases/{release_id}/asset-upload-url",
      path: {
        repo,
        release_id
      },
      body: create_release_asset_upload_url_form
    }
  });
}