const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || '@playwright/test');
const base = process.env.BASE_URL || 'http://localhost:3000';
const api = process.env.API_URL || 'http://localhost:8000/api/v1';

(async () => {
  const browser = await chromium.launch({headless: true});
  const context = await browser.newContext();
  const page = await context.newPage();
  let instrument;
  async function json(response) {
    assert.ok(response.ok(), await response.text());
    return response.json();
  }
  async function ready() {
    await page.getByRole('button', {name: 'Buscar', exact: true}).waitFor();
    await page.waitForFunction(() => document.querySelector('table')?.getAttribute('aria-busy') !== 'true');
  }
  async function submit(term, enter = false) {
    await page.getByPlaceholder('Busca simples').fill(term);
    const response = page.waitForResponse(r => r.url().includes('/instrumentos/' + instrument.id)
      && (term.trim() ? r.url().endsWith('/buscar') : r.url().includes('/registros?')));
    if (enter) await page.getByPlaceholder('Busca simples').press('Enter');
    else await page.getByRole('button', {name: 'Buscar', exact: true}).click();
    await json(await response);
    await ready();
  }
  try {
    await page.goto(base + '/login');
    await page.getByRole('button', {name: 'Entrar em desenvolvimento'}).click();
    await page.waitForURL('**/dashboard');
    instrument = await json(await context.request.post(api + '/instrumentos', {
      data: {nome: 'Smoke busca ' + Date.now(), tipo: 'CATALOGO'}
    }));
    const prefix = api + '/instrumentos/' + instrument.id;
    await json(await context.request.post(prefix + '/campos', {
      data: {nome: 'Titulo', chave: 'titulo', tipo: 'TEXTO_CURTO', aparece_busca: true}
    }));
    // Older non-matches must not leak into the next page of a filtered search.
    await json(await context.request.post(prefix + '/registros', {data: {dados: {titulo: 'Outro registro'}}}));
    for (let i = 0; i < 51; i++) {
      await json(await context.request.post(prefix + '/registros', {
        data: {dados: {titulo: 'Correspondencia ' + i}}
      }));
    }
    await page.goto(base + '/instrumentos/' + instrument.id + '/registros');
    await ready();
    await submit('  Correspondencia  ');
    assert.equal(await page.locator('tbody tr').count(), 50);
    // The draft is independent of the query already applied to the result set.
    await page.getByPlaceholder('Busca simples').fill('Outro');
    const next = page.waitForResponse(r => r.url().includes(prefix)
      && (r.url().endsWith('/buscar') || r.url().includes('/registros?')));
    await page.getByRole('button', {name: 'Carregar mais'}).click();
    const response = await next;
    assert.equal(response.request().method(), 'POST');
    assert.equal(response.request().postDataJSON().q, 'Correspondencia');
    assert.ok(response.request().postDataJSON().cursor);
    await json(response);
    await ready();
    assert.equal(await page.locator('tbody tr').count(), 51);
    assert.ok(!(await page.locator('tbody').innerText()).includes('Outro registro'));
    assert.equal(await page.getByRole('button', {name: 'Carregar mais'}).count(), 0);
    await submit('outro', true);
    assert.equal(await page.locator('tbody tr').count(), 1);
    assert.ok((await page.locator('tbody').innerText()).includes('Outro registro'));
    await submit('sem-correspondencia');
    await page.getByText('Nenhum registro encontrado.').waitFor();
    await submit('   ');
    assert.equal(await page.locator('tbody tr').count(), 50);
    const clearedPage = page.waitForResponse(r => r.url().startsWith(prefix + '/registros?'));
    await page.getByRole('button', {name: 'Carregar mais'}).click();
    await json(await clearedPage);
    await ready();
    assert.equal(await page.locator('tbody tr').count(), 52);
    assert.deepEqual(await page.locator('.error').allTextContents(), []);
    console.log('PASS: clique, Enter, termo aplicado, cursor filtrado, busca vazia, sem resultados e limpar busca.');
  } finally {
    if (instrument) await context.request.delete(api + '/instrumentos/' + instrument.id);
    await browser.close();
  }
})().catch(e => {console.error(e); process.exitCode = 1;});
