import pdfplumber
import os
import re

def extrair_todos_grupos_final(pdf_path):
    dados_finais = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pagina = pdf.pages[0]
            todas_tabelas = pagina.extract_tables()
            # Extração de texto para backup (Plano B)
            texto_pag_linhas = pagina.extract_text(layout=True).split('\n') if pagina.extract_text() else []

            # --- HELPERS (Funções Auxiliares) ---
            
            def pegar_valor_abaixo(linhas_bloco, col_idx, texto_chave):
                """Busca valor numérico abaixo de um rótulo (ex: Dial)"""
                for idx_l, linha in enumerate(linhas_bloco):
                    if col_idx >= len(linha): continue
                    celula = str(linha[col_idx])
                    if texto_chave in celula:
                        if idx_l + 1 < len(linhas_bloco):
                            if col_idx < len(linhas_bloco[idx_l+1]):
                                return str(linhas_bloco[idx_l+1][col_idx]).strip()
                return ""

            def pegar_valor_simples(linhas_bloco, col_idx):
                """Pega o primeiro valor não vazio na coluna especificada"""
                for l in linhas_bloco:
                    if col_idx < len(l):
                        val = str(l[col_idx]).strip()
                        if val and val != "None" and val != "":
                            return val.replace("\n", " ")
                return ""
            
            def pegar_texto_profundo(linhas_bloco, indices_cols):
                """
                Varre colunas e linhas (0 e 1) procurando texto.
                Corrige o problema de 'Texto Escorregadio' em células mescladas.
                """
                for col_idx in indices_cols:
                    # Varre a Linha 0 e a Linha 1 
                    for row_idx in [0, 1]:
                        try:
                            if row_idx < len(linhas_bloco) and col_idx < len(linhas_bloco[row_idx]):
                                val = str(linhas_bloco[row_idx][col_idx]).strip()
                                
                                # Ignora lixo, vazios e cabeçalhos internos
                                if val in ["None", "", "-", "Dial", "T. Adic.", "Tempo", "segundos"]:
                                    continue
                                
                                # Ignora se for puramente numérico (provavelmente é um Dial deslocado)
                                val_check = val.replace('.', '').replace(',', '')
                                if val_check.isdigit(): 
                                    continue
                                
                                # Se chegou aqui, é o Nome da Curva
                                return val.replace("\n", " ")
                        except: pass
                return ""

            def pegar_tempo_morto(linhas_bloco):
                """Concatena valores da última coluna"""
                valores = []
                for l in linhas_bloco:
                    if len(l) > 0:
                        val = str(l[-1]).strip()
                        if val and val not in ["None", "", "-", "Tempo", "Morto"] and len(val) < 10:
                            valores.append(val)
                return ", ".join(valores)

            def resgatar_grupo4_texto(texto_linhas):
                """Plano B: Lê o Grupo 4 via texto bruto se a tabela falhar"""
                for linha_txt in texto_linhas:
                    if linha_txt.strip().startswith("Grupo 4"):
                        partes = linha_txt.split()
                        # Limpa palavras-chave de estrutura
                        partes = [p for p in partes if p not in ["Grupo", "4", "-", "–", ".", "_", "Fase", "Terra"]]
                        dados_limpos = []
                        buffer_curva = ""
                        for p in partes:
                            # Se for número ou termina em 'L' (Seq) ou é a palavra 'Lenta' (Curva Rápida fake)
                            if re.match(r'^\d', p) or p.endswith('L') or p == "Lenta": 
                                if buffer_curva:
                                    dados_limpos.append(buffer_curva.strip()); buffer_curva = ""
                                dados_limpos.append(p)
                            else: 
                                buffer_curva += p + " "
                        if buffer_curva: dados_limpos.append(buffer_curva.strip())
                        return dados_limpos
                return []

            # --- LOOP PRINCIPAL (Varredura de Tabelas) ---
            for idx_tab, tabela in enumerate(todas_tabelas):
                for i, linha in enumerate(tabela):
                    primeira_celula = str(linha[0]).strip() if len(linha) > 0 else ""

                    # Identifica se é uma linha de início de Grupo
                    if "Grupo" in primeira_celula and len(primeira_celula) <= 8 and "Grupos" not in primeira_celula:
                        grupo_nome = primeira_celula
                        linhas_bloco = tabela[i : i+4]
                        if len(linhas_bloco) < 1: continue 

                        # Inicializa Variáveis
                        f_pickup, f_seq, f_lenta_curva, f_lenta_dial, f_lenta_tadic = "", "", "", "", ""
                        f_rapida_curva, f_rapida_dial, f_rapida_tadic = "", "", ""
                        t_pickup, t_seq, t_lenta_curva, t_lenta_tempo = "", "", "", ""
                        t_rapida_curva, t_rapida_tempo = "", ""

                        # ================= LÓGICA GRUPO 4 (Linear/Híbrida) =================
                        if "Grupo 4" in grupo_nome:
                            fila_dados = []
                            # Tenta ler da tabela primeiro
                            for x in linhas_bloco[0]:
                                val = str(x).strip().replace('\n', ' ')
                                if val and val not in ["None", "", "-", "–", ".", "_", "Grupo 4", "Fase", "Terra"]:
                                    fila_dados.append(val)
                            
                            # Se tabela vazia ou inválida, tenta texto bruto
                            if len(fila_dados) == 0 or (len(fila_dados) > 0 and not any(c.isdigit() for c in fila_dados[0])):
                                fila_dados = resgatar_grupo4_texto(texto_pag_linhas)

                            # Parse Dinâmico (Detecta Tipo de Dado)
                            try:
                                idx = 0
                                # --- FASE ---
                                if len(fila_dados) > idx: f_pickup = fila_dados[idx]; idx += 1
                                if len(fila_dados) > idx: f_seq    = fila_dados[idx]; idx += 1
                                
                                # Curva Lenta
                                if len(fila_dados) > idx:
                                    if not re.match(r'^\d', fila_dados[idx]): # Se não é número, é curva
                                        f_lenta_curva = fila_dados[idx]; idx += 1
                                
                                # Decisão: O próximo é Dial (Num) ou Curva Rápida (Texto)?
                                if len(fila_dados) > idx:
                                    val_atual = fila_dados[idx]
                                    if re.match(r'^[\d\.,]+$', val_atual): # É número -> Dial Lenta
                                        f_lenta_dial = val_atual; idx += 1
                                    else: # É texto -> Curva Rápida
                                        f_rapida_curva = val_atual; idx += 1
                                        if len(fila_dados) > idx: f_rapida_dial = fila_dados[idx]; idx += 1
                                
                                # --- TERRA ---
                                if len(fila_dados) > idx: t_pickup = fila_dados[idx]; idx += 1
                                if len(fila_dados) > idx: t_seq    = fila_dados[idx]; idx += 1
                                
                                if len(fila_dados) > idx:
                                    if not re.match(r'^\d', fila_dados[idx]):
                                        t_lenta_curva = fila_dados[idx]; idx += 1
                                
                                if len(fila_dados) > idx:
                                    val_atual = fila_dados[idx]
                                    if re.match(r'^[\d\.,]+$', val_atual):
                                        t_lenta_tempo = val_atual; idx += 1 
                                    else:
                                        t_rapida_curva = val_atual; idx += 1
                                        if len(fila_dados) > idx: t_rapida_tempo = fila_dados[idx]; idx += 1
                            except: pass

                        # ================= LÓGICA PADRÃO (Grupos 1, 2, 3) =================
                        else:
                            f_pickup = pegar_valor_simples(linhas_bloco, 1)
                            t_pickup = pegar_valor_simples(linhas_bloco, 7)
                            
                            # Se não tiver Pickup em nenhum lado, ignora grupo vazio
                            if not f_pickup and not t_pickup: continue

                            f_seq = pegar_valor_simples(linhas_bloco, 2)
                            
                            # Scanner Profundo para Nomes de Curvas
                            f_lenta_curva = pegar_texto_profundo(linhas_bloco, [3, 4])
                            f_rapida_curva = pegar_texto_profundo(linhas_bloco, [5, 6])
                            t_lenta_curva = pegar_texto_profundo(linhas_bloco, [9, 10])
                            t_rapida_curva = pegar_texto_profundo(linhas_bloco, [11, 12])
                            
                            # Valores Numéricos (Abaixo dos labels)
                            f_lenta_dial = pegar_valor_abaixo(linhas_bloco, 3, "Dial")
                            f_lenta_tadic = pegar_valor_abaixo(linhas_bloco, 4, "T. Adic")
                            f_rapida_dial = pegar_valor_abaixo(linhas_bloco, 5, "Dial")
                            f_rapida_tadic = pegar_valor_abaixo(linhas_bloco, 6, "T. Adic")

                            t_seq = pegar_valor_simples(linhas_bloco, 8)
                            t_lenta_tempo = pegar_valor_abaixo(linhas_bloco, 9, "Tempo") or pegar_valor_abaixo(linhas_bloco, 9, "Dial")
                            t_rapida_tempo = pegar_valor_abaixo(linhas_bloco, 11, "Tempo")

                        # Montagem do Objeto Final
                        item = {
                            "Arquivo": os.path.basename(pdf_path),
                            "Grupo": grupo_nome,
                            "Fase_Pickup": f_pickup, "Fase_Seq": f_seq,
                            "Fase_Lenta_Curva": f_lenta_curva, "Fase_Lenta_Dial": f_lenta_dial, "Fase_Lenta_TAdic": f_lenta_tadic,
                            "Fase_Rapida_Curva": f_rapida_curva, "Fase_Rapida_Dial": f_rapida_dial, "Fase_Rapida_TAdic": f_rapida_tadic,
                            "Terra_Pickup": t_pickup, "Terra_Seq": t_seq,
                            "Terra_Lenta_Curva": t_lenta_curva, "Terra_Lenta_Tempo": t_lenta_tempo,
                            "Terra_Rapida_Curva": t_rapida_curva, "Terra_Rapida_Tempo": t_rapida_tempo,
                            "Tempo_Morto": pegar_tempo_morto(linhas_bloco)
                        }
                        dados_finais.append(item)
    
    except Exception as e:
        # Retorna o erro para ser logado no script principal
        return None, f"{os.path.basename(pdf_path)} - ERRO CRÍTICO: {str(e)}"
    
    return dados_finais, None