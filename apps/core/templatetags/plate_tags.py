import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

MERCOSUL_REGEX = re.compile(r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$')
ANTIGO_REGEX = re.compile(r'^[A-Z]{3}[0-9]{4}$')

def get_plate_info(raw_value):
    if not raw_value:
        return {'type': 'generico', 'raw': '', 'formatted': '---'}
    
    clean = re.sub(r'[^A-Za-z0-9]', '', str(raw_value)).upper()
    
    if MERCOSUL_REGEX.match(clean):
        return {
            'type': 'mercosul',
            'raw': clean,
            'formatted': clean,
            'is_mercosul': True,
            'is_antigo': False,
        }
    elif ANTIGO_REGEX.match(clean):
        formatted = f"{clean[:3]}-{clean[3:]}"
        return {
            'type': 'antigo',
            'raw': clean,
            'formatted': formatted,
            'is_mercosul': False,
            'is_antigo': True,
        }
    else:
        return {
            'type': 'generico',
            'raw': clean,
            'formatted': clean,
            'is_mercosul': False,
            'is_antigo': False,
        }

@register.simple_tag
def render_plate(raw_value, size='md'):
    """
    Renderiza um badge gráfico realista e responsivo da Placa Veicular Brasileira
    Identificando automaticamente se é padrão MERCOSUL ou ANTIGO (Cinza).
    Suporta tamanhos: 'sm' (tabelas/listas), 'md' (cards de pátio/portal), 'lg' (destaque/topo).
    """
    info = get_plate_info(raw_value)
    plate_type = info['type']
    formatted_text = info['formatted']

    # Estilos de tamanho
    size_styles = {
        'sm': {
            'container': 'w-[88px] h-[28px] rounded-[3px] border-[1px]',
            'header_h': 'h-[8px] px-1',
            'header_text': 'text-[5px]',
            'flag_w': 'w-2.5 h-1.5',
            'body_text': 'text-[12px] tracking-[0.08em]',
            'antigo_top': 'text-[5px]',
        },
        'md': {
            'container': 'w-[110px] h-[36px] rounded-[4px] border-[1.5px]',
            'header_h': 'h-[10px] px-1.5',
            'header_text': 'text-[6.5px]',
            'flag_w': 'w-3 h-2',
            'body_text': 'text-[15px] tracking-[0.1em]',
            'antigo_top': 'text-[6px]',
        },
        'lg': {
            'container': 'w-[140px] h-[44px] rounded-[5px] border-[2px]',
            'header_h': 'h-[13px] px-2',
            'header_text': 'text-[8.5px]',
            'flag_w': 'w-4 h-2.5',
            'body_text': 'text-[19px] tracking-[0.12em]',
            'antigo_top': 'text-[7.5px]',
        }
    }
    s = size_styles.get(size, size_styles['md'])

    if plate_type == 'mercosul':
        # Placa Padrão Mercosul (Faixa Azul Superior + Fundo Branco + Letras Pretas)
        html = f"""
        <div class="inline-flex flex-col justify-between {s['container']} bg-white border-black shadow-md select-none overflow-hidden shrink-0 relative" title="Placa Padrão Mercosul: {formatted_text}">
            <!-- Faixa Azul Mercosul -->
            <div class="{s['header_h']} bg-[#003399] flex items-center justify-between text-white w-full leading-none">
                <!-- Símbolo Mercosul (estrelas estilizadas) -->
                <div class="flex items-center opacity-90">
                    <svg class="{s['flag_w']}" viewBox="0 0 20 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="5" cy="6" r="1.2" fill="#FFCC00"/>
                        <circle cx="9" cy="3" r="1" fill="#FFCC00"/>
                        <circle cx="11" cy="9" r="1" fill="#FFCC00"/>
                        <circle cx="15" cy="5" r="1.2" fill="#FFCC00"/>
                    </svg>
                </div>
                <!-- Nome BRASIL -->
                <span class="{s['header_text']} font-black tracking-widest uppercase font-sans">BRASIL</span>
                <!-- Bandeira do Brasil -->
                <div class="{s['flag_w']} rounded-[1px] overflow-hidden bg-[#009B3A] flex items-center justify-center relative shadow-sm">
                    <div class="w-[85%] h-[75%] bg-[#FEDF00] rotate-45 transform scale-y-75 flex items-center justify-center"></div>
                    <div class="w-[38%] h-[38%] bg-[#002776] rounded-full absolute"></div>
                </div>
            </div>
            <!-- Caracteres da Placa -->
            <div class="flex-1 flex items-center justify-center bg-gradient-to-b from-white via-[#fcfcfc] to-[#ebebeb] px-0.5">
                <span class="{s['body_text']} font-black font-mono text-black leading-none uppercase drop-shadow-[0_0.5px_0.5px_rgba(0,0,0,0.4)]">
                    {formatted_text}
                </span>
            </div>
        </div>
        """
    elif plate_type == 'antigo':
        # Placa Padrão Antigo (Cinza metálico + Borda + BRASIL sutil + Letras Pretas com hífen)
        html = f"""
        <div class="inline-flex flex-col justify-between {s['container']} bg-gradient-to-b from-[#E2E8F0] via-[#CBD5E1] to-[#94A3B8] border-[#334155] shadow-md select-none overflow-hidden shrink-0 relative" title="Placa Padrão Antigo (Cinza): {formatted_text}">
            <!-- Tarja Superior Cinza Antigo -->
            <div class="{s['header_h']} bg-[#94A3B8]/80 border-b border-[#64748B]/50 flex items-center justify-center text-[#1E293B] w-full leading-none">
                <span class="{s['antigo_top']} font-extrabold tracking-wider uppercase font-sans">BRASIL</span>
            </div>
            <!-- Caracteres da Placa -->
            <div class="flex-1 flex items-center justify-center px-0.5">
                <span class="{s['body_text']} font-black font-mono text-[#0F172A] leading-none uppercase drop-shadow-[0_0.8px_0.8px_rgba(255,255,255,0.7)]">
                    {formatted_text}
                </span>
            </div>
        </div>
        """
    else:
        # Placa Genérica / Outro formato
        html = f"""
        <div class="inline-flex items-center justify-center {s['container']} bg-[#1E293B] border-[#D4AF37]/50 shadow-md select-none overflow-hidden shrink-0" title="Placa: {formatted_text}">
            <span class="{s['body_text']} font-black font-mono text-[#D4AF37] leading-none uppercase">
                {formatted_text}
            </span>
        </div>
        """

    return mark_safe(html.strip())

@register.filter
def plate_format(raw_value):
    return get_plate_info(raw_value)['formatted']

@register.filter
def plate_type(raw_value):
    return get_plate_info(raw_value)['type']
