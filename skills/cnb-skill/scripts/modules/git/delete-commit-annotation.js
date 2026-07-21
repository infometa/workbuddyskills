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
 * @Source /{repo}/-/git/commit-annotations/{sha}/{key}
 */

/**
 * @description deleteCommitAnnotation request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteCommitAnnotationRes Success Response Type
 */

/**
 * @description DeleteCommitAnnotationError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags Git
* @name deleteCommitAnnotation
* @summary 删除指定 commit 的元数据。Delete commit annotation.
* @request delete:/{repo}/-/git/commit-annotations/{sha}/{key}

----------------------------------
* @param {DeleteCommitAnnotationParams} arg0 - deleteCommitAnnotation request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  sha,
  key
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/commit-annotations/${sha}/${key}`,
    _apiTag: "/{repo}/-/git/commit-annotations/{sha}/{key}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/git/commit-annotations/{sha}/{key}",
      path: {
        repo,
        sha,
        key
      }
    }
  });
}