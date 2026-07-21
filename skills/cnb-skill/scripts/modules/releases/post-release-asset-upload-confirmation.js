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
 * @Source /{repo}/-/releases/{release_id}/asset-upload-confirmation/{upload_token}/{asset_path}
 */

/**
 * @description postReleaseAssetUploadConfirmation request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PostReleaseAssetUploadConfirmationRes Success Response Type
 */

/**
 * @description PostReleaseAssetUploadConfirmationError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags Releases
* @name postReleaseAssetUploadConfirmation
* @summary 确认  release 附件上传完成。Confirm release asset upload.
* @request post:/{repo}/-/releases/{release_id}/asset-upload-confirmation/{upload_token}/{asset_path}

----------------------------------
* @param {PostReleaseAssetUploadConfirmationParams} arg0 - postReleaseAssetUploadConfirmation request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  release_id,
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
    url: `/${repo}/-/releases/${release_id}/asset-upload-confirmation/${upload_token}/${asset_path}`,
    _apiTag: "/{repo}/-/releases/{release_id}/asset-upload-confirmation/{upload_token}/{asset_path}",
    method: "post",
    params: query,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/releases/{release_id}/asset-upload-confirmation/{upload_token}/{asset_path}",
      path: {
        repo,
        release_id,
        upload_token,
        asset_path
      },
      query: query
    }
  });
}