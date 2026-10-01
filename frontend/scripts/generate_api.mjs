import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import openapi_ts, { astToString as ast_to_string } from 'openapi-typescript';

const output_path = fileURLToPath(new URL('../src/api/generated.ts', import.meta.url));
const export_path = fileURLToPath(new URL('./export_openapi.py', import.meta.url));
const MAX_SCHEMA_BYTES = 10 * 1024 * 1024;
const schema = process.env.OPENAPI_URL
  ? await fetch(process.env.OPENAPI_URL).then(async (response) => {
      if (!response.ok) throw new Error(`OpenAPI HTTP ${response.status}`);
      return response.json();
    })
  : JSON.parse(
      execFileSync(process.env.PYTHON_BIN || 'python', [export_path], {
        maxBuffer: MAX_SCHEMA_BYTES,
        encoding: 'utf8',
      }),
    );
const generated =
  '// Сгенерировано из OpenAPI. Изменения вносятся через npm run api:generate.\n' +
  ast_to_string(await openapi_ts(schema));
if (process.argv.includes('--check')) {
  if (readFileSync(output_path, 'utf8') !== generated)
    throw new Error('Контракт изменился. Выполните npm run api:generate.');
} else {
  writeFileSync(output_path, generated);
}
