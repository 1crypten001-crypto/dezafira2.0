console.log('POSTBUILD: Script started');
import fs from 'fs';
import path from 'path';

const clientDir = path.join(process.cwd(), 'build', 'client');
const rootDir = process.cwd();

function copyDirRecursive(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirRecursive(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

async function run() {
  console.log('POSTBUILD: run() function started');
  try {
    console.log('POSTBUILD: clientDir exists:', fs.existsSync(clientDir));
    if (!fs.existsSync(clientDir)) {
      console.warn('build/client folder not found. Skipping postbuild static copy.');
      return;
    }

    // 1. Copiar a pasta _app (contém os arquivos compilados de CSS e JS)
    const srcApp = path.join(clientDir, '_app');
    const destApp = path.join(rootDir, '_app');
    console.log('POSTBUILD: srcApp exists:', fs.existsSync(srcApp));
    if (fs.existsSync(srcApp)) {
      if (fs.existsSync(destApp)) {
        console.log('POSTBUILD: destApp exists, removing old destApp...');
        fs.rmSync(destApp, { recursive: true, force: true });
      }
      console.log('POSTBUILD: Copying _app using custom copyDirRecursive...');
      copyDirRecursive(srcApp, destApp);
      console.log('POSTBUILD: Copied build/client/_app to ./_app');
    }

    // 2. Copiar arquivos diretos da build/client para a raiz (ex: favicon.png, robots.txt, sitemap.xml)
    console.log('POSTBUILD: Reading clientDir files...');
    const items = fs.readdirSync(clientDir);
    for (const item of items) {
      const srcPath = path.join(clientDir, item);
      const stat = fs.statSync(srcPath);

      if (stat.isFile()) {
        const destPath = path.join(rootDir, item);
        // Evitar sobrescrever arquivos críticos do projeto raiz
        const protectedFiles = [
          'package.json', 
          'package-lock.json', 
          'tsconfig.json', 
          'svelte.config.js', 
          'vite.config.ts', 
          'README.md', 
          '.gitignore', 
          '.env', 
          '.env.example'
        ];
        if (!protectedFiles.includes(item)) {
          console.log(`POSTBUILD: Copying file ${item}...`);
          fs.copyFileSync(srcPath, destPath);
          console.log(`POSTBUILD: Copied build/client/${item} to ./${item}`);
        }
      }
    }
    
    console.log('POSTBUILD: Postbuild static asset copy completed successfully!');
  } catch (err) {
    console.error('POSTBUILD: Error caught:', err);
  }
}

run();
