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
 * @Source /{repo}/-/git/tag-annotations/{tag}
 */

/**
 * @description getTagAnnotations request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetTagAnnotationsRes Success Response Type
 */

/**
 * @description GetTagAnnotationsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-contents:r
* @tags Git
* @name getTagAnnotations
* @summary 查询指定 tag 的元数据。Query the metadata of the specified tag.
* @request get:/{repo}/-/git/tag-annotations/{tag}

----------------------------------
* @param {GetTagAnnotationsParams} arg0 - getTagAnnotations request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  tag
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/tag-annotations/${tag}`,
    _apiTag: "/{repo}/-/git/tag-annotations/{tag}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/git/tag-annotations/{tag}",
      path: {
        repo,
        tag
      }
    }
  });
}