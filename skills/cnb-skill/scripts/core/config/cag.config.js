module.exports = {
  target: 'https://api.cnb-dev.woa.com/swagger.json',
  skillsOutputDir: `./skills`,
  // skillsDev: true,
  skillConfig: {
    fetchConfig: {
      responseConverter: {
        'get@/{repo}/-/issues/{number}': {
          converter: 'convert-link',
          handler: (handler, fetchOriginParams, data) => {
            data.body = handler(data.body, fetchOriginParams.path.repo);
            return data
          }
        },
        'get@/{repo}/-/issues/{number}/comments/{comment_id}': {
          converter: 'convert-link',
          handler: (handler, fetchOriginParams, data) => {
            data.body = handler(data.body, fetchOriginParams.path.repo);
            return data
          }
        },
        'get@/{repo}/-/issues/{number}/comments': {
          converter: 'convert-link',
          handler: (handler, fetchOriginParams, data) => {
            for (let i = 0; i < data.length; i++) {
              data[i].body = handler(data[i].body, fetchOriginParams.path.repo);
            }
            return data
          }
        },
        'get@/{repo}/-/pulls/{number}': {
          converter: 'convert-link',
          handler: (handler, fetchOriginParams, data) => {
            data.body = handler(data.body, fetchOriginParams.path.repo);
            return data
          }
        },
        'get@/{repo}/-/pulls/{number}/comments/{comment_id}': {
          converter: 'convert-link',
          handler: (handler, fetchOriginParams, data) => {
            data.body = handler(data.body, fetchOriginParams.path.repo);
            return data
          }
        },
        'get@/{repo}/-/pulls/{number}/comments': {
          converter: 'convert-link',
          handler: (handler, fetchOriginParams, data) => {
            for (let i = 0; i < data.length; i++) {
              data[i].body = handler(data[i].body, fetchOriginParams.path.repo);
            }
            return data
          }
        },
      }
    }
  }
}