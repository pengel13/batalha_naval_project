# Batalha Naval P2P em Python (TCP + UDP + Pygame)

Este projeto implementa um jogo distribuído de **Batalha Naval** utilizando os conceitos de **Redes de Computadores**, incluindo:
- Comunicação via **UDP Broadcast**
- Comunicação direta via **TCP**
- Sincronização automática de participantes
- Interface gráfica utilizando **Pygame**
- Estrutura **peer-to-peer (P2P)**

Cada jogador mantém sua própria grade (10x10) e seus navios. Os peers descobrem automaticamente outros jogadores pela rede local, trocando mensagens e registrando participantes.

---

## 🎮 Funcionalidades

| Função | Protocolo | Porta | Descrição |
|-------|-----------|-------|------------|
| Descoberta de jogadores | UDP | 5000 | Broadcast inicial e notificações |
| Comunicação direta | TCP | 5001 | Respostas para tiros e intercâmbio da lista de jogadores |
| Ciclo de ataque automático | UDP | 5000 | Interface que conecta com o usuário  |

**Navios disponíveis:**

| Navio | Tamanho |
|------|---------|
| Porta-aviões | 5 |
| Bombardeiro | 4 |
| Submarino | 3 |
| Lancha militar | 2 |

---

## 📁 Estrutura do Projeto

```
batalha_naval_project/
│
├── jogo.py        # Interface gráfica + lógica principal do jogo
├── p2p_node.py                  # Responsável pelos servidores UDP e TCP (descoberta + mensagens de jogo)
└── grid.py                        # Responsável pelas funções de criação do grid e posicionamento dos navios
```

---

## 🧩 Requisitos

### **Python 3.8+**
---

## 🚀 Como Instalar e Executar

### 1. Baixe ou clone o repositório
```bash
git clone https://github.com/seu-usuario/batalha-p2p.git
cd batalha-p2p
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Execute o cliente
```bash
python jogo.py
```


### 4. Certifique-se de que todos os jogadores estão na **mesma rede local**

---

## 🕹 Como Jogar

- A interface exibe sua grade.
- O posicionamento dos navios pode ser automático ou manual.
- Ao acertar um tiro → é enviado **TCP: "hit"**.
- Quando um navio é destruído → é enviado **TCP: "destroyed"**.
- Se todos os navios forem destruídos → é enviado **UDP: "lost"**.
- Para sair → feche a janela → enviará **"saindo"** aos outros.

---

## 🏁 Finalização e Score

Ao sair, o cliente exibe:
- QJogadores únicos que você atingiu
- Quantas vezes foi atingido
- **Score final = jogadores acertados − vezes atingido**

---

