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
 * @Source /{repo}/-/git/tags
 */

/**
 * @description Other reuqest params
 */

/**
 * @description CreateTagRes Success Response Type
 */

/**
 * @description CreateTagError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags Git
* @name createTag
* @summary 创建一个 tag。Create a tag.
* @request post:/{repo}/-/git/tags

----------------------------------
* @param {string} arg0
* @param {ApiPostTagFrom} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, post_tag_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/tags`,
    _apiTag: "/{repo}/-/git/tags",
    method: "post",
    data: post_tag_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/git/tags",
      path: {
        repo
      },
      body: post_tag_form
    }
  });
}