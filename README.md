# ELO

Como Rodar?
```cmd
cd elo
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Como alternativa, execute `python executar.py` na raiz do projeto. O script usa
o ambiente virtual `.venv` quando ele existir; instale as dependências conforme
o comando acima antes de iniciar a aplicação.

Na primeira mensagem enviada, o backend baixa o modelo local
`Horizon-Labs/multilingual-toxicity-small` (checkpoint ONNX quantizado de cerca
de 268 MB e tokenizer de cerca de 34 MB), com os arquivos verificados por
SHA-256. As mensagens são avaliadas localmente; as que atingem o limiar de 0,5
(0,4 para ameaças e 0,3 para ataques a identidade, para compensar pontuações
mais baixas em idiomas diferentes do inglês) em uma ou mais categorias são
registradas em `log_mensagem_inadequada.txt` como JSON Lines. O arquivo fica na
raiz do servidor e não é incluído no Git. A classificação é probabilística,
sinaliza, mas não bloqueia, mensagens, e deve ser avaliada com exemplos reais
em português antes de ser usada como decisão automática. A categoria
`ataque_a_identidade` é ampla e não determina especificamente se o ataque é
racista ou misógino. O log guarda o texto integral da mensagem e deve ter acesso
restrito. Mensagens sinalizadas ficam ocultas para membros sem permissão até
serem avaliadas; administradores do grêmio podem avaliá-las, e a permissão
`AVALIAR_MENSAGENS` pode ser concedida a outros cargos.
