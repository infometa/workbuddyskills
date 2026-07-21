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
 * @Source /{repo}/-/labels/{name}
 */

/**
 * @description patchLabel request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PatchLabelRes Success Response Type
 */

/**
 * @description PatchLabelError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-notes:rw
* @tags RepoLabels
* @name patchLabel
* @summary 更新标签信息。Update label information.
* @request patch:/{repo}/-/labels/{name}

----------------------------------
* @param {PatchLabelParams} arg0 - patchLabel request params
* @param {ApiPatchLabelForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  name
}, patch_label_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/labels/${name}`,
    _apiTag: "/{repo}/-/labels/{name}",
    method: "patch",
    data: patch_label_form,
    _originParams: {
      method: "patch",
      _apiTag: "/{repo}/-/labels/{name}",
      path: {
        repo,
        name
      },
      body: patch_label_form
    }
  });
}