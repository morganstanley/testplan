const
  { dirname, resolve, delimiter } = require('path'),
  { appPackageJson, appNodeModules } = require('react-scripts/config/paths'),
  { getServers } = require('jest-dev-server'),
  { env: { PATH, SKIP_BUILD, CI, HEADLESS }, execPath } = process,
  // serve production build for puppeteer integration tests
  { scripts: { build, serve } } = require(appPackageJson),
  isSkipBuild = !!JSON.parse(SKIP_BUILD || '0'),
  isHeadless = !!JSON.parse(CI || '0') && !!JSON.parse(HEADLESS || '1');

module.exports = {
  // see github.com/smooth-code/jest-puppeteer/issues/120#issuecomment-464185653
  launch: {
    dumpio: true,
    ...(isHeadless ? {} : { headless: false, devtools: true }),
  },
  server: {
    debug: true,
    proto: 'http',
    host: '127.0.0.1',
    port: 5000,
    usedPortAction: 'error',
    launchTimeout: 1000 * 60 * 5,
    command: (isSkipBuild ? '' : `${build} && `) + serve,
    options: {
      env: {
        PATH: [
          dirname(execPath),
          resolve(appNodeModules, '.bin'),
          PATH
        ].join(delimiter),
      },
      windowsVerbatimArguments: true,
    },
  },
  getOrigin() {
    return `${this.server.proto}://${this.server.host}:${this.server.port}`;
  },
  getProcesses: getServers,
};
