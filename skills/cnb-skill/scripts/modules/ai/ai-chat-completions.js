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
 * @Source /{repo}/-/ai/chat/completions
 */

/**
 * @description Other reuqest params
 */

/**
 * @description AiChatCompletionsRes Success Response Type
 */

/**
 * @description AiChatCompletionsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags AI
* @name aiChatCompletions
* @summary AI 对话。调用者需有代码写权限（CNB_TOKEN 仅需读权限，部署令牌不检查读写权限）。AI chat completions. Requires caller to have repo write permission.
* @request post:/{repo}/-/ai/chat/completions

----------------------------------
* @param {string} arg0
* @param {DtoAiChatCompletionsReq} arg1
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
    url: `/${repo}/-/ai/chat/completions`,
    _apiTag: "/{repo}/-/ai/chat/completions",
    method: "post",
    data: request,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/ai/chat/completions",
      path: {
        repo
      },
      body: request
    }
  });
}