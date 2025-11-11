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
| Ciclo de ataque automático | UDP | 5000 | A cada 10 segundos um tiro é enviado |

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
batalha_p2p/
│
├── client.py        # Interface gráfica + lógica principal do jogo
├── udp_server.py    # Servidor UDP (descoberta + mensagens de jogo)
├── tcp_server.py    # Servidor TCP (respostas de hit/destroyed/listas)
└── grid.py          # Representação da grid e posicionamento dos navios
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
python client.py
```

### 4. Certifique-se de que todos os jogadores estão na **mesma rede local**

---

## 🕹 Como Jogar

- A interface exibe sua grade.
- O posicionamento dos navios pode ser automático ou manual (dependendo da implementação).
- O jogo envia tiros automaticamente a cada 10 segundos.
- Ao acertar um tiro → é enviado **TCP: "hit"**.
- Quando um navio é destruído → é enviado **TCP: "destroyed"**.
- Se todos os navios forem destruídos → é enviado **UDP: "lost"**.
- Para sair → pressione **Q** ou feche a janela → enviará **"saindo"** aos outros.

---

## 🏁 Finalização e Score

Ao sair, o cliente exibe:
- Quantos jogadores você acertou
- Quantas vezes foi atingido
- **Score final = jogadores acertados − vezes atingido**

---

