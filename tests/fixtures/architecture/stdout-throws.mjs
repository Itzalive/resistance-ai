// Test preload: the first stdout write that carries a report throws.
const original = process.stdout.write.bind(process.stdout);
let armed = true;
process.stdout.write = (chunk, ...rest) => {
  if (armed && String(chunk).includes('"breaches"')) {
    armed = false;
    throw new Error('forced stdout failure');
  }
  return original(chunk, ...rest);
};
