"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.schemaToJson = schemaToJson;
function schemaToJson(schema, json) {
  if (schema.type === 'object' || schema.type === 'array') {
    const props = schema.type === 'object' ? schema.properties : schema.items.properties;
    // eslint-disable-next-line no-restricted-syntax
    for (const key in props) {
      const {
        type,
        items
      } = props[key];
      if (type === 'object') {
        json[key] = schemaToJson(props[key], {});
      } else if (type === 'array') {
        if (items.properties) {
          json[key] = [schemaToJson(props[key], {})];
        } else {
          json[key] = [items.type];
        }
      } else {
        json[key] = type;
      }
    }
  } else {
    return schema.type;
  }
  return json;
}