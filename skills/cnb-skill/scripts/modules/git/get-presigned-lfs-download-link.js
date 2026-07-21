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
 * @Source /{slug}/-/lfs/{oid}
 */

/**
 * @description getPresignedLFSDownloadLink request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetPresignedLFSDownloadLinkRes Success Response Type
 */

/**
 * @description GetPresignedLFSDownloadLinkError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Git
* @name getPresignedLFSDownloadLink
* @summary 获取 git lfs 文件下载链接
* @request get:/{slug}/-/lfs/{oid}

----------------------------------
* @param {GetPresignedLFSDownloadLinkParams} arg0 - getPresignedLFSDownloadLink request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  slug,
  oid,
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
    url: `/${slug}/-/lfs/${oid}`,
    _apiTag: "/{slug}/-/lfs/{oid}",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{slug}/-/lfs/{oid}",
      path: {
        slug,
        oid
      },
      query: query
    }
  });
}