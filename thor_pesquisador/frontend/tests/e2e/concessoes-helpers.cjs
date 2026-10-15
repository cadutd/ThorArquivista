async function selecionarPerfil(page, code) {
  const group = page.getByRole("group",{name:"Pesquisa de perfis",exact:true});
  await group.getByLabel("Perfil",{exact:true}).fill(code);
  await group.getByRole("button",{name:"Buscar perfis",exact:true}).click();
  await group.getByRole("row").filter({hasText:code}).getByRole("checkbox").check();
}
async function selecionarInstrumento(page, instrument) {
  await page.getByRole("radio",{name:"Por instrumento",exact:true}).check();
  const group = page.getByRole("group",{name:"Pesquisa de instrumentos",exact:true});
  await group.getByLabel("Nome",{exact:true}).fill(instrument.nome);
  await group.getByRole("button",{name:"Buscar instrumentos",exact:true}).click();
  await group.getByRole("row").filter({hasText:instrument.nome}).getByRole("checkbox").check();
}
module.exports = {selecionarPerfil,selecionarInstrumento};
