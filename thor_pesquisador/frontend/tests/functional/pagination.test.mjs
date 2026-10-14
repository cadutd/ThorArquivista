import test from "node:test";
import assert from "node:assert/strict";
import { getPaginationItems } from "../../lib/pagination.mjs";

for(const [current,total,expected] of [
  [1,1,[1]],
  [4,7,[1,2,3,4,5,6,7]],
  [1,10,[1,2,"ellipsis",10]],
  [2,10,[1,2,3,"ellipsis",10]],
  [5,10,[1,"ellipsis",4,5,6,"ellipsis",10]],
  [9,10,[1,"ellipsis",8,9,10]],
  [10,10,[1,"ellipsis",9,10]],
]) {
  test("Unidades de Acondicionamento: pagina " + current + " de " + total, () => {
    assert.deepEqual(getPaginationItems(current,total),expected);
  });
}
