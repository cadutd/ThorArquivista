from __future__ import annotations

import unittest
from unittest.mock import patch

from ui.panels import backup_plan_editor
from ui.panels import preservation_backup


class FakeVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeText:
    def __init__(self, *args, **kwargs):
        self.text = ""

    def pack(self, *args, **kwargs):
        return None

    def grid(self, *args, **kwargs):
        return None

    def configure(self, *args, **kwargs):
        return None

    def yview(self, *args, **kwargs):
        return None

    def delete(self, *args, **kwargs):
        self.text = ""

    def insert(self, *args):
        self.text += str(args[-1])


class FakeWidget:
    registry: list["FakeWidget"] = []

    def __init__(self, kind="Widget", *args, **kwargs):
        self.kind = kind
        self.args = args
        self.kwargs = kwargs
        self.text = kwargs.get("text", "")
        self.command = kwargs.get("command")
        self.children = []
        self.rows = []
        FakeWidget.registry.append(self)

    def pack(self, *args, **kwargs):
        return None

    def grid(self, *args, **kwargs):
        return None

    def configure(self, *args, **kwargs):
        self.kwargs.update(kwargs)

    def grid_columnconfigure(self, *args, **kwargs):
        return None

    def columnconfigure(self, *args, **kwargs):
        return None

    def heading(self, *args, **kwargs):
        return None

    def column(self, *args, **kwargs):
        return None

    def yview(self, *args, **kwargs):
        return None

    def set(self, *args, **kwargs):
        return None

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

    def selection(self):
        return []

    def winfo_toplevel(self):
        return self

    def destroy(self):
        return None


class FakeTtk:
    @staticmethod
    def Frame(*args, **kwargs):
        return FakeWidget("Frame", *args, **kwargs)

    @staticmethod
    def LabelFrame(*args, **kwargs):
        return FakeWidget("LabelFrame", *args, **kwargs)

    @staticmethod
    def Button(*args, **kwargs):
        return FakeWidget("Button", *args, **kwargs)

    @staticmethod
    def Label(*args, **kwargs):
        return FakeWidget("Label", *args, **kwargs)

    @staticmethod
    def Entry(*args, **kwargs):
        return FakeWidget("Entry", *args, **kwargs)

    @staticmethod
    def Combobox(*args, **kwargs):
        return FakeWidget("Combobox", *args, **kwargs)

    @staticmethod
    def Checkbutton(*args, **kwargs):
        return FakeWidget("Checkbutton", *args, **kwargs)

    @staticmethod
    def Treeview(*args, **kwargs):
        return FakeWidget("Treeview", *args, **kwargs)

    @staticmethod
    def Scrollbar(*args, **kwargs):
        return FakeWidget("Scrollbar", *args, **kwargs)


class FakeNotebook(FakeWidget):
    def forget(self, page):
        return None


class FakeApp:
    def __init__(self):
        self._main_nb = FakeNotebook("Notebook")


def button_texts():
    return [w.text for w in FakeWidget.registry if w.kind == "Button"]


def label_texts():
    return [w.text for w in FakeWidget.registry if w.kind in {"Label", "LabelFrame"}]


class BackupGuiTests(unittest.TestCase):
    def setUp(self):
        FakeWidget.registry = []

    def test_preservation_backup_operational_screen_exposes_all_actions(self):
        with (
            patch.object(preservation_backup, "ttk", FakeTtk),
            patch.object(preservation_backup, "StringVar", FakeVar),
            patch.object(preservation_backup, "Text", FakeText),
        ):
            page = preservation_backup.create_panel(FakeApp(), lambda *_: None)

        self.assertIsInstance(page, FakeWidget)
        texts = button_texts()
        for expected in [
            "Abrir...",
            "Selecionar...",
            "Validar plano",
            "Executar",
            "Retomar",
            "Pausar com STOP",
            "Verificar integridade",
            "Histórico",
            "Fechar aba",
        ]:
            self.assertIn(expected, texts)
        for expected in ["Plano JSON", "Destino BagIt", "Backup"]:
            self.assertIn(expected, label_texts())

    def test_backup_plan_editor_screen_exposes_json_editing_controls(self):
        with (
            patch.object(backup_plan_editor, "ttk", FakeTtk),
            patch.object(backup_plan_editor, "StringVar", FakeVar),
            patch.object(backup_plan_editor, "IntVar", FakeVar),
            patch.object(backup_plan_editor, "Text", FakeText),
        ):
            page = backup_plan_editor.create_panel(FakeApp(), lambda *_: None)

        self.assertIsInstance(page, FakeWidget)
        texts = button_texts()
        for expected in [
            "Novo",
            "Abrir...",
            "Salvar",
            "Salvar como...",
            "Selecionar...",
            "Adicionar pasta",
            "Editar",
            "Remover",
            "Pré-visualizar JSON",
            "Validar plano",
            "Fechar aba",
        ]:
            self.assertIn(expected, texts)
        for expected in ["Nome do backup", "Destino BagIt", "Algoritmo", "Origens"]:
            self.assertIn(expected, label_texts())

    def test_backup_plan_editor_builds_treeview_for_sources(self):
        with (
            patch.object(backup_plan_editor, "ttk", FakeTtk),
            patch.object(backup_plan_editor, "StringVar", FakeVar),
            patch.object(backup_plan_editor, "IntVar", FakeVar),
            patch.object(backup_plan_editor, "Text", FakeText),
        ):
            backup_plan_editor.create_panel(FakeApp(), lambda *_: None)

        treeviews = [w for w in FakeWidget.registry if w.kind == "Treeview"]
        self.assertEqual(len(treeviews), 1)
        self.assertEqual(treeviews[0].kwargs.get("columns"), ("name", "path"))


if __name__ == "__main__":
    unittest.main()
