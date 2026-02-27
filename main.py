import customtkinter as ctk
from PIL import Image
import json
import os
from tkinter import messagebox

# =========================
# CONFIG VISUAL
# =========================
ctk.set_appearance_mode("dark")

COLOR_BG = "#0A0A0A"
COLOR_GOLD = "#BF9B30"
COLOR_SANGUE = "#8B0000"
COLOR_MORTE = "#4B0082"
COLOR_ENERGIA = "#00AAAA"
COLOR_CONHECIMENTO = "#BF9B30"
COLOR_FISICO = "#555555"
COLOR_PANEL = "#111111"
COLOR_ENTRY = "#161616"

FONT_TITLE = ("Cinzel", 28, "bold")
FONT_SUB = ("Cinzel", 20, "bold")
FONT_TEXT = ("Cinzel", 14)

# =========================
# CLASSE CRIATURA
# =========================
class Criatura:
    def __init__(self, nome, pv_max, elemento, rds=None):
        self.nome = nome
        self.pv_max = int(pv_max)
        self.pv_atual = int(pv_max)
        self.elemento = elemento
        self.rds = rds if rds else {}

    def calcular_dano(self, valor, tipo, status_vulneravel=False):
        # Mapeamento do ciclo de elementos: Quem sofre < Para quem (A Fraqueza)
        fraquezas = {
            "Sangue": "Morte",
            "Morte": "Energia",
            "Energia": "Conhecimento",
            "Conhecimento": "Sangue"
        }

        dano_final = valor
        msg = ""
        
        # Puxa a RD específica do tipo de ataque (se não existir, é 0)
        rd_efetiva = int(self.rds.get(tipo, 0))

        # 1. FRAQUEZA ELEMENTAL (Dano dobra e ignora RD)
        if tipo == fraquezas.get(self.elemento):
            dano_final = valor * 2
            rd_efetiva = 0 
            msg = "⚡ FRAQUEZA ELEMENTAL! (RD Ignorada)"
            
        # 2. RESISTÊNCIA ELEMENTAL (Dano cai pela metade)
        elif tipo == self.elemento:
            dano_final = valor // 2
            msg = "🛡️ RESISTÊNCIA ELEMENTAL."

        # 3. STATUS VULNERÁVEL (Corta a RD pela metade, se ainda houver RD)
        if status_vulneravel:
            if rd_efetiva > 0:
                rd_efetiva = rd_efetiva // 2
            msg += " | ⚠️ ALVO VULNERÁVEL"

        # 4. APLICAÇÃO DA REDUÇÃO DE DANO (RD Específica)
        dano_final = max(0, dano_final - rd_efetiva)

        self.pv_atual = max(0, self.pv_atual - dano_final)
        return dano_final, msg


