import { execFileSync } from 'node:child_process'
import { writeFileSync } from 'node:fs'
import openapiTS, { astToString } from 'openapi-typescript'
const python = process.platform === 'win32' ? '../.venv/Scripts/python.exe' : '../.venv/bin/python'
const schema = JSON.parse(execFileSync(python, ['-c', 'import sys,json;sys.path.insert(0,"..");from backend.main import app;print(json.dumps(app.openapi()))'], {encoding:'utf8'}))
writeFileSync('src/api.generated.ts', astToString(await openapiTS(schema)))
