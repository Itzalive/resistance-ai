// Command-line parsing for the architecture delta tool. Every problem is a `usage` error.
import { ToolError } from './errors.mjs';

const FLAGS = {
  check: ['--repo', '--deps', '--model', '--gap', '--scope', '--shards', '--separator', '--format', '--timeout'],
  export: ['--repo', '--model', '--timeout'],
};
const MAX_TIMEOUT = 600;

function usage(detail) {
  return new ToolError('usage', detail);
}

export function parseArgs(argv) {
  const [command, ...rest] = argv;
  if (!Object.hasOwn(FLAGS, command ?? '')) {
    throw usage(`unknown subcommand ${command ?? '(none)'}; use check or export`);
  }
  const opts = {};
  for (let i = 0; i < rest.length; i += 2) {
    const flag = rest[i];
    const value = rest[i + 1];
    if (!FLAGS[command].includes(flag)) throw usage(`unknown flag for ${command}: ${flag}`);
    if (value === undefined || value.startsWith('--')) throw usage(`${flag} needs a value`);
    if (Object.hasOwn(opts, flag)) throw usage(`${flag} given twice`);
    opts[flag] = value;
  }
  if (!opts['--repo']) throw usage('--repo is required');
  if (command === 'check' && !opts['--deps']) throw usage('--deps is required for check');
  for (const flag of ['--model', '--gap', '--shards']) if (opts[flag] === '') throw usage(`${flag} must not be empty`);
  const format = opts['--format'] ?? 'text';
  if (format !== 'text' && format !== 'json') throw usage('--format must be text or json');
  const timeoutText = opts['--timeout'] ?? '60';
  if (!/^\d+$/.test(timeoutText) || Number(timeoutText) > MAX_TIMEOUT) {
    throw usage(`--timeout must be a whole number from 0 to ${MAX_TIMEOUT}`);
  }
  const separator = opts['--separator'] ?? '.';
  if (separator === '') throw usage('--separator must not be empty');
  let scope = null;
  if (opts['--scope'] !== undefined) {
    scope = opts['--scope'].split(',').map((s) => s.trim());
    if (scope.some((s) => s === '')) throw usage('--scope has an empty element id');
  }
  return {
    command,
    repo: opts['--repo'],
    deps: opts['--deps'] ?? null,
    model: opts['--model'] ?? 'architecture',
    gap: opts['--gap'] ?? null,
    scope,
    shards: opts['--shards'] ?? null,
    separator,
    format,
    timeout: Number(timeoutText),
  };
}