# =========================
# APP PRINCIPAL
# =========================
class OrdoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ORDO ALVARUS - Master Dashboard")
        self.geometry("1300x780")
        self.configure(fg_color=COLOR_BG)

        self.arquivo_dados = "bestiario.json"
        self.bestiario = self.carregar_dados()
        self.inimigo_atual = None
        self.lista_iniciativa = []

        self.setup_ui()

    # =========================
    def carregar_dados(self):
        if os.path.exists(self.arquivo_dados):
            with open(self.arquivo_dados, "r") as f:
                return json.load(f)
        return {}

    # =========================
    def criar_input(self, parent, placeholder):
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            fg_color=COLOR_ENTRY,
            border_color=COLOR_GOLD,
            corner_radius=10
        )
        entry.pack(pady=6, padx=15, fill="x")
        return entry

    # =========================
    def criar_botao(self, parent, texto, comando, cor):
        btn = ctk.CTkButton(
            parent,
            text=texto,
            command=comando,
            fg_color=cor,
            hover_color="#AA0000",
            corner_radius=12,
            height=45,
            border_width=1,
            border_color=COLOR_GOLD,
            font=FONT_TEXT
        )
        btn.pack(pady=10, padx=15, fill="x")
        return btn

    # =========================
    def setup_ui(self):

        # ===== SIDEBAR BESTIÁRIO =====
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=COLOR_PANEL,
            border_color=COLOR_GOLD,
            border_width=2,
            corner_radius=15
        )
        self.sidebar.place(relx=0.02, rely=0.03, relwidth=0.24, relheight=0.94)

        ctk.CTkLabel(
            self.sidebar,
            text="☣ BESTIÁRIO",
            font=FONT_SUB,
            text_color=COLOR_SANGUE
        ).pack(pady=15)

        self.combo_selecao = ctk.CTkComboBox(
            self.sidebar,
            values=list(self.bestiario.keys()) if self.bestiario else ["Vazio"],
            command=self.carregar_monstro
        )
        self.combo_selecao.pack(pady=5, padx=15, fill="x")

        self.ent_nome = self.criar_input(self.sidebar, "Nome")
        self.ent_pv = self.criar_input(self.sidebar, "PV Máximo")
        
        # Combo de Elemento Base
        self.combo_elem = ctk.CTkComboBox(
            self.sidebar,
            values=["Sangue", "Morte", "Energia", "Conhecimento", "Físico"]
        )
        self.combo_elem.pack(pady=5, padx=15, fill="x")

        # --- GRID DE REDUÇÃO DE DANO (RD) ---
        ctk.CTkLabel(self.sidebar, text="REDUÇÕES DE DANO (RD)", font=FONT_TEXT, text_color=COLOR_GOLD).pack(pady=(10, 0))
        
        self.frame_rds = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_rds.pack(pady=5, padx=15, fill="x")

        tipos_dano = ["Impacto", "Corte", "Perfuração", "Balístico", "Sangue", "Morte", "Conhecimento", "Energia"]
        self.entradas_rd = {}

        for i, tipo in enumerate(tipos_dano):
            row = i // 2
            col = i % 2
            # Usa abreviações se o nome for muito longo
            nome_display = tipo[:6] + "." if len(tipo) > 9 else tipo
            
            ent = ctk.CTkEntry(
                self.frame_rds, 
                placeholder_text=f"{nome_display}", 
                width=110,
                fg_color=COLOR_ENTRY, 
                border_color="#333", 
                corner_radius=5
            )
            ent.grid(row=row, column=col, padx=5, pady=5)
            self.entradas_rd[tipo] = ent

        self.criar_botao(
            self.sidebar,
            "SALVAR ENTIDADE",
            self.adicionar_bestiario,
            COLOR_SANGUE
        )

        # ===== CENTRAL COMBATE =====
        self.main = ctk.CTkFrame(
            self,
            fg_color=COLOR_PANEL,
            border_color="#333",
            border_width=1,
            corner_radius=20
        )
        self.main.place(relx=0.28, rely=0.03, relwidth=0.44, relheight=0.94)

        self.lbl_nome = ctk.CTkLabel(
            self.main,
            text="AGUARDANDO CHAMADO",
            font=FONT_TITLE,
            text_color=COLOR_GOLD
        )
        self.lbl_nome.pack(pady=25)

        self.barra_pv = ctk.CTkProgressBar(
            self.main,
            width=520,
            height=35,
            corner_radius=20,
            progress_color=COLOR_SANGUE,
            fg_color="#1A1A1A",
            border_width=1,
            border_color=COLOR_GOLD
        )
        self.barra_pv.set(0)
        self.barra_pv.pack(pady=10)

        self.lbl_pv_status = ctk.CTkLabel(
            self.main,
            text="PV: -- / --",
            font=FONT_TEXT
        )
        self.lbl_pv_status.pack(pady=5)

        # Ações
        self.action_frame = ctk.CTkFrame(
            self.main,
            fg_color="#141414",
            border_color="#333",
            border_width=1,
            corner_radius=15
        )
        self.action_frame.pack(pady=20, padx=25, fill="x")

        self.check_vulneravel = ctk.CTkCheckBox(
            self.action_frame,
            text="VULNERÁVEL",
            text_color="#FF4444",
            font=FONT_TEXT
        )
        self.check_vulneravel.grid(row=0, column=0, padx=15, pady=20)

        self.ent_dano = ctk.CTkEntry(
            self.action_frame,
            placeholder_text="VALOR",
            width=90
        )
        self.ent_dano.grid(row=0, column=1, padx=10)

        self.combo_tipo = ctk.CTkComboBox(
            self.action_frame,
            values=["Impacto", "Corte", "Perfuração", "Balístico", "Sangue", "Morte", "Energia", "Conhecimento"],
            width=150
        )
        self.combo_tipo.grid(row=0, column=2, padx=10)

        self.criar_botao(
            self.main,
            "EFETUAR GOLPE",
            self.atacar,
            COLOR_SANGUE
        )

        self.log = ctk.CTkTextbox(
            self.main,
            height=260,
            fg_color="#0B0B0B",
            border_color=COLOR_GOLD,
            border_width=1,
            corner_radius=15,
            font=FONT_TEXT,
            text_color="#E0C878"
        )
        self.log.pack(pady=15, padx=20, fill="both", expand=True)

        # ===== INICIATIVA =====
        self.ini_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_PANEL,
            border_color=COLOR_GOLD,
            border_width=2,
            corner_radius=15
        )
        self.ini_frame.place(relx=0.74, rely=0.03, relwidth=0.24, relheight=0.94)

        ctk.CTkLabel(
            self.ini_frame,
            text="⌛ INICIATIVA",
            font=FONT_SUB,
            text_color=COLOR_GOLD
        ).pack(pady=20)

        self.ent_ini_n = self.criar_input(self.ini_frame, "Nome")
        self.ent_ini_v = self.criar_input(self.ini_frame, "Valor")

        self.criar_botao(
            self.ini_frame,
            "ADICIONAR",
            self.add_ini,
            "#333333"
        )

        self.criar_botao(
            self.ini_frame,
            "LIMPAR",
            self.clear_ini,
            "#222222"
        )

        self.txt_ini = ctk.CTkTextbox(
            self.ini_frame,
            fg_color="#000000",
            text_color=COLOR_GOLD,
            font=FONT_TEXT
        )
        self.txt_ini.pack(pady=15, padx=15, fill="both", expand=True)

    # =========================
    def carregar_monstro(self, nome):
        if nome in self.bestiario:
            d = self.bestiario[nome]
            
            # Pega as RDs do JSON (se for um save antigo, garante que não quebre)
            rds_salvas = d.get('rds', {})
            
            self.inimigo_atual = Criatura(
                nome, d['pv'], d['elemento'], rds_salvas
            )

            # Atualiza visualmente os campos de RD para o mestre ver
            for tipo, ent in self.entradas_rd.items():
                ent.delete(0, 'end')
                valor_rd = rds_salvas.get(tipo, 0)
                if valor_rd > 0:
                    ent.insert(0, str(valor_rd))

            cores = {
                "Sangue": COLOR_SANGUE,
                "Morte": COLOR_MORTE,
                "Energia": COLOR_ENERGIA,
                "Conhecimento": COLOR_CONHECIMENTO,
                "Físico": COLOR_FISICO
            }

            cor_atual = cores.get(d['elemento'], COLOR_SANGUE)

            self.lbl_nome.configure(
                text=nome.upper(),
                text_color=cor_atual
            )

            self.barra_pv.configure(
                progress_color=cor_atual
            )

            self.barra_pv.set(1.0)
            self.lbl_pv_status.configure(
                text=f"PV: {d['pv']} / {d['pv']}"
            )

            self.log.insert(
                "end",
                f"\n[SISTEMA] Entidade de {d['elemento']} manifestada.\n"
            )

    # =========================
    def atacar(self):
        if not self.inimigo_atual:
            return

        try:
            val = int(self.ent_dano.get())
            tipo = self.combo_tipo.get()

            dano, msg = self.inimigo_atual.calcular_dano(
                val, tipo, self.check_vulneravel.get()
            )

            self.barra_pv.set(
                self.inimigo_atual.pv_atual /
                self.inimigo_atual.pv_max
            )

            self.lbl_pv_status.configure(
                text=f"PV: {self.inimigo_atual.pv_atual} / {self.inimigo_atual.pv_max}"
            )

            self.log.insert(
                "end",
                f">> {dano} dano [{tipo}] {msg}\n"
            )

            if self.inimigo_atual.pv_atual <= 0:
                self.lbl_nome.configure(
                    text="✖ ALVO ELIMINADO ✖",
                    text_color="#8B0000"
                )
                self.log.insert(
                    "end",
                    "\n[!] PROTOCOLO DE EXPURGO CONCLUÍDO.\n"
                )

            self.log.see("end")

        except ValueError:
            pass

    # =========================
    def adicionar_bestiario(self):
        n = self.ent_nome.get()
        p = self.ent_pv.get()

        if n and p.isdigit():
            # Coleta todos os valores da grid de RDs
            rds_atuais = {}
            for tipo, ent in self.entradas_rd.items():
                val = ent.get()
                rds_atuais[tipo] = int(val) if val.isdigit() else 0

            self.bestiario[n] = {
                "pv": p,
                "rds": rds_atuais,
                "elemento": self.combo_elem.get()
            }

            with open(self.arquivo_dados, "w") as f:
                json.dump(self.bestiario, f)

            self.combo_selecao.configure(
                values=list(self.bestiario.keys())
            )

            messagebox.showinfo(
                "Grimório",
                f"Dados de {n} sincronizados."
            )

    # =========================
    def add_ini(self):
        n = self.ent_ini_n.get()
        v = self.ent_ini_v.get()

        if n and v.isdigit():
            self.lista_iniciativa.append((n, int(v)))
            self.lista_iniciativa.sort(
                key=lambda x: x[1],
                reverse=True
            )

            self.txt_ini.delete("1.0", "end")

            for i, (name, val) in enumerate(self.lista_iniciativa):
                self.txt_ini.insert(
                    "end",
                    f"{'▶ ' if i == 0 else '  '}{val:02d} | {name}\n"
                )

    # =========================
    def clear_ini(self):
        self.lista_iniciativa = []
        self.txt_ini.delete("1.0", "end")


# =========================
if __name__ == "__main__":
    app = OrdoApp()
    app.mainloop()