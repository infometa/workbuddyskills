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
 * @Source /{repo}/-/imgs/{imgPath}
 */

/**
 * @description deleteRepoImgs request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteRepoImgsRes Success Response Type
 */

/**
 * @description DeleteRepoImgsError Error Response Type
 */

/**
* @description 删除 UploadImgs 上传的图片
* 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:rw
* @tags Pulls,Issues
* @name deleteRepoImgs
* @summary 删除 UploadImgs 上传的图片
* @request delete:/{repo}/-/imgs/{imgPath}

----------------------------------
* @param {DeleteRepoImgsParams} arg0 - deleteRepoImgs request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  imgPath
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/imgs/${imgPath}`,
    _apiTag: "/{repo}/-/imgs/{imgPath}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/imgs/{imgPath}",
      path: {
        repo,
        imgPath
      }
    }
  });
}