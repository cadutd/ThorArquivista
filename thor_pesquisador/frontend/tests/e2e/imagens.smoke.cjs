const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || '@playwright/test');

const base = process.env.BASE_URL || 'http://localhost:3000';
const api = process.env.API_URL || 'http://localhost:8000/api/v1';
const unique = 'Smoke imagens ' + Date.now();

(async () => {
 const browser = await chromium.launch({headless:true});
 const context = await browser.newContext({viewport:{width:1440,height:900}});
 const page = await context.newPage();
 const errors = [];
 page.on('pageerror',e=>errors.push(e.message));
 const imageIds = [];
 let instrument;
 async function responseJson(response) {
  assert.ok(response.ok(), String(response.status()) + ': ' + await response.text());
  return response.json();
 }
 async function noErrors() {assert.deepEqual(await page.locator('.error').allTextContents(),[]);assert.deepEqual(errors,[]);}
 async function saveImage(endpoint='/imagens') {
  const response=page.waitForResponse(r=>r.url()===api+endpoint&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Salvar',exact:true}).click();
  const result=await responseJson(await response);
  imageIds.push(result.id);
  return result;
 }
 try {
  await page.goto(base+'/login');
  await page.getByRole('button',{name:'Entrar em desenvolvimento'}).click();
  await page.waitForURL('**/dashboard');
  instrument=await responseJson(await context.request.post(api+'/instrumentos',{data:{nome:unique,tipo:'CATALOGO'}}));
  const registro=await responseJson(await context.request.post(api+'/instrumentos/'+instrument.id+'/registros',{data:{dados:{},status:'ATIVO'}}));
  const registroUrl=base+'/instrumentos/'+instrument.id+'/registros/'+registro.id;
  const linkPrefix=api+'/instrumentos/'+instrument.id+'/registros/'+registro.id+'/imagens';
  let galleryRequests=0;
  page.on('request',r=>{if(r.url().startsWith(linkPrefix))galleryRequests++;});
  await page.goto(registroUrl);
  await page.getByRole('tab',{name:'Imagens'}).waitFor();
  assert.equal(galleryRequests,0,'A galeria deve carregar apenas ao abrir a aba');
  await page.getByRole('tab',{name:'Imagens'}).click();
  await page.getByText('Nenhuma imagem vinculada.').waitFor();
  await page.getByRole('link',{name:'Nova imagem'}).click();
  await page.getByLabel('Titulo *',{exact:true}).fill(unique+' upload');
  await page.getByLabel('Tipo de referencia *').selectOption('UPLOAD');
  await page.getByLabel('Direitos de acesso *').selectOption('RESTRITO');
  await page.locator('input[type=file]').setInputFiles(path.resolve(__dirname,'../../public/images/login_pesquisador.png'));
  await page.getByLabel('Metadados JSON').fill(JSON.stringify({fonte:'smoke'}));
  const uploaded=await saveImage('/imagens/upload');
  await page.waitForURL('**/registros/'+registro.id+'?aba=imagens');
  await page.locator('.image-tile img').waitFor();
  await page.waitForFunction(()=>document.querySelector('.image-tile img')?.naturalWidth>0);
  assert.equal(uploaded.metadados_json.fonte,'smoke');
  const anonymous = await browser.newContext();
  assert.equal((await anonymous.request.get(api+'/imagens/'+uploaded.id+'/conteudo')).status(),401);
  await anonymous.close();
  await page.locator('.thumbnail-button').click();
  await page.waitForFunction(()=>document.querySelector('dialog .media-large')?.naturalWidth>0);
  await page.screenshot({path:path.join(os.tmpdir(),'thor-fase3-preview.png')});
  await page.getByRole('button',{name:'Fechar',exact:true}).click();
  await page.getByLabel('Legenda',{exact:true}).fill('Documento de teste');
  await page.getByRole('button',{name:'Salvar legenda',exact:true}).click();
  await page.waitForTimeout(400);
  await page.getByRole('button',{name:'Marcar como principal'}).click();
  await page.waitForTimeout(400);
  assert.equal((await responseJson(await context.request.get(linkPrefix))).items[0].legenda,'Documento de teste');

  await page.goto(base+'/imagens/'+uploaded.id+'/editar');
  await page.getByLabel('Titulo *',{exact:true}).fill(unique+' atualizado');
  await page.getByRole('button',{name:'Salvar',exact:true}).click();
  await page.waitForURL('**/imagens');
  assert.equal((await responseJson(await context.request.get(api+'/imagens/'+uploaded.id))).titulo,unique+' atualizado');

  const media=api+'/imagens/'+uploaded.id+'/conteudo';
  for(const kind of ['URL','IIIF']) {
   await page.goto(base+'/imagens/novo');
   await page.getByLabel('Titulo *',{exact:true}).fill(unique+' '+kind);
   await page.getByLabel('Tipo de referencia *').selectOption(kind);
   await page.getByLabel(kind==='IIIF'?'Manifest IIIF *':'URL *',{exact:true}).fill(kind==='IIIF'?'https://iiif.example.org/manifest.json':media);
   await page.getByLabel('URL da miniatura').fill(api+'/imagens/'+uploaded.id+'/conteudo?thumbnail=true');
   const image=await saveImage();
   await page.waitForURL('**/imagens');
   await page.goto(registroUrl+'?aba=imagens');
   await page.getByRole('button',{name:'Vincular imagem',exact:true}).click();
   const dialog=page.getByRole('dialog',{name:'Selecionar imagem'});
   await dialog.getByLabel('Buscar imagem').fill(image.titulo);
   await dialog.getByRole('button',{name:'Buscar',exact:true}).click();
   await page.waitForTimeout(300);
   await dialog.getByRole('row').filter({hasText:image.titulo}).getByRole('button',{name:'Vincular imagem',exact:true}).click();
   await dialog.waitFor({state:'hidden'});
   await page.getByText(image.titulo,{exact:true}).waitFor();
  }
  await page.route('https://iiif.example.org/manifest.json',route=>route.fulfill({json:{items:[{items:[{items:[{body:{id:media}}]}]}]},headers:{'Access-Control-Allow-Origin':base}}));
  const iiifTile=page.locator('.image-tile').filter({hasText:unique+' IIIF'});
  await iiifTile.locator('.thumbnail-button').click();
  await page.waitForFunction(()=>document.querySelector('dialog .media-large')?.naturalWidth>0);
  await noErrors();
  await page.getByRole('button',{name:'Fechar',exact:true}).click();
  await page.locator('.image-tile').first().getByRole('button',{name:'Mover para direita'}).click();
  await page.waitForTimeout(500);
  const links=await responseJson(await context.request.get(linkPrefix));
  assert.equal(links.total,3);
  assert.notEqual(links.items[0].imagem_id,uploaded.id);
  let indexed;
  for(let attempt=0;attempt<30;attempt++){
   const results=await responseJson(await context.request.post(api+'/instrumentos/'+instrument.id+'/buscar-avancado',{data:{}}));
   indexed=results.items.find(item=>item.id===registro.id);
   if(indexed)break;
   await page.waitForTimeout(500);
  }
  assert.ok(indexed,'O worker deve indexar o registro no Meilisearch');
  assert.equal(indexed.possui_imagens,true);
  assert.equal(indexed.total_imagens,3);
  assert.ok(indexed.imagem_principal_thumbnail);
  for(const viewport of [{width:1440,height:900},{width:390,height:844}]){
   await page.setViewportSize(viewport);
   await page.screenshot({path:path.join(os.tmpdir(),'thor-fase3-galeria-'+viewport.width+'.png'),fullPage:true});
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Overflow na galeria');
  }
  const second=await responseJson(await context.request.post(api+'/instrumentos/'+instrument.id+'/registros',{data:{dados:{},status:'ATIVO'}}));
  assert.equal((await context.request.post(api+'/instrumentos/'+instrument.id+'/registros/'+second.id+'/imagens',{data:{imagem_id:uploaded.id}})).status(),201);
  assert.equal((await context.request.delete(api+'/imagens/'+uploaded.id)).status(),409);
  page.once('dialog',dialog=>dialog.accept());
  await page.locator('.image-tile').first().getByRole('button',{name:'Remover vinculo'}).click();
  await page.waitForTimeout(400);
  assert.equal((await responseJson(await context.request.get(linkPrefix))).total,2);
  await noErrors();
  console.log('PASS: upload S3 real, miniatura, original protegido, edicao, URL, IIIF, vinculos, legenda, capa, ordem, compartilhamento, busca real e desktop/mobile.');
 } finally {
  if(instrument) await context.request.delete(api+'/instrumentos/'+instrument.id);
  for(const id of imageIds){
   const response=await context.request.delete(api+'/imagens/'+id);
   assert.ok([204,404].includes(response.status()),'Falha na limpeza da imagem '+id);
  }
  await browser.close();
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
