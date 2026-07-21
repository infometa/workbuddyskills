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
 * @Source /{repo}/-/git/commit-annotations/{sha}
 */

/**
 * @description getCommitAnnotations request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetCommitAnnotationsRes Success Response Type
 */

/**
 * @description GetCommitAnnotationsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Git
* @name getCommitAnnotations
* @summary 查询指定 commit 的元数据。Get commit annotations.
* @request get:/{repo}/-/git/commit-annotations/{sha}

----------------------------------
* @param {GetCommitAnnotationsParams} arg0 - getCommitAnnotations request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  sha
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/commit-annotations/${sha}`,
    _apiTag: "/{repo}/-/git/commit-annotations/{sha}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/git/commit-annotations/{sha}",
      path: {
        repo,
        sha
      }
    }
  });
}