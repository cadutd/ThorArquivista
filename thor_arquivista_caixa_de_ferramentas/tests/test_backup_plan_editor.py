from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ui.panels import backup_plan_editor as editor


class Var:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class Output:
    def __init__(self):
        self.text = ""

    def delete(self, *_):
        self.text = ""

    def insert(self, *args):
        self.text += str(args[-1])


class Tree:
    def __init__(self):
        self.rows = []

    def get_children(self):
        return list(range(len(self.rows)))

    def item(self, item, option=None, **kwargs):
        if "values" in kwargs:
            self.rows[item] = tuple(kwargs["values"])
            return None
        if option == "values":
            return self.rows[item]
        return {"values": self.rows[item]}

    def insert(self, _parent, _index, values):
        self.rows.append(tuple(values))
        return len(self.rows) - 1

    def delete(self, *items):
        if not items:
            return
        if len(items) == 1 and isinstance(items[0], (list, tuple)):
            items = tuple(items[0])
        for item in sorted(items, reverse=True):
            del self.rows[item]


class BackupPlanEditorTests(unittest.TestCase):
    def vars(self):
        return Var("plano"), Var("D:/Backup"), Var("sha256"), Var(1), Var(0), Tree(), Output(), Var("")

    def test_collect_plan_covers_screen_options(self):
        name, dest, algo, ignore_hidden, follow_symlinks, tree, _output, _status = self.vars()
        tree.insert("", "end", values=("docs", "D:/Acervo/Docs"))
        tree.insert("", "end", values=("imgs", "D:/Acervo/Imgs"))
        follow_symlinks.set(1)
        algo.set("sha512")

        plan = editor._collect_plan(name, dest, algo, ignore_hidden, follow_symlinks, tree)

        self.assertEqual(plan["name"], "plano")
        self.assertEqual(plan["destination"], "D:/Backup")
        self.assertEqual(plan["options"], {"algo": "sha512", "ignore_hidden": True, "follow_symlinks": True})
        self.assertEqual(plan["sources"], [{"name": "docs", "path": "D:/Acervo/Docs"}, {"name": "imgs", "path": "D:/Acervo/Imgs"}])

    def test_apply_plan_accepts_legacy_portuguese_keys(self):
        name, dest, algo, ignore_hidden, follow_symlinks, tree, _output, _status = self.vars()
        data = {
            "nome": "legado",
            "destino": "E:/Bag",
            "pastas": [{"nome": "origem", "raiz": "D:/Origem"}],
            "opcoes": {"algorithm": "sha512", "ignorar_ocultos": True, "seguir_symlinks": True},
        }

        editor._apply_plan(data, "legado.json", name, dest, algo, ignore_hidden, follow_symlinks, tree)

        self.assertEqual(name.get(), "legado")
        self.assertEqual(dest.get(), "E:/Bag")
        self.assertEqual(algo.get(), "sha512")
        self.assertEqual(ignore_hidden.get(), 1)
        self.assertEqual(follow_symlinks.get(), 1)
        self.assertEqual(tree.rows, [("origem", "D:/Origem")])

    def test_validate_editor_rejects_missing_required_fields(self):
        name, dest, algo, ignore_hidden, follow_symlinks, tree, output, status = self.vars()
        name.set("")
        dest.set("")

        with self.assertRaises(ValueError):
            editor._validate_editor(name, dest, algo, ignore_hidden, follow_symlinks, tree, output, status)

        self.assertIn("Informe o nome do backup", output.text)
        self.assertIn("Informe o destino BagIt", output.text)
        self.assertIn("Adicione pelo menos uma pasta", output.text)

    def test_validate_editor_rejects_duplicate_source_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            name, dest, algo, ignore_hidden, follow_symlinks, tree, output, status = self.vars()
            tree.insert("", "end", values=("origem", tmp))
            tree.insert("", "end", values=("origem", tmp))

            with self.assertRaises(ValueError):
                editor._validate_editor(name, dest, algo, ignore_hidden, follow_symlinks, tree, output, status)

            self.assertIn("Nome de origem duplicado", output.text)

    def test_save_plan_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            target = root / "plan.json"
            plan_path = Var(str(target))
            name, dest, algo, ignore_hidden, follow_symlinks, tree, output, status = self.vars()
            dest.set(str(root / "backup"))
            tree.insert("", "end", values=("origem", str(source)))

            with patch("ui.panels.backup_plan_editor.messagebox.showinfo"), patch("ui.panels.backup_plan_editor.messagebox.showerror"):
                ok = editor._save_plan(plan_path, name, dest, algo, ignore_hidden, follow_symlinks, tree, output, status, page=None, save_as=False)

            self.assertTrue(ok)
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(data["name"], "plano")
            self.assertEqual(data["sources"], [{"name": "origem", "path": str(source)}])


if __name__ == "__main__":
    unittest.main()
