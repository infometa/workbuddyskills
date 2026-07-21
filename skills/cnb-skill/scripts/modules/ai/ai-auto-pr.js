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
 * @Version 2.1.8
 * @Source /{repo}/-/build/ai/auto-pr
 */

/**
 * @description Other reuqest params
 */

/**
 * @description AiAutoPrRes Success Response Type
 */

/**
 * @description AiAutoPrError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags AI
* @name aiAutoPr
* @summary 根据传入的需求内容和需求标题借助 AI 自动编码并提 PR。Automatically code and create a PR with AI based on the input requirement content and title.
* @request post:/{repo}/-/build/ai/auto-pr

----------------------------------
* @param {string} arg0
* @param {DtoAiAutoPrReq} arg1
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
    url: `/${repo}/-/build/ai/auto-pr`,
    _apiTag: "/{repo}/-/build/ai/auto-pr",
    method: "post",
    data: request,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/build/ai/auto-pr",
      path: {
        repo
      },
      body: request
    }
  });
}