import assert from 'node:assert/strict';
import test from 'node:test';

import { validateLockfileObject } from './validate-lockfile.mjs';

const manifest = {
  dependencies: {
    react: '19.2.8',
  },
  devDependencies: {
    vite: '8.2.1',
  },
};

const validLockfile = {
  name: '@golden-rose/web',
  lockfileVersion: 3,
  packages: {
    '': {
      name: '@golden-rose/web',
      version: '0.0.0',
      dependencies: {
        react: '19.2.8',
      },
      devDependencies: {
        vite: '8.2.1',
      },
    },
    'node_modules/react': {
      version: '19.2.8',
      resolved: 'https://registry.npmjs.org/react/-/react-19.2.8.tgz',
      integrity: 'sha512-' + Buffer.alloc(64).toString('base64'),
    },
    'node_modules/vite': {
      version: '8.2.1',
      resolved: 'https://registry.npmjs.org/vite/-/vite-8.2.1.tgz',
      integrity: 'sha512-' + Buffer.alloc(64, 1).toString('base64'),
      dev: true,
    },
  },
};

test('accepts a valid lockfile v3 with exact root dependency maps and registry tarballs', () => {
  assert.doesNotThrow(() => validateLockfileObject(validLockfile, manifest));
});

test('rejects a lockfile version other than 3', () => {
  const lockfile = structuredClone(validLockfile);
  lockfile.lockfileVersion = 2;

  assert.throws(
    () => validateLockfileObject(lockfile, manifest),
    /lockfileVersion must be exactly 3/,
  );
});

test('rejects root manifest drift', () => {
  const lockfile = structuredClone(validLockfile);
  lockfile.packages[''].dependencies.react = '19.2.7';

  assert.throws(
    () => validateLockfileObject(lockfile, manifest),
    /root dependency map drift/,
  );
});

test('rejects ranged, tag, url, alias, and protocol dependency specs', async (t) => {
  await t.test('range spec', () => {
    const drift = structuredClone(validLockfile);
    const manifestWithRange = { ...manifest, dependencies: { react: '^19.2.8' } };
    assert.throws(() => validateLockfileObject(drift, manifestWithRange), /exact SemVer literal/);
  });

  await t.test('tag spec', () => {
    const drift = structuredClone(validLockfile);
    const manifestWithTag = { ...manifest, dependencies: { react: 'latest' } };
    assert.throws(() => validateLockfileObject(drift, manifestWithTag), /exact SemVer literal/);
  });

  await t.test('url spec', () => {
    const drift = structuredClone(validLockfile);
    const manifestWithUrl = { ...manifest, dependencies: { react: 'https://registry.npmjs.org/react/-/react-19.2.8.tgz' } };
    assert.throws(() => validateLockfileObject(drift, manifestWithUrl), /exact SemVer literal/);
  });

  await t.test('alias spec', () => {
    const drift = structuredClone(validLockfile);
    const manifestWithAlias = { ...manifest, dependencies: { react: 'npm:preact@10.26.9' } };
    assert.throws(() => validateLockfileObject(drift, manifestWithAlias), /exact SemVer literal/);
  });

  await t.test('file protocol spec', () => {
    const drift = structuredClone(validLockfile);
    const manifestWithFile = { ...manifest, dependencies: { react: 'file:../react' } };
    assert.throws(() => validateLockfileObject(drift, manifestWithFile), /exact SemVer literal/);
  });

  await t.test('git protocol spec', () => {
    const drift = structuredClone(validLockfile);
    const manifestWithGit = { ...manifest, dependencies: { react: 'git+https://example.com/react.git' } };
    assert.throws(() => validateLockfileObject(drift, manifestWithGit), /exact SemVer literal/);
  });
});

test('rejects non-root packages with an alternate host, http, credentials, query, or fragment', async (t) => {
  await t.test('alternate host', () => {
    const lockfile = structuredClone(validLockfile);
    lockfile.packages['node_modules/react'].resolved = 'https://example.com/react/-/react-19.2.8.tgz';
    assert.throws(() => validateLockfileObject(lockfile, manifest), /registry\.npmjs\.org/);
  });

  await t.test('http url', () => {
    const lockfile = structuredClone(validLockfile);
    lockfile.packages['node_modules/react'].resolved = 'http://registry.npmjs.org/react/-/react-19.2.8.tgz';
    assert.throws(() => validateLockfileObject(lockfile, manifest), /https/);
  });

  await t.test('credentials', () => {
    const lockfile = structuredClone(validLockfile);
    lockfile.packages['node_modules/react'].resolved = 'https://user:pass@registry.npmjs.org/react/-/react-19.2.8.tgz';
    assert.throws(() => validateLockfileObject(lockfile, manifest), /must not include credentials/);
  });

  await t.test('query string', () => {
    const lockfile = structuredClone(validLockfile);
    lockfile.packages['node_modules/react'].resolved = 'https://registry.npmjs.org/react/-/react-19.2.8.tgz?download=1';
    assert.throws(() => validateLockfileObject(lockfile, manifest), /must not include query or fragment/);
  });

  await t.test('fragment', () => {
    const lockfile = structuredClone(validLockfile);
    lockfile.packages['node_modules/react'].resolved = 'https://registry.npmjs.org/react/-/react-19.2.8.tgz#hash';
    assert.throws(() => validateLockfileObject(lockfile, manifest), /must not include query or fragment/);
  });
});

test('rejects local, git, and link package sources', async (t) => {
  await t.test('link entry', () => {
    const lockfile = structuredClone(validLockfile);
    lockfile.packages['node_modules/react'] = { link: true };
    assert.throws(() => validateLockfileObject(lockfile, manifest), /link or local source/);
  });

  await t.test('file source', () => {
    const lockfile = structuredClone(validLockfile);
    lockfile.packages['node_modules/react'].resolved = 'file:../react';
    assert.throws(() => validateLockfileObject(lockfile, manifest), /link or local source/);
  });

  await t.test('git source', () => {
    const lockfile = structuredClone(validLockfile);
    lockfile.packages['node_modules/react'].resolved = 'git+https://example.com/react.git';
    assert.throws(() => validateLockfileObject(lockfile, manifest), /link or local source/);
  });
});

test('rejects missing, weak, and malformed integrity values', async (t) => {
  await t.test('missing integrity', () => {
    const lockfile = structuredClone(validLockfile);
    delete lockfile.packages['node_modules/react'].integrity;
    assert.throws(() => validateLockfileObject(lockfile, manifest), /integrity/);
  });

  await t.test('weak algorithm', () => {
    const lockfile = structuredClone(validLockfile);
    lockfile.packages['node_modules/react'].integrity = 'sha256-' + Buffer.alloc(32).toString('base64');
    assert.throws(() => validateLockfileObject(lockfile, manifest), /sha512/);
  });

  await t.test('malformed sri', () => {
    const lockfile = structuredClone(validLockfile);
    lockfile.packages['node_modules/react'].integrity = 'sha512-not-base64';
    assert.throws(() => validateLockfileObject(lockfile, manifest), /64 bytes/);
  });
});
