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
 * @Source /{repo}/-/commit-assets/download/{commit_id}/{filename}
 */

/**
 * @description getCommitAssets request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetCommitAssetsRes Success Response Type
 */

/**
 * @description GetCommitAssetsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-contents:r
* @tags Git
* @name getCommitAssets
* @summary 发起一个获取 commits 附件的请求， 302到有一定效期的下载地址。Get a request to fetch a commit assets and returns 302 redirect to the assets URL with specific valid time.
* @request get:/{repo}/-/commit-assets/download/{commit_id}/{filename}

----------------------------------
* @param {GetCommitAssetsParams} arg0 - getCommitAssets request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  commit_id,
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
    url: `/${repo}/-/commit-assets/download/${commit_id}/${filename}`,
    _apiTag: "/{repo}/-/commit-assets/download/{commit_id}/{filename}",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/commit-assets/download/{commit_id}/{filename}",
      path: {
        repo,
        commit_id,
        filename
      },
      query: query
    }
  });
}