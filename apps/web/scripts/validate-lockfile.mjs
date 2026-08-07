import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const EXACT_SEMVER_LITERAL = /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/;
const EXPECTED_REGISTRY_ORIGIN = 'https://registry.npmjs.org';

function fail(message) {
  throw new Error(message);
}

function isObject(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function sortedEntries(record) {
  return Object.entries(record).sort(([left], [right]) => left.localeCompare(right));
}

function readJson(jsonPath) {
  return JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
}

function getRootDependencyMap(manifest) {
  return {
    dependencies: manifest.dependencies ?? {},
    devDependencies: manifest.devDependencies ?? {},
  };
}

function assertExactSemverLiteral(sectionName, dependencyName, spec) {
  if (!EXACT_SEMVER_LITERAL.test(spec)) {
    fail(
      `${sectionName}.${dependencyName} must be an exact SemVer literal; received ${JSON.stringify(spec)}`,
    );
  }
}

function assertRootDependencyMap(manifest, lockfile) {
  const rootPackage = lockfile.packages?.[''];
  if (!isObject(rootPackage)) {
    fail('package-lock.json must contain a root package entry at packages[""]');
  }

  const manifestMaps = getRootDependencyMap(manifest);
  const lockfileMaps = {
    dependencies: rootPackage.dependencies ?? {},
    devDependencies: rootPackage.devDependencies ?? {},
  };

  for (const [sectionName, sectionDependencies] of sortedEntries(manifestMaps)) {
    if (!isObject(sectionDependencies)) {
      fail(`package.json ${sectionName} must be an object when present`);
    }
    for (const [dependencyName, spec] of sortedEntries(sectionDependencies)) {
      assertExactSemverLiteral(sectionName, dependencyName, spec);
    }
  }

  try {
    assert.deepStrictEqual(lockfileMaps, manifestMaps);
  } catch {
    fail('root dependency map drift between package.json and package-lock.json');
  }
}

function assertResolvedUrl(packagePath, resolved) {
  if (typeof resolved !== 'string' || resolved.length === 0) {
    fail(`${packagePath} must define a resolved tarball URL`);
  }
  if (resolved.startsWith('file:') || resolved.startsWith('git+') || resolved.startsWith('link:')) {
    fail(`${packagePath} must not use a link or local source`);
  }

  const parsedUrl = new URL(resolved);
  if (parsedUrl.protocol !== 'https:') {
    fail(`${packagePath} resolved URL must use https`);
  }
  if (parsedUrl.origin !== EXPECTED_REGISTRY_ORIGIN) {
    fail(`${packagePath} resolved URL must use ${EXPECTED_REGISTRY_ORIGIN}`);
  }
  if (parsedUrl.username || parsedUrl.password) {
    fail(`${packagePath} resolved URL must not include credentials`);
  }
  if (parsedUrl.port) {
    fail(`${packagePath} resolved URL must not include a port`);
  }
  if (parsedUrl.search || parsedUrl.hash) {
    fail(`${packagePath} resolved URL must not include query or fragment`);
  }
  if (!parsedUrl.pathname.endsWith('.tgz')) {
    fail(`${packagePath} resolved URL must point to a .tgz tarball`);
  }
}

function assertIntegrity(packagePath, integrity) {
  if (typeof integrity !== 'string' || integrity.length === 0) {
    fail(`${packagePath} must include integrity`);
  }
  if (!integrity.startsWith('sha512-')) {
    fail(`${packagePath} integrity must use sha512`);
  }

  const encodedDigest = integrity.slice('sha512-'.length);
  let digest;
  try {
    digest = Buffer.from(encodedDigest, 'base64');
  } catch {
    fail(`${packagePath} integrity must decode to 64 bytes`);
  }

  if (digest.length !== 64 || digest.toString('base64') !== encodedDigest) {
    fail(`${packagePath} integrity must decode to 64 bytes`);
  }
}

function assertFetchedPackages(lockfile) {
  const packages = lockfile.packages;
  if (!isObject(packages)) {
    fail('package-lock.json must contain a packages object');
  }

  for (const [packagePath, packageEntry] of sortedEntries(packages)) {
    if (packagePath === '') {
      continue;
    }
    if (!isObject(packageEntry)) {
      fail(`${packagePath} entry must be an object`);
    }
    if (packageEntry.link === true) {
      fail(`${packagePath} must not use a link or local source`);
    }

    assertResolvedUrl(packagePath, packageEntry.resolved);
    assertIntegrity(packagePath, packageEntry.integrity);
  }
}

export function validateLockfileObject(lockfile, manifest) {
  if (!isObject(lockfile)) {
    fail('package-lock.json must decode to an object');
  }
  if (!isObject(manifest)) {
    fail('package.json must decode to an object');
  }
  if (lockfile.lockfileVersion !== 3) {
    fail('lockfileVersion must be exactly 3');
  }

  assertRootDependencyMap(manifest, lockfile);
  assertFetchedPackages(lockfile);
}

export function validateLockfileFile(lockfilePath, manifestPath = path.join(path.dirname(lockfilePath), 'package.json')) {
  const lockfile = readJson(lockfilePath);
  const manifest = readJson(manifestPath);
  validateLockfileObject(lockfile, manifest);
}

function main(argv) {
  const lockfilePath = argv[2];
  if (!lockfilePath) {
    fail('usage: node scripts/validate-lockfile.mjs <package-lock.json>');
  }
  validateLockfileFile(path.resolve(lockfilePath));
}

if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    main(process.argv);
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
