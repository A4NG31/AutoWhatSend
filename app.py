import streamlit as st
import pandas as pd
import time
import re
from io import BytesIO
import urllib.parse
import base64
import random

# Configuración de la página
st.set_page_config(
    page_title="AutoWhatSend Gratis",
    page_icon="📱",
    layout="wide"
)

# Inicializar session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'column_selected' not in st.session_state:
    st.session_state.column_selected = False
if 'numbers_validated' not in st.session_state:
    st.session_state.numbers_validated = False
if 'message_ready' not in st.session_state:
    st.session_state.message_ready = False
if 'sending_complete' not in st.session_state:
    st.session_state.sending_complete = False
if 'failed_numbers' not in st.session_state:
    st.session_state.failed_numbers = []
if 'successful_numbers' not in st.session_state:
    st.session_state.successful_numbers = []
if 'current_sending_index' not in st.session_state:
    st.session_state.current_sending_index = 0
if 'sending_in_progress' not in st.session_state:
    st.session_state.sending_in_progress = False
if 'whatsapp_urls' not in st.session_state:
    st.session_state.whatsapp_urls = []

def validate_colombian_number(number):
    """Valida que el número sea un número colombiano válido"""
    number_str = str(number).strip()
    clean_number = re.sub(r'[^\d]', '', number_str)
    
    if len(clean_number) == 10 and clean_number.startswith('3'):
        return True, clean_number
    return False, clean_number

def format_number_for_url(number):
    """Formatea el número para URLs de WhatsApp"""
    return f"57{number}"

def generate_whatsapp_url(number, message):
    """Genera URL de WhatsApp Web"""
    encoded_message = urllib.parse.quote(message)
    return f"https://web.whatsapp.com/send?phone={number}&text={encoded_message}"

