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
 * @description putTagAnnotations request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PutTagAnnotationsRes Success Response Type
 */

/**
 * @description PutTagAnnotationsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-contents:rw
* @tags Git
* @name putTagAnnotations
* @summary 设定指定 tag 的元数据。Set the metadata of the specified tag.
* @request put:/{repo}/-/git/tag-annotations/{tag}

----------------------------------
* @param {PutTagAnnotationsParams} arg0 - putTagAnnotations request params
* @param {OpenapiPutTagAnnotationsForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  tag
}, put_tag_annotations_form, {
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
    method: "put",
    data: put_tag_annotations_form,
    _originParams: {
      method: "put",
      _apiTag: "/{repo}/-/git/tag-annotations/{tag}",
      path: {
        repo,
        tag
      },
      body: put_tag_annotations_form
    }
  });
}