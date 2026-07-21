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
 * @Source /{repo}/-/releases/download/{tag}/{filename}
 */

/**
 * @description getReleasesAsset request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetReleasesAssetRes Success Response Type
 */

/**
 * @description GetReleasesAssetError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-contents:r
* @tags Releases
* @name getReleasesAsset
* @summary 发起一个获取 release 附件的请求， 302到有一定效期的下载地址。Get a request to fetch a release assets and returns 302 redirect to the assets URL with specific valid time.
* @request get:/{repo}/-/releases/download/{tag}/{filename}

----------------------------------
* @param {GetReleasesAssetParams} arg0 - getReleasesAsset request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  tag,
  filename,
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
    url: `/${repo}/-/releases/download/${tag}/${filename}`,
    _apiTag: "/{repo}/-/releases/download/{tag}/{filename}",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/releases/download/{tag}/{filename}",
      path: {
        repo,
        tag,
        filename
      },
      query: query
    }
  });
}