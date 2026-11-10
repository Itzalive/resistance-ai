import fs from 'node:fs';

fs.mkdirSync('build', { recursive: true });
fs.copyFileSync('deps/dependencies.json', 'build/architecture-deps.json');
