'use strict';
// Generated at package time. Loads the original api-client.js from the adjacent gzip file.
const fs = require('fs');
const zlib = require('zlib');
const source = zlib.gunzipSync(fs.readFileSync(__filename + '.gz')).toString('utf8');
module._compile(source, __filename);
