# Deploy na Oracle Cloud Infrastructure (OCI)

Este documento descreve, passo a passo, como publicar o **NexaAI —
Assistente Corporativo** em uma **OCI Compute Instance**, tornando-o
acessível pela internet.

> ⚠️ Estas etapas dependem da sua conta OCI pessoal (login, criação de
> recursos, chaves SSH) e por isso **precisam ser executadas por você**.
> O código e a documentação abaixo já deixam tudo pronto para que o
> deploy seja apenas uma sequência de comandos.

---

## 1. Criar a Compute Instance

1. Acesse o [Console OCI](https://cloud.oracle.com/) e faça login.
2. No menu principal, vá em **Compute → Instances → Create Instance**.
3. Preencha:
   - **Name**: `nexaai-vm`
   - **Compartment**: o compartimento onde você deseja criar o recurso.
   - **Placement**: mantenha o domínio de disponibilidade padrão.
4. Em **Image and shape**:
   - **Image**: `Canonical Ubuntu 24.04` (recomendado — mesma base usada no Dockerfile).
   - **Shape**: `VM.Standard.E2.1.Micro` (elegível ao **Always Free**) ou outra shape compatível com seu orçamento.
5. Em **Networking**:
   - Utilize uma VCN existente ou crie uma nova com **subnet pública**.
   - Marque a opção para **atribuir um IP público** à instância.
6. Em **Add SSH keys**:
   - Faça upload da sua chave pública SSH (ou gere um novo par pelo próprio console e baixe a chave privada).
7. Clique em **Create**. Aguarde o status mudar para **Running**.
8. Anote o **IP público** exibido na página de detalhes da instância.

---

## 2. Configurar a rede (abrir a porta da aplicação)

Por padrão, a OCI bloqueia portas não essenciais. É preciso liberar a
porta **8501** (usada pelo Streamlit).

1. No console, acesse **Networking → Virtual Cloud Networks**.
2. Selecione a VCN usada pela instância → **Security Lists** (ou **Network Security Groups**, se estiver usando NSG).
3. Selecione a Security List da subnet pública.
4. Em **Ingress Rules**, clique em **Add Ingress Rules** e adicione:
   - **Source CIDR**: `0.0.0.0/0` (ou restrinja ao seu IP, se preferir mais segurança)
   - **IP Protocol**: TCP
   - **Destination Port Range**: `8501`
5. Salve a regra.

Além da regra da OCI, o firewall interno do Ubuntu (`iptables`/`ufw`)
também precisa permitir a porta, caso esteja ativo:

```bash
sudo ufw allow 8501/tcp
```

---

## 3. Acessar a instância via SSH

```bash
ssh -i /caminho/para/sua-chave-privada.pem ubuntu@SEU_IP_PUBLICO
```

---

## 4. Instalar dependências na VM

Escolha **uma** das duas opções abaixo (Docker é recomendado).

### Opção A — Com Docker (recomendado)

```bash
# Atualiza pacotes
sudo apt-get update -y

# Instala Docker
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Permite rodar docker sem sudo (efetivo após reconectar via SSH)
sudo usermod -aG docker $USER
```

### Opção B — Sem Docker (Python direto)

```bash
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip git
```

---

## 5. Copiar o projeto para a VM

Após o repositório estar publicado no GitHub (veja o `README.md`,
seção "GitHub"), clone-o diretamente na instância:

```bash
git clone https://github.com/SEU_USUARIO/nexaai-rag-agent.git
cd nexaai-rag-agent
```

Alternativamente, use `scp` para copiar os arquivos locais.

---

## 6. Configurar a API key na VM

```bash
cp .env.example .env
nano .env   # preencha GOOGLE_API_KEY=... com sua chave real
```

A chave **nunca** deve ser commitada no Git nem copiada para dentro da
imagem Docker — ela é lida em tempo de execução a partir do `.env`.

---

## 7. Indexar os documentos

### Com Docker

```bash
docker compose build
docker compose run --rm nexaai python ingest.py
```

### Sem Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python ingest.py
```

---

## 8. Executar a aplicação

### Com Docker

```bash
docker compose up -d
```

### Sem Docker

```bash
source .venv/bin/activate
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

Para manter a aplicação rodando após encerrar o SSH (sem Docker), use
`tmux`, `screen` ou configure um serviço `systemd`.

---

## 9. Verificar se está funcionando

Na própria VM:

```bash
curl http://localhost:8501/_stcore/health
```

Deve retornar `ok`.

---

## 10. Acessar pelo navegador

Abra em qualquer navegador:

```
http://SEU_IP_PUBLICO:8501
```

---

## 11. Cuidados básicos de segurança

- Nunca exponha o arquivo `.env` publicamente (ele já está no `.gitignore`).
- Restrinja a `Source CIDR` da regra de ingress ao seu IP, se o acesso público amplo não for necessário.
- Mantenha o sistema operacional da VM atualizado (`sudo apt-get update && sudo apt-get upgrade`).
- Considere configurar HTTPS (ex.: via um proxy reverso Nginx + Let's Encrypt) antes de divulgar a URL publicamente por tempo prolongado.
- Evite usar a chave `GOOGLE_API_KEY` de produção em ambientes de teste.

---

## Status do deploy neste projeto

> Este arquivo descreve o procedimento completo. A execução real destas
> etapas depende de credenciais da conta OCI do autor do projeto e será
> registrada no `README.md`, na seção **Demonstração**, assim que o
> deploy for realizado.
