// Error type, output cleaning and error lines for the architecture delta tool.

export class ToolError extends Error {
  constructor(token, details) {
    const list = [].concat(details).map(String);
    super(`${token}: ${list.join('; ')}`);
    this.token = token;
    this.details = list;
  }
}

const ANSI = /\u001b\[[0-?]*[ -\/]*[@-~]|\u001b\][^\u0007\u001b]*(?:\u0007|\u001b\\)?/g;
const CONTROLS = /[\u0000-\u001f\u007f-\u009f‪-‮⁦-⁩]/g;
export const MAX_POINTS = 200;

export function clean(value) {
  const text = String(value).replace(ANSI, '').replace(CONTROLS, '');
  const points = Array.from(text);
  return points.length > MAX_POINTS ? `${points.slice(0, MAX_POINTS - 1).join('')}…` : text;
}

export function errorLines(error) {
  return error.details.map((detail) => `error: ${error.token}: ${clean(detail)}`);
}
