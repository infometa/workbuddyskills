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
 * @Source /{repo}/-/git/tags/{tag}
 */

/**
 * @description deleteTag request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteTagRes Success Response Type
 */

/**
 * @description DeleteTagError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-contents:rw
* @tags Git
* @name deleteTag
* @summary 删除指定 tag。Delete the specified tag.
* @request delete:/{repo}/-/git/tags/{tag}

----------------------------------
* @param {DeleteTagParams} arg0 - deleteTag request params
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
    url: `/${repo}/-/git/tags/${tag}`,
    _apiTag: "/{repo}/-/git/tags/{tag}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/git/tags/{tag}",
      path: {
        repo,
        tag
      }
    }
  });
}