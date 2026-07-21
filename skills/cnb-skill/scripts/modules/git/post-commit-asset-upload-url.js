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
 * @Source /{repo}/-/git/commit-assets/{sha1}/asset-upload-url
 */

/**
 * @description postCommitAssetUploadURL request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PostCommitAssetUploadURLRes Success Response Type
 */

/**
 * @description PostCommitAssetUploadURLError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags Git
* @name postCommitAssetUploadURL
* @summary 新增一个 commit 附件。Create a commit asset.
* @request post:/{repo}/-/git/commit-assets/{sha1}/asset-upload-url

----------------------------------
* @param {PostCommitAssetUploadURLParams} arg0 - postCommitAssetUploadURL request params
* @param {OpenapiPostCommitAssetUploadURLForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  sha1
}, create_commit_asset_upload_url_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/commit-assets/${sha1}/asset-upload-url`,
    _apiTag: "/{repo}/-/git/commit-assets/{sha1}/asset-upload-url",
    method: "post",
    data: create_commit_asset_upload_url_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/git/commit-assets/{sha1}/asset-upload-url",
      path: {
        repo,
        sha1
      },
      body: create_commit_asset_upload_url_form
    }
  });
}