def create_excel_download(data, filename):
    """Crea un archivo Excel para descarga"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        data.to_excel(writer, index=False, sheet_name='Datos')
    return output.getvalue()

def create_html_with_auto_click(urls_data):
    """Crea HTML con auto-click para enviar mensajes"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AutoWhatsApp - Envío Automático</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 40px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            .whatsapp-link { 
                display: inline-block; 
                background-color: #25D366; 
                color: white; 
                padding: 15px 25px; 
                margin: 15px; 
                text-decoration: none; 
                border-radius: 30px; 
                font-weight: bold; 
                font-size: 16px;
                transition: all 0.3s; 
                box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3);
            }
            .whatsapp-link:hover { 
                background-color: #128C7E; 
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(37, 211, 102, 0.4);
            }
            .contact-info { 
                background: rgba(255, 255, 255, 0.15); 
                padding: 20px; 
                margin: 20px 0; 
                border-radius: 12px; 
                border-left: 5px solid #25D366; 
            }
            .instructions {
                background: rgba(255, 255, 255, 0.1);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
            h1 {
                text-align: center;
                font-size: 2.5em;
                margin-bottom: 30px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📱 AutoWhatsApp</h1>
            
            <div class="instructions">
                <h3>🚀 Instrucciones para Envío Automático:</h3>
                <ol>
                    <li>Haz clic en cada botón verde</li>
                    <li>Se abrirá WhatsApp Web en nueva pestaña</li>
                    <li>El mensaje estará pre-escrito</li>
                    <li>Solo debes hacer clic en <strong>ENVIAR</strong> manualmente</li>
                    <li>Espera 3 segundos entre cada envío</li>
                </ol>
                <p><strong>💡 Tip:</strong> Mantén WhatsApp Web abierto y logueado</p>
            </div>
    """
    
    for i, data in enumerate(urls_data):
        html_content += f"""
            <div class="contact-info">
                <strong>👤 Contacto {i+1}:</strong> {data['display_info']}<br>
                <strong>💬 Mensaje:</strong> {data['mensaje'][:100]}...<br><br>
                <a href="{data['url']}" target="_blank" class="whatsapp-link" 
                   onclick="setTimeout(function(){{ window.open('{data['url']}', '_blank'); }}, {i * 3000}); return false;">
                    📱 Enviar a {data['display_info'].split(' - ')[0] if ' - ' in data['display_info'] else data['display_info']}
                </a>
            </div>
        """
    
    html_content += """
        </div>
        
        <script>
            // Función para abrir enlaces con delay
            function openWithDelay(url, delay) {
                setTimeout(function() {
                    window.open(url, '_blank');
                }, delay);
            }
        </script>
    </body>
    </html>
    """
    
    return html_content

def create_javascript_opener(urls, delay=3):
    """Crea código JavaScript para abrir URLs con delay"""
    js_code = """
    <script>
        function openWhatsAppLinks() {
    """
    
    for i, url in enumerate(urls):
        js_code += f"""
            setTimeout(function() {{
                window.open('{url}', '_blank');
                console.log('Abriendo enlace {i+1}');
            }}, {i * (delay * 1000)});
        """
    
    js_code += """
        }
        openWhatsAppLinks();
    </script>
    """
    
    return js_code

# Título principal
st.title("📱 AutoWhatSend Gratis")
st.markdown("🚀 **Envío Semi-Automático 100% Gratuito** - Abre WhatsApp automáticamente")
st.markdown("---")

# Paso 1: Cargar archivo
st.header("1️⃣ Cargar Base de Datos")

uploaded_file = st.file_uploader(
    "Selecciona tu archivo Excel (.xlsx)",
    type=['xlsx'],
    help="El archivo debe contener al menos una columna con números de teléfono"
)

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.session_state.df = df
        st.success(f"✅ Archivo cargado exitosamente: {len(df)} registros encontrados")
        
        st.subheader("📊 Vista previa de los datos")
        st.write(f"**Total de registros:** {len(df)}")
        st.write(f"**Columnas disponibles:** {', '.join(df.columns.tolist())}")
        st.dataframe(df.head(10))
        
    except Exception as e:
        st.error(f"❌ Error al leer el archivo: {str(e)}")
        st.session_state.df = None

# Paso 2: Seleccionar columna de números
if st.session_state.df is not None:
    st.markdown("---")
    st.header("2️⃣ Seleccionar Columna de Números")
    
    number_column = st.selectbox(
        "¿En qué columna están los números de teléfono?",
        options=st.session_state.df.columns.tolist(),
        help="Selecciona la columna que contiene los números de WhatsApp"
    )
    
    if st.button("✅ Confirmar Columna de Números"):
        st.session_state.number_column = number_column
        st.session_state.column_selected = True
        st.rerun()

# Paso 3: Validar números
if st.session_state.get('column_selected', False):
    st.markdown("---")
    st.header("3️⃣ Validación de Números")
    
    df = st.session_state.df
    number_col = st.session_state.number_column
    
    valid_numbers = []
    invalid_numbers = []
    
    for index, row in df.iterrows():
        number = row[number_col]
        is_valid, clean_number = validate_colombian_number(number)
        
        if is_valid:
            valid_numbers.append({
                'index': index,
                'original': number,
                'clean': clean_number,
                'url_format': format_number_for_url(clean_number),
                'full_number': f"+57{clean_number}"
            })
        else:
            invalid_numbers.append({
                'index': index,
                'original': number,
                'reason': 'Formato inválido o no es número colombiano'
            })
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("✅ Números Válidos", len(valid_numbers))
    with col2:
        st.metric("❌ Números Inválidos", len(invalid_numbers))
    
    if invalid_numbers:
        st.warning("⚠️ Se encontraron números con formato inválido:")
        st.dataframe(pd.DataFrame(invalid_numbers))
        st.info("💡 **Formato correcto:** 10 dígitos que empiecen con 3 (ej: 3008686725)")
    
    if valid_numbers:
        st.success(f"🎉 {len(valid_numbers)} números están listos para envío")
        
        if st.checkbox("Ver muestra de números válidos"):
            st.dataframe(pd.DataFrame(valid_numbers[:10]))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Cargar Nueva Base", type="secondary"):
                for key in ['df', 'column_selected', 'numbers_validated', 'message_ready', 'sending_complete']:
                    if key in st.session_state: del st.session_state[key]
                st.rerun()
        
        with col2:
            if st.button("✅ Continuar", type="primary"):
                st.session_state.valid_numbers = valid_numbers
                st.session_state.numbers_validated = True
                st.rerun()
    else:
        st.error("❌ No se encontraron números válidos")

# Paso 4: Personalizar mensaje
if st.session_state.get('numbers_validated', False):
    st.markdown("---")
    st.header("4️⃣ Personalizar Mensaje")
    
    df = st.session_state.df
    available_columns = [col for col in df.columns if col != st.session_state.number_column]
    
    st.info("💡 **Tip:** Usa variables como {NOMBRE}, {EMPRESA} entre llaves")
    
    if available_columns:
        st.write("**Columnas disponibles:**")
        cols_display = st.columns(min(len(available_columns), 4))
        for i, col in enumerate(available_columns):
            with cols_display[i % 4]:
                st.code(f"{{{col}}}")
    
    default_message = """Buenas tardes,

Tengo disponibles dos fechas para que podamos reunirnos y realizar la difusión de la metodología, los requisitos genéricos y los documentos. Usted puede escoger la que más le convenga:

Opción 1: Sábado 12 de abril a las 10:00 a.m., de manera virtual a través de Zoom.

Opción 2: Jueves 24 de abril a las 2:00 p.m., de manera presencial en las instalaciones del IDPAC (Avenida Calle 22 No. 68C-51).

Si prefiere la opción virtual, con gusto le envío de una vez el enlace para que pueda ingresar mañana.

Quedo atenta a la fecha que elija."""

    message_template = st.text_area("Escribe tu mensaje:", value=default_message, height=300)
    
    delay = st.slider("Tiempo entre mensajes (segundos):", min_value=2, max_value=10, value=3)
    
    st.subheader("👁️ Vista Previa del Mensaje")
    
    if st.session_state.valid_numbers:
        sample_row = df.iloc[st.session_state.valid_numbers[0]['index']]
        try:
            preview_message = message_template
            for col in df.columns:
                value = str(sample_row[col]) if pd.notna(sample_row[col]) else ""
                preview_message = preview_message.replace(f"{{{col}}}", value)
            st.text_area("Así se verá:", preview_message, height=200, disabled=True)
        except Exception as e:
            st.error(f"Error en vista previa: {str(e)}")
    
    if st.button("📝 Confirmar Mensaje", type="primary"):
        st.session_state.message_template = message_template
        st.session_state.delay = delay
        st.session_state.message_ready = True
        st.success("✅ Mensaje configurado")
        st.rerun()

# Paso 5: Preparar envío
if st.session_state.get('message_ready', False):
    st.markdown("---")
    st.header("5️⃣ Preparar Envío de Mensajes")
    
    total_messages = len(st.session_state.valid_numbers)
    st.info(f"📊 Preparando **{total_messages}** mensajes de WhatsApp")
    
    # Preparar URLs de WhatsApp
    whatsapp_urls = []
    df = st.session_state.df
    
    for number_info in st.session_state.valid_numbers:
        try:
            row_data = df.iloc[number_info['index']]
            personalized_message = st.session_state.message_template
            
            for col in df.columns:
                value = str(row_data[col]) if pd.notna(row_data[col]) else ""
                personalized_message = personalized_message.replace(f"{{{col}}}", value)
            
            # Crear información para mostrar
            display_info = number_info['full_number']
            if 'NOMBRE' in df.columns and pd.notna(row_data.get('NOMBRE')):
                display_info += f" - {row_data['NOMBRE']}"
            if 'EMPRESA' in df.columns and pd.notna(row_data.get('EMPRESA')):
                display_info += f" ({row_data['EMPRESA']})"
            
            whatsapp_urls.append({
                'numero': number_info['full_number'],
                'url': generate_whatsapp_url(number_info['url_format'], personalized_message),
                'mensaje': personalized_message,
                'display_info': display_info
            })
            
        except Exception as e:
            st.error(f"Error preparando mensaje: {str(e)}")
    
    st.session_state.whatsapp_urls = whatsapp_urls
    
    # Mostrar opciones de envío
    st.subheader("🚀 Opciones de Envío")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Abrir Enlaces Automáticamente", type="primary", use_container_width=True):
            # Crear JavaScript para abrir enlaces con delay
            urls = [item['url'] for item in whatsapp_urls]
            js_code = create_javascript_opener(urls, st.session_state.delay)
            st.components.v1.html(js_code, height=0)
            
            st.success("🚀 ¡Enlaces se están abriendo automáticamente!")
            st.info("""
            **📋 Qué está pasando:**
            - Se están abriendo pestañas de WhatsApp automáticamente
            - Cada 3 segundos se abre una nueva pestaña
            - El mensaje ya está pre-escrito
            - Solo debes hacer clic en **ENVIAR** manualmente
            """)
    
    with col2:
        # Descargar HTML con enlaces interactivos
        html_content = create_html_with_auto_click(whatsapp_urls)
        b64 = base64.b64encode(html_content.encode()).decode()
        href = f'<a href="data:text/html;base64,{b64}" download="whatsapp_auto_send.html" style="display:inline-block; background:#25D366; color:white; padding:15px 25px; border-radius:30px; text-decoration:none; font-weight:bold; text-align:center;">📥 Descargar HTML Automático</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.caption("Descarga este archivo y ábrelo en tu navegador para envío automático")

# Sidebar informativo
st.sidebar.header("ℹ️ AutoWhatSend Gratis")
st.sidebar.markdown("""
### 🚀 Cómo funciona:

**Método 1: Envío Directo**
- Haz clic en "Abrir Enlaces Automáticamente"
- Se abrirán pestañas automáticamente
- Solo debes hacer clic en **ENVIAR**

**Método 2: HTML Descargable**
- Descarga el archivo HTML
- Ábrelo en tu navegador
- Haz clic en los botones verdes
- Se abrirán con delay automático

### ⚠️ Requisitos:
- WhatsApp Web abierto y logueado
- Permitir ventanas emergentes
- No cerrar el navegador principal

### 💡 Tips:
1. Abre WhatsApp Web primero
2. Mantén la sesión activa
3. Usa delay de 3-5 segundos
4. revisa cada pestaña antes de enviar
""")

st.sidebar.markdown("---")
st.sidebar.success("**✅ 100% Gratuito** - Sin APIs costosas")
st.sidebar.markdown("**🎯 Eficiente** - Semi-automático pero rápido")
st.sidebar.markdown("**🌐 Compatible** - Funciona en Streamlit Cloud")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; margin-top: 50px;'>
    <p>🚀 <strong>AutoWhatSend Gratis</strong> - Envío semi-automático de WhatsApp</p>
    <p>💡 Recuerda: Debes hacer clic en ENVIAR manualmente en cada pestaña</p>
</div>
""", unsafe_allow_html=True)
