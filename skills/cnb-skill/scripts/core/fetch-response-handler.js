"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.fetchResponseHandler = fetchResponseHandler;
async function fetchResponseHandler(fetchOriginParams, response) {
  const config = require('./config/cag.config.js');
  const responseConverter = config?.skillConfig?.fetchConfig?.responseConverter;
  if (!responseConverter) {
    return response;
  }
  const {
    method,
    _apiTag
  } = fetchOriginParams;
  const requestTag = `${method}@${_apiTag}`;
  const convertConfig = responseConverter[requestTag];
  if (convertConfig) {
    const {
      converter,
      handler
    } = convertConfig;
    try {
      const converterExample = require(`./utils/${converter}`).default;
      if (converterExample && typeof converterExample === 'function') {
        return handler(converterExample, fetchOriginParams, response.data);
      }
    } catch (e) {
      console.error(`converter ${converter} not found`);
    }
  }
  return response;
}