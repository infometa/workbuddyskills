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
 * @Source /{group}/-/upload/logos
 */

/**
 * @description Other reuqest params
 */

/**
 * @description UploadLogosRes Success Response Type
 */

/**
 * @description UploadLogosError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* group-manage:rw
* @tags Organizations
* @name uploadLogos
* @summary 发起一个上传 logo 的请求，返回上传文件的url，请使用 put 发起流式上传。Initiate a request to upload logo,returns upload URL.Use PUT to initiate a stream upload.
* @request post:/{group}/-/upload/logos

----------------------------------
* @param {string} arg0
* @param {DtoUploadRequestParams} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(group, request, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${group}/-/upload/logos`,
    _apiTag: "/{group}/-/upload/logos",
    method: "post",
    data: request,
    _originParams: {
      method: "post",
      _apiTag: "/{group}/-/upload/logos",
      path: {
        group
      },
      body: request
    }
  });
}