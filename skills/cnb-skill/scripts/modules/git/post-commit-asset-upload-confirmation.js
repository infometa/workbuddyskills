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
 * @Source /{repo}/-/git/commit-assets/{sha1}/asset-upload-confirmation/{upload_token}/{asset_path}
 */

/**
 * @description postCommitAssetUploadConfirmation request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PostCommitAssetUploadConfirmationRes Success Response Type
 */

/**
 * @description PostCommitAssetUploadConfirmationError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags Git
* @name postCommitAssetUploadConfirmation
* @summary 确认 commit 附件上传完成。Confirm commit asset upload.
* @request post:/{repo}/-/git/commit-assets/{sha1}/asset-upload-confirmation/{upload_token}/{asset_path}

----------------------------------
* @param {PostCommitAssetUploadConfirmationParams} arg0 - postCommitAssetUploadConfirmation request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  sha1,
  upload_token,
  asset_path,
  ...query
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/commit-assets/${sha1}/asset-upload-confirmation/${upload_token}/${asset_path}`,
    _apiTag: "/{repo}/-/git/commit-assets/{sha1}/asset-upload-confirmation/{upload_token}/{asset_path}",
    method: "post",
    params: query,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/git/commit-assets/{sha1}/asset-upload-confirmation/{upload_token}/{asset_path}",
      path: {
        repo,
        sha1,
        upload_token,
        asset_path
      },
      query: query
    }
  });
}