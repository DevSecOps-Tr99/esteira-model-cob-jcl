"""Publica config/jcl_env_params.yml como GitHub variables JCL_<NOME> em
cada Environment (TU/TI/PRD) deste repositorio.

Uso (gh logado, com permissao de admin no repositorio):
    pip install pyyaml
    python scripts/sincronizar-variables.py [--repo OWNER/REPO] [--dry-run]

Com varios membros (jobs) no yml, o mesmo placeholder precisa ter o mesmo
valor em todos eles - a variable do Environment vale para o repositorio
inteiro. Conflitos sao reportados e nada e gravado.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AMBIENTES = ("TU", "TI", "PRD")


def coletar(config: dict) -> dict[str, dict[str, str]]:
    por_ambiente: dict[str, dict[str, str]] = {amb: {} for amb in AMBIENTES}
    conflitos: list[str] = []
    for membro, ambientes in config.items():
        for amb in AMBIENTES:
            for nome, valor in (ambientes.get(amb) or {}).items():
                valor = str(valor)
                atual = por_ambiente[amb].get(nome)
                if atual is not None and atual != valor:
                    conflitos.append(f"{amb}/{nome}: '{atual}' x '{valor}' ({membro})")
                por_ambiente[amb][nome] = valor
    if conflitos:
        sys.exit("Valores conflitantes para a mesma variable:\n  " + "\n  ".join(conflitos))
    return por_ambiente


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="DevSecOps-Tr99/esteira-model-cob-jcl")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = yaml.safe_load((ROOT / "config" / "jcl_env_params.yml").read_text(encoding="utf-8")) or {}
    gh = shutil.which("gh") or "gh"

    for amb, valores in coletar(config).items():
        for nome, valor in sorted(valores.items()):
            print(f"{amb:<4} JCL_{nome:<16} = {valor}")
            if not args.dry_run:
                subprocess.run(
                    [gh, "variable", "set", f"JCL_{nome}", "--repo", args.repo, "--env", amb, "--body", valor],
                    check=True,
                    stdout=subprocess.DEVNULL,
                )


if __name__ == "__main__":
    main()
