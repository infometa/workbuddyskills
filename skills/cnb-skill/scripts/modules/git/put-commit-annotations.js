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
 * @description putCommitAnnotations request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PutCommitAnnotationsRes Success Response Type
 */

/**
 * @description PutCommitAnnotationsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags Git
* @name putCommitAnnotations
* @summary 设定指定 commit 的元数据。Put commit annotations.
* @request put:/{repo}/-/git/commit-annotations/{sha}

----------------------------------
* @param {PutCommitAnnotationsParams} arg0 - putCommitAnnotations request params
* @param {OpenapiPutCommitAnnotationsForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  sha
}, put_commit_annotations_form, {
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
    method: "put",
    data: put_commit_annotations_form,
    _originParams: {
      method: "put",
      _apiTag: "/{repo}/-/git/commit-annotations/{sha}",
      path: {
        repo,
        sha
      },
      body: put_commit_annotations_form
    }
  });
}