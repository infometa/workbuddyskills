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
 * @Source /{repo}/-/git/commit-annotations-in-batch
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetCommitAnnotationsInBatchRes Success Response Type
 */

/**
 * @description GetCommitAnnotationsInBatchError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Git
* @name getCommitAnnotationsInBatch
* @summary 查询指定 commit 的元数据。Get commit annotations in batch.
* @request post:/{repo}/-/git/commit-annotations-in-batch

----------------------------------
* @param {string} arg0
* @param {WebGetCommitAnnotationsInBatchForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, get_commit_annotations_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/commit-annotations-in-batch`,
    _apiTag: "/{repo}/-/git/commit-annotations-in-batch",
    method: "post",
    data: get_commit_annotations_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/git/commit-annotations-in-batch",
      path: {
        repo
      },
      body: get_commit_annotations_form
    }
  });
}