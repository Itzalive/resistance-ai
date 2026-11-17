// Command-line parsing for the architecture docs tool. Every problem is a `usage` error.
import { ToolError } from '../architecture-delta/errors.mjs';

const COMMANDS = ['build', 'check'];
const FLAGS = ['--repo', '--model', '--gap', '--out', '--timeout'];
const MAX_TIMEOUT = 600;
const usage = (detail) => new ToolError('usage', detail);

export function parseArgs(argv) {
  const [command, ...rest] = argv;
  if (!COMMANDS.includes(command ?? '')) throw usage(`unknown subcommand ${command ?? '(none)'}; use build or check`);
  const opts = {};
  for (let i = 0; i < rest.length; i += 2) {
    const flag = rest[i];
    const value = rest[i + 1];
    if (!FLAGS.includes(flag)) throw usage(`unknown flag for ${command}: ${flag}`);
    if (value === undefined || value.startsWith('--')) throw usage(`${flag} needs a value`);
    if (Object.hasOwn(opts, flag)) throw usage(`${flag} given twice`);
    opts[flag] = value;
  }
  if (!opts['--repo']) throw usage('--repo is required');
  for (const flag of ['--model', '--gap', '--out']) if (opts[flag] === '') throw usage(`${flag} must not be empty`);
  const timeoutText = opts['--timeout'] ?? '60';
  if (!/^\d+$/.test(timeoutText) || Number(timeoutText) > MAX_TIMEOUT) {
    throw usage(`--timeout must be a whole number from 0 to ${MAX_TIMEOUT}`);
  }
  return {
    command,
    repo: opts['--repo'],
    model: opts['--model'] ?? 'docs/architecture',
    gap: opts['--gap'] ?? null,
    out: opts['--out'] ?? null,
    timeout: Number(timeoutText),
  };
}
