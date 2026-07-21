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
 * @Source /{repo}/-/assets/{assetID}
 */

/**
 * @description deleteAsset request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteAssetRes Success Response Type
 */

/**
 * @description DeleteAssetError Error Response Type
 */

/**
* @description 通过 asset 记录 id 删除一个 asset，release和commit附件不能通过该接口删除
* 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:rw
* @tags Assets
* @name deleteAsset
* @summary 通过 asset 记录 id 删除一个 asset
* @request delete:/{repo}/-/assets/{assetID}

----------------------------------
* @param {DeleteAssetParams} arg0 - deleteAsset request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  assetID
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/assets/${assetID}`,
    _apiTag: "/{repo}/-/assets/{assetID}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/assets/{assetID}",
      path: {
        repo,
        assetID
      }
    }
  });
}