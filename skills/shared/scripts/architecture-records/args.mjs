// Command-line parsing for the architecture records tool. Every problem is a `usage` error.
import { ToolError } from '../architecture-delta/errors.mjs';

const FLAGS = {
  change: ['--repo', '--model', '--before', '--deps', '--separator', '--name', '--date', '--run', '--asked-by',
    '--summary', '--rejected', '--timeout'],
};
const SWITCHES = { change: ['--compare'] };
const REQUIRED = { change: ['--repo', '--deps', '--name', '--date', '--run'] };
const MAX_TIMEOUT = 600;
const usage = (detail) => new ToolError('usage', detail);

export function parseArgs(argv) {
  const [command, ...rest] = argv;
  if (!Object.hasOwn(FLAGS, command ?? '')) {
    throw usage(`unknown subcommand ${command ?? '(none)'}; use ${Object.keys(FLAGS).join(' or ')}`);
  }
  const opts = {};
  const switches = new Set();
  const rejected = [];
  for (let i = 0; i < rest.length;) {
    const flag = rest[i];
    if (SWITCHES[command].includes(flag)) {
      if (switches.has(flag)) throw usage(`${flag} given twice`);
      switches.add(flag);
      i += 1;
      continue;
    }
    if (!FLAGS[command].includes(flag)) throw usage(`unknown flag for ${command}: ${flag}`);
    const value = rest[i + 1];
    if (value === undefined || value.startsWith('--')) throw usage(`${flag} needs a value`);
    if (flag === '--rejected') rejected.push(value);
    else if (Object.hasOwn(opts, flag)) throw usage(`${flag} given twice`);
    else opts[flag] = value;
    i += 2;
  }
  for (const flag of REQUIRED[command]) if (opts[flag] === undefined) throw usage(`${flag} is required`);
  const compare = switches.has('--compare');
  for (const flag of ['--asked-by', '--summary']) {
    if (!compare && opts[flag] === undefined) throw usage(`${flag} is required without --compare`);
  }
  for (const flag of ['--model', '--before', '--separator']) if (opts[flag] === '') throw usage(`${flag} must not be empty`);
  const timeoutText = opts['--timeout'] ?? '60';
  if (!/^\d+$/.test(timeoutText) || Number(timeoutText) > MAX_TIMEOUT) {
    throw usage(`--timeout must be a whole number from 0 to ${MAX_TIMEOUT}`);
  }
  return {
    command,
    repo: opts['--repo'],
    model: opts['--model'] ?? 'docs/architecture',
    before: opts['--before'] ?? null,
    deps: opts['--deps'],
    separator: opts['--separator'] ?? '.',
    name: opts['--name'],
    date: opts['--date'],
    run: opts['--run'],
    askedBy: opts['--asked-by'] ?? null,
    summary: opts['--summary'] ?? null,
    rejected,
    compare,
    timeout: Number(timeoutText),
  };
}
