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
 * @Source /{repo}/-/git/commit-assets/{sha1}/{asset_id}
 */

/**
 * @description deleteCommitAsset request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteCommitAssetRes Success Response Type
 */

/**
 * @description DeleteCommitAssetError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags Git
* @name deleteCommitAsset
* @summary 删除指定 commit 的附件。Delete commit asset.
* @request delete:/{repo}/-/git/commit-assets/{sha1}/{asset_id}

----------------------------------
* @param {DeleteCommitAssetParams} arg0 - deleteCommitAsset request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  sha1,
  asset_id
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/commit-assets/${sha1}/${asset_id}`,
    _apiTag: "/{repo}/-/git/commit-assets/{sha1}/{asset_id}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/git/commit-assets/{sha1}/{asset_id}",
      path: {
        repo,
        sha1,
        asset_id
      }
    }
  });
}