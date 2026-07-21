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
 * @Source /{repo}/-/releases/{release_id}/assets/{asset_id}
 */

/**
 * @description getReleaseAsset request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetReleaseAssetRes Success Response Type
 */

/**
 * @description GetReleaseAssetError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Releases
* @name getReleaseAsset
* @summary 查询指定的 release 附件 the specified release asset.
* @request get:/{repo}/-/releases/{release_id}/assets/{asset_id}

----------------------------------
* @param {GetReleaseAssetParams} arg0 - getReleaseAsset request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  release_id,
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
    url: `/${repo}/-/releases/${release_id}/assets/${asset_id}`,
    _apiTag: "/{repo}/-/releases/{release_id}/assets/{asset_id}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/releases/{release_id}/assets/{asset_id}",
      path: {
        repo,
        release_id,
        asset_id
      }
    }
  });
}