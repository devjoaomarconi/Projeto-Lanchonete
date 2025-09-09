import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import calendar
import sqlite3
import unittest

class Configuracao:
    def _init_(self):
        self.mostrar_adicionais = True
        self.mensagem_relatorio = "Relatório de Mensalidades"
        self.campos_relatorio = ["Nome do Cliente", "Data de Início", "Mensalidade Base"]

config = Configuracao()

class Cliente:
    DATE_FORMAT = '%d/%m/%Y'
    DAYS_IN_MONTH = 30

    def _init_(self, nome, data_inicio, vencimento, mensalidade_base, taxa_implantacao, parcelas_implantacao=3):
        self.nome = nome
        self.data_inicio = datetime.strptime(data_inicio, self.DATE_FORMAT)
        self.vencimento = int(vencimento)
        self.mensalidade_base = mensalidade_base
        self.taxa_implantacao = taxa_implantacao
        self.parcelas_implantacao = parcelas_implantacao
        self.implantacao_parcela = taxa_implantacao / parcelas_implantacao if parcelas_implantacao > 1 else 0
        self.mensalidades = []
        self.adicionais = []

    def adicionar_adicional(self, descricao, valor):
        self.adicionais.append((descricao, valor))

    def calcular_mensalidades(self):
        self.mensalidades.clear()
        primeiro_vencimento = self.data_inicio

        adicional_total = sum(valor for _, valor in self.adicionais)

        # Primeira mensalidade
        valor_primeira_mensalidade = self.mensalidade_base + adicional_total
        valor_primeira_implantacao = self.taxa_implantacao if self.parcelas_implantacao == 1 else self.implantacao_parcela
        descricao_primeira_implantacao = "implantação" if self.parcelas_implantacao == 1 else "Primeira parcela implantação"
        self._adicionar_mensalidade(primeiro_vencimento, primeiro_vencimento, valor_primeira_mensalidade, valor_primeira_implantacao, descricao_primeira_implantacao)

        # Ajustar para o próximo vencimento (10 ou 20)
        segundo_vencimento = self._ajustar_proximo_vencimento(primeiro_vencimento)

        # Verificar se o segundo vencimento cai no mesmo mês da primeira mensalidade
        if segundo_vencimento.month == primeiro_vencimento.month and segundo_vencimento.year == primeiro_vencimento.year:
            segundo_vencimento = self._proximo_vencimento(segundo_vencimento)

        # Ajustar o início do período da segunda mensalidade para o dia após o fim do período da primeira mensalidade
        inicio_segunda_mensalidade = primeiro_vencimento + timedelta(days=self.DAYS_IN_MONTH) + timedelta(days=1)

        # Segunda mensalidade proporcional
        dias_proporcionais = (segundo_vencimento - inicio_segunda_mensalidade).days
        if dias_proporcionais < 0:
            dias_proporcionais += self.DAYS_IN_MONTH
        valor_proporcional = (self.mensalidade_base / self.DAYS_IN_MONTH) * dias_proporcionais
        valor_segunda_mensalidade = self.mensalidade_base + adicional_total
        valor_segunda_implantacao = self.implantacao_parcela if self.parcelas_implantacao > 1 else 0
        descricao_segunda_mensalidade = f"Proporcional {dias_proporcionais} dias"
        descricao_segunda_implantacao = "Segunda parcela implantação" if self.parcelas_implantacao > 1 else ""
        self._adicionar_mensalidade(inicio_segunda_mensalidade, segundo_vencimento, valor_segunda_mensalidade, valor_segunda_implantacao, descricao_segunda_mensalidade, valor_proporcional, descricao_segunda_implantacao, incluir_proporcional=True)

        # Terceira mensalidade
        terceiro_vencimento = self._proximo_vencimento(segundo_vencimento)
        valor_terceira_mensalidade = self.mensalidade_base + adicional_total
        valor_terceira_implantacao = self.implantacao_parcela if self.parcelas_implantacao > 2 else 0
        descricao_terceira_implantacao = "Terceira parcela implantação" if self.parcelas_implantacao > 2 else ""
        self._adicionar_mensalidade(terceiro_vencimento, terceiro_vencimento, valor_terceira_mensalidade, valor_terceira_implantacao, descricao_terceira_implantacao)

        # Mensalidades após a terceira (sem taxa de implantação)
        ultimo_vencimento = terceiro_vencimento
        while ultimo_vencimento < datetime.now():
            ultimo_vencimento = self._proximo_vencimento(ultimo_vencimento)
            self._adicionar_mensalidade(ultimo_vencimento, ultimo_vencimento, self.mensalidade_base + adicional_total, 0, "Mensalidade")

    def _ajustar_proximo_vencimento(self, data):
        proximo_vencimento = data.replace(day=self.vencimento)
        if proximo_vencimento <= data:
            proximo_vencimento += timedelta(days=calendar.monthrange(proximo_vencimento.year, proximo_vencimento.month)[1])
        return proximo_vencimento

    def _proximo_vencimento(self, data):
        return (data.replace(day=1) + timedelta(days=32)).replace(day=self.vencimento)

    def _adicionar_mensalidade(self, inicio_periodo, vencimento, valor, valor_implantacao, observacao, valor_proporcional=0, descricao_adicional="", incluir_proporcional=False):
        data_fim = vencimento + timedelta(days=self.DAYS_IN_MONTH)
        descricao = self._gerar_descricao(valor, valor_implantacao, observacao, valor_proporcional, descricao_adicional, incluir_proporcional)
        self.mensalidades.append((inicio_periodo, vencimento, data_fim, valor, valor_implantacao, descricao, observacao))

    def _gerar_descricao(self, valor, valor_implantacao, observacao, valor_proporcional=0, descricao_adicional="", incluir_proporcional=False):
        descricao = f"R$ {valor:.2f}"
        if incluir_proporcional:
            descricao += f" + R$ {valor_proporcional:.2f} ({observacao})"
        else:
            if valor_proporcional > 0:
                descricao += f" + R$ {valor_proporcional:.2f} ({observacao})"
        if valor_implantacao > 0 and "implantação" in observacao:
            descricao += f" + R$ {valor_implantacao:.2f} ({observacao})"
        if descricao_adicional:
            descricao += f" + R$ {valor_implantacao:.2f} ({descricao_adicional})"
        return descricao

    def gerar_relatorio(self):
        relatorio = [config.mensagem_relatorio, f"Nome do Cliente: {self.nome}\n"]
        for i, (inicio_periodo, vencimento, data_fim, valor, valor_implantacao, descricao, observacao) in enumerate(self.mensalidades[:3]):
            periodo = f"{inicio_periodo.strftime(self.DATE_FORMAT)} até {data_fim.strftime(self.DATE_FORMAT)}"
            linha = (f"{i+1}ª Mensalidade - Venc. {vencimento.strftime(self.DATE_FORMAT)} (referente {periodo}): "
                     f"{descricao}")
            relatorio.append(linha)
        if len(self.mensalidades) > 3:
            relatorio.append(f"A partir da 4ª mensalidade: R$ {self.mensalidade_base:.2f} mensais")
        if config.mostrar_adicionais:
            adicionais_nf_boleto_assinatura = [ad for ad in self.adicionais if "NF" in ad[0] or "Boleto" in ad[0] or "Assinatura" in ad[0]]
            if adicionais_nf_boleto_assinatura:
                relatorio.append(f"Adicionais: {', '.join([f'{descricao} (R$ {valor:.2f})' for descricao, valor in adicionais_nf_boleto_assinatura])}")
        return relatorio

    def salvar_relatorio(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO relatorios (nome, data_inicio, relatorio)
            VALUES (?, ?, ?)
        ''', (self.nome, self.data_inicio.strftime(self.DATE_FORMAT), '\n'.join(self.gerar_relatorio())))
        conn.commit()

def mascarar_data(event):
    texto = entry_data_inicio.get()
    if len(texto) == 2 or len(texto) == 5:
        entry_data_inicio.insert(tk.END, "/")
    elif len(texto) > 10:
        entry_data_inicio.delete(10, tk.END)

def validar_entrada():
    try:
        if not entry_nome_cliente.get():
            raise ValueError("Nome do Cliente é obrigatório.")
        datetime.strptime(entry_data_inicio.get(), '%d/%m/%Y')
        if int(entry_vencimento.get()) not in [10, 20]:
            raise ValueError("Vencimento deve ser 10 ou 20.")
        float(entry_mensalidade_base.get())
        float(entry_taxa_implantacao.get())
        int(entry_parcelas_implantacao.get())
        return True
    except ValueError as e:
        messagebox.showerror("Erro de validação", str(e))
        return False

def calcular():
    if validar_entrada():
        try:
            nome_cliente = entry_nome_cliente.get()
            data_inicio = entry_data_inicio.get()
            vencimento = entry_vencimento.get()
            mensalidade_base = float(entry_mensalidade_base.get())
            taxa_implantacao = float(entry_taxa_implantacao.get())
            parcelas_implantacao = int(entry_parcelas_implantacao.get())
            cliente = Cliente(nome_cliente, data_inicio, vencimento, mensalidade_base, taxa_implantacao, parcelas_implantacao)

            nf_valor = float(entry_nf_valor.get() or 0)
            boleto_valor = float(entry_boleto_valor.get() or 0)
            assinatura_valor = float(entry_assinatura_valor.get() or 0)

            if nf_valor > 0:
                cliente.adicionar_adicional("NF", nf_valor)
            if boleto_valor > 0:
                cliente.adicionar_adicional("Boleto", boleto_valor)
            if assinatura_valor > 0:
                cliente.adicionar_adicional("Assinatura digital", assinatura_valor)

            cliente.calcular_mensalidades()
            relatorio = cliente.gerar_relatorio()

            text_relatorio.delete(1.0, tk.END)
            for linha in relatorio:
                text_relatorio.insert(tk.END, linha + "\n")

            # Salvar relatório no banco de dados
            cliente.salvar_relatorio(conn)

        except Exception as e:
            messagebox.showerror("Erro", str(e))

def criar_banco_de_dados():
    conn = sqlite3.connect('relatorios.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relatorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            data_inicio TEXT NOT NULL,
            relatorio TEXT NOT NULL
        )
    ''')
    conn.commit()
    return conn

