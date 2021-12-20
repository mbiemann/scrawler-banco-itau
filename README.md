# Scrawler Banco Itaú
Extrator em Python de dados bancários do Banco Itaú pelo Internet Banking Desktop utilizando Selenium

Fazer download do geckodriver conforme seu sistema operacional:

https://github.com/mozilla/geckodriver/releases

```python

from scrawler_itau import ScrawlerItau, ExtratoTipo, CartaoFaturaTipo

# definir instancia do scrawler
scrawler = ScrawlerItau(
    agencia='9999', # número da agência
    conta='999999', # número da conta com o dígito sem hífen
    nome='FULANO', # nome igual exibido no botão
    senha='999999' # senha eletrônica de 6 dígitos (não é a senha do cartão)
)

# abrir navegador
scrawler.open('geckodriver') # utilizar geckodriver

# saldo
saldo = scrawler.get_saldo()
print(f'saldo atual = {saldo}\n')

# extrato (para mais opções ver ExtratoTipo)
extrato = scrawler.get_extrato(tipo=ExtratoTipo.Ultimos3dias)
print(f'list de lançamentos dos últimos 3 dias = {extrato}\n')

extrato = scrawler.get_extrato(tipo=ExtratoTipo.Ultimos60dias)
print(f'list de lançamentos dos últimos 60 dias = {extrato}\n')

extrato = scrawler.get_extrato(tipo=ExtratoTipo.MesCompleto,mes=1,ano=2021)
print(f'list de lançamentos do mês = {extrato}\n')

extrato = scrawler.get_extrato(tipo=ExtratoTipo.Futuro)
print(f'list de lançamentos futuros = {extrato}\n')

# cartões de créditos
cartoes = scrawler.list_cartoes()
print(f'list dos cartões de créditos = {cartoes}\n')

for cartao in cartoes:

    fatura = scrawler.get_cartao_fatura(cartao['name'])
    print(f'dict da fatura atual = {fatura}\n')

    fatura = scrawler.get_cartao_fatura(cartao['name'], tipo=CartaoFaturaTipo.Anterior)
    print(f'dict da fatura anterior = {fatura}\n')

    fatura = scrawler.get_cartao_fatura(cartao['name'], tipo=CartaoFaturaTipo.Proximas)
    print(f'list das próximas faturas = {fatura}\n')

# fechar navegador
scrawler.close()

```
