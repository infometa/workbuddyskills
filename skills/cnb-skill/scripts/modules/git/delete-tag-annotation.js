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
 * @Source /{repo}/-/git/tag-annotations/{tag_with_key}
 */

/**
 * @description deleteTagAnnotation request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteTagAnnotationRes Success Response Type
 */

/**
 * @description DeleteTagAnnotationError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-contents:rw
* @tags Git
* @name deleteTagAnnotation
* @summary 删除指定 tag 的元数据。Delete the metadata of the specified tag.
* @request delete:/{repo}/-/git/tag-annotations/{tag_with_key}

----------------------------------
* @param {DeleteTagAnnotationParams} arg0 - deleteTagAnnotation request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  tag_with_key
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/tag-annotations/${tag_with_key}`,
    _apiTag: "/{repo}/-/git/tag-annotations/{tag_with_key}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/git/tag-annotations/{tag_with_key}",
      path: {
        repo,
        tag_with_key
      }
    }
  });
}