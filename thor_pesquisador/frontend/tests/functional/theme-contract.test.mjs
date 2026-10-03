import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

const theme = readFileSync(new URL("../../app/thor-theme.css", import.meta.url), "utf8");
const styles = readFileSync(new URL("../../app/globals.css", import.meta.url), "utf8");
const gestorTheme = new URL("../../../../thor_gestor_de_arquivos_digitais/frontend/app/thor-theme.css", import.meta.url);

test("tema base permanece identico ao Thor Gestor no monorepo", { skip: !existsSync(gestorTheme) }, () => {
  assert.equal(theme.replaceAll("\r\n", "\n"), readFileSync(gestorTheme, "utf8").replaceAll("\r\n", "\n"));
});

test("tema usa fonte de sistema, escala rem e paleta do Gestor", () => {
  assert.match(theme, /font-family: ui-sans-serif, system-ui/);
  assert.match(theme, /font-size: 16px/);
  assert.match(theme, /--primary: 204 82% 31%/);
  assert.match(styles, /@import "\.\/thor-theme\.css"/);
  assert.doesNotMatch(styles, /font-family: Arial|:root\s*\{/);
  assert.doesNotMatch(styles, /(?<!hsl\()var\(--/);
});

test("controles, tabelas e titulos usam a escala compacta do Gestor", () => {
  assert.match(styles, /\.table,\s*\.pagination,[\s\S]*?font-size: 14px;\s*line-height: 20px/);
  assert.match(styles, /\.page-heading h1 \{[^}]*font-size: 24px;\s*line-height: 32px/);
  assert.match(styles, /\.panel h2,[\s\S]*?font-size: 16px;\s*line-height: 24px/);
  assert.match(styles, /\.icon-button \{[^}]*width: 40px;\s*height: 40px/);
  assert.match(styles, /\.button:focus-visible/);
  assert.match(styles, /\.input:disabled/);
});
