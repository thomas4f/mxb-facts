// A static server for the built site (_site/), as GitHub Pages serves it: a folder's index.html for its address. Node only, so
// the checks run the same in the Playwright image (which has no Python) as on a runner.
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';

const root = new URL('../../_site/', import.meta.url).pathname, port = Number(process.argv[2] || 8790);
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.woff2': 'font/woff2', '.md': 'text/markdown; charset=utf-8', '.yaml': 'text/yaml; charset=utf-8' };
createServer(async (req, res) => {
  let p = normalize(decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (p.includes('..')) { res.writeHead(400).end(); return; }
  let f = join(root, p);
  try { if ((await stat(f)).isDirectory()) f = join(f, 'index.html'); res.writeHead(200, { 'content-type': types[extname(f)] || 'application/octet-stream' }).end(await readFile(f)); }
  catch { res.writeHead(404).end('not found'); }
}).listen(port, '127.0.0.1');
