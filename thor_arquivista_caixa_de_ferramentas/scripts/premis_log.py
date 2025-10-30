#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
premis_log.py — Registra eventos PREMIS mínimos em JSONL.
"""
import argparse, json, uuid
from pathlib import Path
from pd_common import append_jsonl, iso_now, add_common_args, load_config

def main():
    ap = argparse.ArgumentParser(description="Adicionar evento PREMIS (JSONL).")
    ap.add_argument("--arquivo-log", required=True, help="Arquivo JSONL de eventos PREMIS.")
    ap.add_argument("--tipo", required=True, help="eventType (ex: ingestion, fixity check, format identification).")
    ap.add_argument("--obj-id", required=True, help="Identificador do objeto (ex: caminho relativo, URI).")
    ap.add_argument("--detalhe", default="", help="eventDetail (texto livre).")
    ap.add_argument("--resultado", default="success", help="outcome (success|failure|warning|...).")
    ap.add_argument("--agente", default="Sistema de Preservação", help="Agente responsável (nome).")
    add_common_args(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    evt = {
        "eventIdentifier": str(uuid.uuid4()),
        "eventType": args.tipo,
        "eventDateTime": iso_now(),
        "eventDetail": args.detalhe,
        "eventOutcome": args.resultado,
        "linkingObjectIdentifier": args.obj_id,
        "linkingAgentName": args.agente
    }
    append_jsonl(Path(args.arquivo_log), evt)
    print("Evento PREMIS registrado.")

if __name__ == "__main__":
    main()
