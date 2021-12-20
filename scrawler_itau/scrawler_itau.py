import datetime
import time
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

class ExtratoTipo(object):
    Futuro = 'futuro'
    Ultimos3dias = '3'
    Ultimos5dias = '5'
    Ultimos7dias = '7'
    Ultimos15dias = '15'
    Ultimos30dias = '30'
    Ultimos60dias = '60'
    Ultimos90dias = '90'
    MesCompleto = 'mesCompleto'

class CartaoFaturaTipo(object):
    Atual = 0
    Anterior = -1
    Proximas = 1

class MesAnoException(Exception):
    pass

class ScrawlerItau:

    _meses = {
        "jan": 1,
        "fev": 2,
        "mar": 3,
        "abr": 4,
        "mai": 5,
        "jun": 6,
        "jul": 7,
        "ago": 8,
        "set": 9,
        "out": 10,
        "nov": 11,
        "dez": 12
    }
    def __init__(self, agencia, conta, nome, senha):
        self._agencia = agencia
        self._conta = conta
        self._nome = nome
        self._senha = senha

    def open(self, driver_path):

        # abrir browser e acessar site
        self.s_driver = webdriver.Firefox(executable_path=driver_path)
        self.s_driver.get('http://www.itau.com.br')
        self.s_wait = WebDriverWait(self.s_driver,10)

        # inserir agência e conta
        time.sleep(3)
        s_elem = self.s_wait.until(EC.visibility_of_element_located((By.ID,'agencia')))
        s_elem.send_keys(self._agencia)
        s_elem = self.s_wait.until(EC.visibility_of_element_located((By.ID,'conta')))
        s_elem.send_keys(self._conta)
        s_elem.send_keys(Keys.RETURN)

        # escolher nome
        time.sleep(3)
        tries = 1
        click = False
        while not click:
            try:
                time.sleep(3)
                s_elem = self.s_wait.until(EC.visibility_of_element_located((By.LINK_TEXT,self._nome)))
                s_elem.click()
                click = True
            except Exception as e:
                if tries == 3:
                    raise e
                tries += 1

        # inserir senha
        time.sleep(4)
        for digito in self._senha:
            tries = 1
            click = False
            while not click:
                try:
                    time.sleep(random.randint(0,2))
                    s_elem = self.s_wait.until(EC.visibility_of_element_located((By.PARTIAL_LINK_TEXT,digito)))
                    s_elem.click()
                    click = True
                except Exception as e:
                    if tries == 3:
                        raise e
                    tries += 1
        s_elem = self.s_wait.until(EC.visibility_of_element_located((By.PARTIAL_LINK_TEXT,'acessar')))
        s_elem.click()

        # aguardar página carregar
        time.sleep(6)

    def go_home(self):

        # ir para página inicial
        time.sleep(3)
        s_elem = self.s_wait.until(EC.visibility_of_element_located((By.ID,'HomeLogo')))
        s_elem.click()

        # expandir Cartões, se necessário
        time.sleep(3)
        s_elem = self.s_wait.until(EC.visibility_of_element_located((By.ID,'cartao-card-accordion')))
        if s_elem.get_attribute('aria-expanded') == 'false':
            s_elem.click()

        # expandir Saldo e Extrato da Conta, se necessário
        time.sleep(3)
        s_elem = self.s_wait.until(EC.visibility_of_element_located((By.ID,'saldo-extrato-card-accordion')))
        if s_elem.get_attribute('aria-expanded') == 'false':
            s_elem.click()

    def get_saldo(self):
        self.go_home()

        s_elem = self.s_wait.until(EC.visibility_of_element_located((By.ID,'saldo')))
        saldo = s_elem.text.strip()
        saldo = saldo.replace('R$ ','')
        saldo = saldo.replace('.','')
        saldo = saldo.replace(',','.')
        saldo = float(saldo)

        return saldo

    def get_extrato(self, tipo, mes=0, ano=0):

        if tipo == ExtratoTipo.MesCompleto:
            if not (mes >= 1 and mes <= 12):
                raise MesAnoException('Parâmetros mes e/ou ano inválido(s).')
            if not (ano >= 1970 and ano <= datetime.date.today().year):
                raise MesAnoException('Parâmetros mes e/ou ano inválido(s).')
        else:
            if mes != 0 or ano != 0:
                raise MesAnoException('Utilizar mes e ano somente para "tipo=ExtratoTipo.MesCompleto".')

        self.go_home()

        base = []
        order = {}

        # abrir extrato
        s_elem = self.s_wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'btn-bank-statement')))
        s_elem.click()

        # definir período
        tries = 1
        selected = False
        while not selected:
            try:
                time.sleep(3)
                s_elem = self.s_wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'select__options')))
                Select(s_elem).select_by_value(ExtratoTipo.Ultimos3dias if tipo == ExtratoTipo.Futuro else tipo)
                selected = True
            except Exception as e:
                if tries == 3:
                    raise e
                tries += 1

        # Lançamentos Futuros
        if tipo == ExtratoTipo.Futuro:

            # clicar em lançamentos futuros
            time.sleep(3)
            s_elem = self.s_wait.until(EC.element_to_be_clickable((By.ID,'btn-aba-lancamentos-futuros')))
            s_elem.click()

            # extrair lançamentos futuros
            time.sleep(3)
            s_elem = self.s_wait.until(EC.presence_of_element_located((By.ID,'corpo-tabela-lancamentos-futuros'))) \
                .find_elements_by_class_name('table-extract__row')
            for s_elem_row in s_elem:
                s_elem_cols = s_elem_row.find_elements_by_tag_name('div')
                date = datetime.datetime.strptime(s_elem_cols[0].text.strip(),'%d/%m/%Y').strftime('%Y-%m-%d')
                name = s_elem_cols[1].text.strip()
                value = 0 - float(s_elem_cols[2].text.strip().replace('.','').replace(',','.'))
                order[date] = 1 + (order[date] if date in order else 0)
                base.append({
                    "date": date,
                    "order": order[date],
                    "name": name,
                    "value": value,
                    "executed": False,
                })

        # Extrato
        else:

            # filtrar período para mês completo
            if tipo == ExtratoTipo.MesCompleto:

                time.sleep(3)

                filter_date = datetime.date(ano, mes, 1)

                self.s_driver.execute_script('scrollBy(0,250);')

                s_elem = self.s_wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'month-picker__icon__icon')))
                s_elem.click()

                s_elem = self.s_wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'month-picker__input')))
                s_elem.clear()
                s_elem.send_keys(filter_date.strftime('%m')+filter_date.strftime('%Y'))

                s_elem = self.s_wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'month-picker__button')))
                s_elem.click()

            # extrair lançamentos
            time.sleep(3)
            s_elem = self.s_wait.until(EC.presence_of_element_located((By.ID,'extrato-grid-lancamentos')))
            for s_elem_row in s_elem.find_elements_by_tag_name('tr'):
                s_elem_cols = s_elem_row.find_elements_by_tag_name('td')
                if len(s_elem_cols) >= 3 and s_elem_cols[2].text.strip() != '':
                    date = datetime.datetime.strptime(s_elem_cols[0].text.strip(),'%d/%m/%Y').strftime('%Y-%m-%d')
                    name = s_elem_cols[1].text.strip()
                    value = float(s_elem_cols[2].text.strip().replace('.','').replace(',','.'))
                    order[date] = 1 + (order[date] if date in order else 0)
                    base.append({
                        "date": date,
                        "order": order[date],
                        "name": name,
                        "value": value,
                        "executed": True,
                    })

        return base

    def list_cartoes(self):

        self.go_home()

        base = []

        s_elem_rows = self.s_wait.until(EC.presence_of_element_located((By.ID,'content-cartao-card-accordion'))) \
            .find_element_by_class_name('content-cartoes') \
            .find_element_by_tag_name('table') \
            .find_element_by_tag_name('tbody') \
            .find_elements_by_tag_name('tr')
        for s_elem_row in s_elem_rows:
            s_elem_cols = s_elem_row.find_elements_by_tag_name('td')
            base.append({
                "name": s_elem_cols[0].find_element_by_class_name('card-name').text.strip(),
                "due_date": datetime.datetime.strptime(s_elem_cols[1].text.strip(),'%d/%m/%Y').strftime('%Y-%m-%d'),
                "value": float(s_elem_cols[2].text.strip().replace('.','').replace(',','.')),
                "status": s_elem_cols[3].text.strip()
            })

        return base

    def get_cartao_fatura(self, nome, tipo=CartaoFaturaTipo.Atual):
        self.go_home()

        base = []
        before = None

        # acessar cartão
        time.sleep(4)
        self.s_wait.until(EC.element_to_be_clickable((By.LINK_TEXT,nome))).click()

        # acessar fatura anterior
        if tipo == CartaoFaturaTipo.Anterior:
            time.sleep(4)
            self.s_wait.until(EC.presence_of_element_located((By.CLASS_NAME,'icon-itaufonts_seta'))).click()

        # acessar próxima fatura
        elif tipo == CartaoFaturaTipo.Proximas:
            time.sleep(2)
            tries = 1
            clicked = False
            while not clicked:
                try:
                    time.sleep(2)
                    self.s_wait.until(EC.presence_of_element_located((By.CLASS_NAME,'icon-itaufonts_seta_right'))).click()
                    clicked = True
                except Exception as e:
                    if tries == 3:
                        raise e
                    tries += 1
        
        # loop
        while True:
            time.sleep(4)

            items = []

            # vencimento fatura
            s_elem = self.s_wait.until(EC.presence_of_element_located((By.CLASS_NAME,'c-category-status__venc')))
            dates = s_elem.text.strip().replace('venc. ','').split('/')
            invoice_due_date = datetime.date(2000+int(dates[2]),int(dates[1]),int(dates[0]))

            # parar loop se fatura anterior for igual que fatura atual
            if (tipo == CartaoFaturaTipo.Proximas and 
                before != None and before == invoice_due_date):
                break

            # valor fatura
            s_elem = self.s_wait.until(EC.presence_of_element_located((By.CLASS_NAME,'c-category-status__total')))
            invoice_value = float(s_elem.text.strip().replace('R$','').replace('.','').replace(',','.'))

            for s_elem_type in self.s_wait.until(EC.presence_of_element_located(
                (By.CLASS_NAME,'lancamento'))).find_elements_by_xpath('./*'):

                try:
                    type_name = s_elem_type.find_element_by_tag_name('h3').text.strip()
                except:
                    break

                if type_name == 'lançamentos nacionais':

                    for s_elem_card in s_elem_type.find_elements_by_class_name('fatura__tipo'):

                        card_name = s_elem_card.find_element_by_tag_name('h4').text.strip()

                        order = {}

                        for s_elem_row in s_elem_card.find_elements_by_class_name('linha-valor-total'):

                            # columns
                            s_elem_cols = s_elem_row.find_elements_by_tag_name('td')
                            # date
                            dates = s_elem_cols[0].text.strip().split(' / ')
                            date = datetime.date(2021,self._meses[dates[1]],int(dates[0])).strftime('%Y-%m-%d')
                            # value
                            values = s_elem_cols[2].text.strip().split('\n')
                            value = -1 * float(
                                values[0 if len(values) == 1 else 1].replace('R$ ','').replace('.','').replace(',','.'))
                            # order
                            order[date] = 1 + (order[date] if date in order else 0)

                            # item
                            items.append({
                                "group": card_name,
                                "date": date,
                                "name": s_elem_cols[1].text.strip(),
                                "value": value,
                                "order": order[date]
                            })

                elif type_name == 'encargos e serviços':

                    order = {}

                    for s_elem_row in s_elem_type.find_element_by_tag_name('tbody').find_elements_by_tag_name('tr'):

                        # columns
                        s_elem_cols = s_elem_row.find_elements_by_tag_name('td')
                        # date
                        dates = s_elem_cols[0].text.strip().split(' / ')
                        date = datetime.date(2021,self._meses[dates[1]],int(dates[0])).strftime('%Y-%m-%d')
                        # value
                        values = s_elem_cols[2].text.strip().split('\n')
                        value = -1 * float(
                            values[0 if len(values) == 1 else 1].replace('R$ ','').replace('.','').replace(',','.'))
                        # order
                        order[date] = 1 + (order[date] if date in order else 0)

                        # item
                        items.append({
                            "group": type_name,
                            "date": date,
                            "name": s_elem_cols[1].text.strip(),
                            "value": value,
                            "order": order[date]
                        })

            base.append({
                "name": nome,
                "due_date": invoice_due_date.strftime('%Y-%m-%d'),
                "amount_value": invoice_value,
                "items": items
            })

            if tipo == CartaoFaturaTipo.Proximas:
                before = invoice_due_date
                self.s_wait.until(EC.presence_of_element_located((By.CLASS_NAME,'icon-itaufonts_seta_right'))).click()
            else:
                break

        if tipo == CartaoFaturaTipo.Proximas:
            return base
        else:
            return base[0]

    def close(self):
        self.s_driver.quit()
