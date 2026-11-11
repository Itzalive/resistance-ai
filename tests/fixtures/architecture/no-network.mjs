// Test preload: any network call throws.
import http from 'node:http';
import https from 'node:https';

const deny = () => {
  throw new Error('network access attempted');
};
globalThis.fetch = deny;
http.request = deny;
http.get = deny;
https.request = deny;
https.get = deny;
