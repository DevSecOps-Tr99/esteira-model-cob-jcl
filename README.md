# esteira-model-cob-jcl

Repositório de **JCL** da POC `esteira-model-cob`. Aqui ficam só:

- os JCLs (`jcl/`), cada um como **modelo único**, com placeholders `${NOME}`
  onde o valor muda por ambiente;
- os valores por ambiente (`config/jcl_env_params.yml`);
- um **caller fino** (`.github/workflows/esteira.yml`) que chama o workflow
  reutilizável da esteira.

A lógica da esteira (gate, renderização, Key Vault, SSH) fica em
[`DevSecOps-Tr99/esteira-model-cob`](https://github.com/DevSecOps-Tr99/esteira-model-cob).
A infra (VMs, Key Vault, runner) fica em
[`DevSecOps-Tr99/esteira-model-cob-infra`](https://github.com/DevSecOps-Tr99/esteira-model-cob-infra).
Arquitetura e funcionamento completos:
[`docs/esteira-poc-como-funciona.md`](https://github.com/DevSecOps-Tr99/esteira-model-cob/blob/main/docs/esteira-poc-como-funciona.md).

| Repositório | Papel | Equivalente na esteira corporativa |
|---|---|---|
| **esteira-model-cob-jcl** (este) | JCL + parâmetros + caller | repositório da aplicação MFE |
| esteira-model-cob | motor + workflow reutilizável + regras | reusable workflows |
| esteira-model-cob-infra | Bicep + provisionamento | configurações e infraestrutura da plataforma |

## O que acontece em cada evento

| Evento | Resultado |
|---|---|
| Pull request | `validate`: gitleaks + Quality/Security Gate em todos os JCLs. Não publica |
| Push em `develop` | `validate` → publica em **TU** |
| Push em `release/*` | `validate` → publica em **TI** (pede aprovação) |
| Push em `main` / `hotfix/*` | `validate` → publica em **PRD** (pede aprovação) |
| Actions → *Esteira JCL* → *Run workflow* | seletor: escolhe TU, TI ou PRD e o JCL |

Na publicação, cada JCL vira um arquivo por ambiente
(`ESTMX001TU.jcl`, `ESTMX001TI.jcl`, `ESTMX001PRD.jcl`). O arquivo é gravado
no servidor de destino como membro da biblioteca do ambiente
(`ESTM.POC.<ENV>.JCLLIB(ESTMX001)`). O Job Summary do run mostra:
- o valor e a origem de cada placeholder;
- as versões dos segredos lidos no Key Vault;
- o login SSH no destino;
- o JOBID e o spool.

## Configuração do GitHub deste repositório

| Onde | O quê | Quem cria |
|---|---|---|
| Environments `TU`, `TI`, `PRD` | TI e PRD com required reviewers | `esteira-model-cob-infra/provisionar.ps1` |
| Variables do Environment | `JCL_<NOME>` para cada placeholder | `scripts/sincronizar-variables.py` (a partir do yml) |
| Variables do repositório | `GH_KV_DEV`, `DEPLOY_SERVERS_<ENV>`, `G_DEPLOYMENT_TARGET_*` | `provisionar.ps1` |
| Secret do repositório | `SPN_KV_DEV_SECRET` | `provisionar.ps1` |
| Runner self-hosted | `vm-estm-runner`, label `estm-runner` | `provisionar.ps1` |

## Adicionar ou alterar um JCL

1. Crie `jcl/<MEMBRO>.jcl` (membro de até 8 caracteres) e use `${NOME}` onde o
   valor muda por ambiente. Os datasets seguem `ESTM.<APP>.<ENV>.<RECURSO>`.
2. Coloque os valores de TU, TI e PRD em `config/jcl_env_params.yml`, num
   bloco `<MEMBRO>`.
3. Teste localmente:
   ```bash
   pip install -e "git+https://github.com/DevSecOps-Tr99/esteira-model-cob@main#egg=esteira-model-cob"
   # ou, com o repositório da esteira clonado ao lado: pip install -e ../esteira-model-cob
   export ESTM_JCL_ENV_PARAMS=config/jcl_env_params.yml     # PowerShell: $env:ESTM_JCL_ENV_PARAMS=...
   python -m esteira_model_cob validate jcl/ --env PRD
   python -m esteira_model_cob render jcl/ --env PRD --out build
   ```
4. Se criou ou mudou um valor, publique as variables:
   `python scripts/sincronizar-variables.py`.
5. Abra o PR para a `develop`. O gate roda no PR, e o merge publica em TU.

## Antes de uma demo

As VMs desligam às 22h. Ligue as duas antes de publicar:

```
az vm start -g rg-esteira-model-cob-poc -n vm-estm-runner
az vm start -g rg-esteira-model-cob-poc -n vm-estm-alvo
```