def abrir_banco_de_dados():
    def fechar_janela():
        db_window.destroy()

    conn = sqlite3.connect('relatorios.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM relatorios')
    registros = cursor.fetchall()
    conn.close()

    db_window = tk.Toplevel(root)
    db_window.title("Banco de Dados")

    cols = ('ID', 'Nome', 'Data de Início', 'Relatório')
    tree = ttk.Treeview(db_window, columns=cols, show='headings')

    for col in cols:
        tree.heading(col, text=col)
        tree.grid(row=0, column=0, sticky='nsew')

    for registro in registros:
        tree.insert("", "end", values=registro)

    scrollbar = ttk.Scrollbar(db_window, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.grid(row=0, column=1, sticky='ns')

    button_fechar = ttk.Button(db_window, text="Fechar", command=fechar_janela)
    button_fechar.grid(row=1, column=0, columnspan=2)

def copiar_para_area_de_transferencia():
    root.clipboard_clear()
    root.clipboard_append('\n'.join(text_relatorio.get(1.0, tk.END).strip().split('\n')))
    messagebox.showinfo("Sucesso", "Relatório copiado para a área de transferência!")

def abrir_configuracoes():
    def salvar_configuracoes():
        config.mostrar_adicionais = var_mostrar_adicionais.get()
        config.mensagem_relatorio = entry_mensagem_relatorio.get()
        config.campos_relatorio = entry_campos_relatorio.get().split(',')
        config_window.destroy()

    config_window = tk.Toplevel(root)
    config_window.title("Configurações")
    
    tk.Label(config_window, text="Configurações do Relatório").pack(pady=10)
    
    var_mostrar_adicionais = tk.BooleanVar(value=config.mostrar_adicionais)
    tk.Checkbutton(config_window, text="Mostrar adicionais", variable=var_mostrar_adicionais).pack(pady=10)
    
    tk.Label(config_window, text="Mensagem do Relatório:").pack(pady=10)
    entry_mensagem_relatorio = tk.Entry(config_window)
    entry_mensagem_relatorio.insert(0, config.mensagem_relatorio)
    entry_mensagem_relatorio.pack(pady=10)
    
    tk.Label(config_window, text="Campos do Relatório (separados por vírgula):").pack(pady=10)
    entry_campos_relatorio = tk.Entry(config_window)
    entry_campos_relatorio.insert(0, ','.join(config.campos_relatorio))
    entry_campos_relatorio.pack(pady=10)
    
    tk.Button(config_window, text="Salvar", command=salvar_configuracoes).pack(pady=10)
    tk.Button(config_window, text="Fechar", command=config_window.destroy).pack(pady=10)

# Conectar ao banco de dados
conn = criar_banco_de_dados()

# Configurando a interface gráfica
root = tk.Tk()
root.title("Calculadora de Mensalidades")
root.geometry("850x600")  # Ajusta o tamanho da janela para acomodar o campo de observação à direita

# Estilo ttk
style = ttk.Style()
style.theme_use('clam')
style.configure('TLabel', background='#A9CCE3', foreground='#1B4F72', padding=6)
style.configure('TButton', background='#5499C7', foreground='#FFFFFF', padding=6)
style.configure('TEntry', padding=6)
style.configure('TFrame', background='#D6EAF8')

def criar_label_entry(root, texto, linha, coluna):
    ttk.Label(root, text=texto).grid(row=linha, column=coluna, padx=10, pady=10)
    entry = ttk.Entry(root)
    entry.grid(row=linha, column=coluna + 1, padx=10, pady=10)
    return entry

frame_principal = ttk.Frame(root)
frame_principal.grid(row=0, column=0, padx=10, pady=10, sticky='n')

entry_nome_cliente = criar_label_entry(frame_principal, "Nome do Cliente:", 0, 0)
entry_data_inicio = criar_label_entry(frame_principal, "Data de Início (dd/mm/yyyy):", 1, 0)
entry_data_inicio.bind("<KeyRelease>", mascarar_data)

entry_vencimento = criar_label_entry(frame_principal, "Vencimento (10 ou 20):", 2, 0)
entry_mensalidade_base = criar_label_entry(frame_principal, "Valor da Mensalidade:", 3, 0)
entry_taxa_implantacao = criar_label_entry(frame_principal, "Valor da Implantação:", 4, 0)
entry_parcelas_implantacao = criar_label_entry(frame_principal, "Parcelas da Implantação:", 5, 0)
entry_nf_valor = criar_label_entry(frame_principal, "Valor NF:", 6, 0)
entry_boleto_valor = criar_label_entry(frame_principal, "Valor Boleto:", 7, 0)
entry_assinatura_valor = criar_label_entry(frame_principal, "Valor Assinatura Digital:", 8, 0)

ttk.Button(frame_principal, text="Calcular", command=calcular).grid(row=9, column=0, columnspan=2, padx=10, pady=10)
ttk.Button(frame_principal, text="Copiar Relatório", command=copiar_para_area_de_transferencia).grid(row=10, column=0, columnspan=2, padx=10, pady=10)
ttk.Button(frame_principal, text="Abrir Banco de Dados", command=abrir_banco_de_dados).grid(row=11, column=0, columnspan=2, padx=10, pady=10)

# Novo frame para o relatório à direita
frame_relatorio = ttk.Frame(root)
frame_relatorio.grid(row=0, column=1, padx=10, pady=10, sticky='ne')

ttk.Label(frame_relatorio, text="Relatório:").grid(row=0, column=0, padx=10, pady=10, sticky='ne')
text_relatorio = tk.Text(frame_relatorio, width=50, height=28)
text_relatorio.grid(row=1, column=0, padx=10, pady=10, sticky='ne')

# Menu de Configurações
menu_bar = tk.Menu(root)
config_menu = tk.Menu(menu_bar, tearoff=0)
config_menu.add_command(label="Configurações", command=abrir_configuracoes)
menu_bar.add_cascade(label="Opções", menu=config_menu)
root.config(menu=menu_bar)

# Fechar a conexão ao banco de dados ao sair do programa
def on_closing():
    conn.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
