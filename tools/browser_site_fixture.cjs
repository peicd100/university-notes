// Shared bounded localhost server for built-site UX checks, not a deployment.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const prefix = '/university-notes/';
const mime = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.json': 'application/json', '.xml': 'application/xml', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp', '.woff': 'font/woff', '.woff2': 'font/woff2' };
async function serve(directory) {
  const root = path.resolve(directory);
  const server = http.createServer((req, res) => {
    try {
      const pathname = new URL(req.url, 'http://localhost').pathname;
      if (!pathname.startsWith(prefix)) { res.writeHead(404).end(); return; }
      let file = path.resolve(root, decodeURIComponent(pathname.slice(prefix.length)) || 'index.html');
      if (!file.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
      if (fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
      if (process.env.UX_HTML_OVERLAY_DIR && path.extname(file) === '.html') {
        const overlay = path.resolve(process.env.UX_HTML_OVERLAY_DIR, path.relative(root, file));
        if (fs.existsSync(overlay)) file = overlay;
      }
      // Explicit development-only overlay. Frozen builds are never rewritten.
      if (process.env.UX_SOURCE_OVERLAY === '1' && pathname.includes('/assets/')) {
        const name = path.basename(file);
        const source = path.resolve(name === 'search-peicd.js' ? 'theme/assets/javascripts/workers/search-peicd.js' : 'theme/assets/pymdownx-extras/' + name);
        if (name.endsWith('.js') && fs.existsSync(source)) file = source;
        if (/^peicd-site\..*\.css$/.test(name)) file = path.resolve('theme/assets/pymdownx-extras/自定義.css');
      }
      res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream' });
      if (process.env.UX_SOURCE_OVERLAY === '1' && path.extname(file) === '.html') {
        const bootstrap = fs.readFileSync(path.resolve('theme/assets/pymdownx-extras/page-ux.js'), 'utf8');
        const html = fs.readFileSync(file, 'utf8').replace(/(<script(?:\s[^>]*)?>)([\s\S]*?)(<\/script>)/g,
          (whole, open, code, close) => code.includes('Must run before Material reads __config') ? open + bootstrap + close : whole);
        res.end(html);
      } else if (path.basename(file) === 'sitemap.xml') res.end(fs.readFileSync(file, 'utf8').replaceAll('https://peicd100.github.io/university-notes/', `http://${req.headers.host}${prefix}`));
      else fs.createReadStream(file).on('error', () => res.destroy()).pipe(res);
    } catch (_) { res.writeHead(404).end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  return { base: `http://127.0.0.1:${server.address().port}${prefix}`, close: () => new Promise(resolve => server.close(resolve)) };
}
module.exports = { serve };
