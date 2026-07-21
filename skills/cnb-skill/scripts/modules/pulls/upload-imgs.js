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
 * @Source /{repo}/-/upload/imgs
 */

/**
 * @description Other reuqest params
 */

/**
 * @description UploadImgsRes Success Response Type
 */

/**
 * @description UploadImgsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-contents:rw
* @tags Pulls,Issues
* @name uploadImgs
* @summary 发起一个上传 imgs 的请求，返回上传文件的url，请使用 put 发起流式上传。Initiate a request to upload images,returns upload URL.Use PUT to initiate a stream upload.
* @request post:/{repo}/-/upload/imgs

----------------------------------
* @param {string} arg0
* @param {DtoUploadRequestParams} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, request, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/upload/imgs`,
    _apiTag: "/{repo}/-/upload/imgs",
    method: "post",
    data: request,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/upload/imgs",
      path: {
        repo
      },
      body: request
    }
  });
}