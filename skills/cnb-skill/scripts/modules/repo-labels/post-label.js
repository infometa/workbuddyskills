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
 * @Source /{repo}/-/labels
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PostLabelRes Success Response Type
 */

/**
 * @description PostLabelError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-notes:rw
* @tags RepoLabels
* @name postLabel
* @summary 创建一个 标签。Create a label.
* @request post:/{repo}/-/labels

----------------------------------
* @param {string} arg0
* @param {ApiPostLabelForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, post_label_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/labels`,
    _apiTag: "/{repo}/-/labels",
    method: "post",
    data: post_label_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/labels",
      path: {
        repo
      },
      body: post_label_form
    }
  });
}