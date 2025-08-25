import streamlit as st
import pandas as pd
import time
import re
from io import BytesIO
import urllib.parse
import webbrowser
import threading
import base64

# Configuración de la página
st.set_page_config(
    page_title="AutoWhatSend",
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

def validate_colombian_number(number):
    """Valida que el número sea un número colombiano válido"""
    # Convertir a string y limpiar
    number_str = str(number).strip()
    
    # Remover espacios, guiones y otros caracteres
    clean_number = re.sub(r'[^\d]', '', number_str)
    
    # Verificar que tenga 10 dígitos y empiece con 3
    if len(clean_number) == 10 and clean_number.startswith('3'):
        return True, clean_number
    
    return False, clean_number

def format_number_for_url(number):
    """Formatea el número para URLs de WhatsApp (sin +)"""
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
    
    processed_data = output.getvalue()
    return processed_data

def create_html_download_link(urls_data, filename="whatsapp_links.html"):
    """Crea un archivo HTML con enlaces para descargar"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enlaces de WhatsApp</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .whatsapp-link { 
                display: inline-block; 
                background-color: #25D366; 
                color: white; 
                padding: 12px 20px; 
                margin: 10px; 
                text-decoration: none; 
                border-radius: 25px; 
                font-weight: bold; 
                transition: all 0.3s; 
            }
            .whatsapp-link:hover { 
                background-color: #128C7E; 
                transform: scale(1.05); 
            }
            .contact-info { 
                background-color: #f0f2f6; 
                padding: 15px; 
                margin: 10px; 
                border-radius: 10px; 
                border-left: 4px solid #25D366; 
            }
        </style>
    </head>
    <body>
        <h1>Enlaces de WhatsApp</h1>
    """
    
    for i, data in enumerate(urls_data):
        html_content += f"""
        <div class="contact-info">
            <strong>Contacto {i+1}:</strong> {data['display_info']}<br>
            <a href="{data['url']}" target="_blank" class="whatsapp-link">
                📱 Abrir en WhatsApp
            </a>
        </div>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    return html_content

# Título principal
st.title("📱 AutoWhatSend")
st.markdown("🚀 **Envío Semi-Automático de WhatsApp** - Abre automáticamente los enlaces de WhatsApp")
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
        # Leer el archivo Excel
        df = pd.read_excel(uploaded_file)
        st.session_state.df = df
        
        st.success(f"✅ Archivo cargado exitosamente: {len(df)} registros encontrados")
        
        # Mostrar información del archivo
        st.subheader("📊 Vista previa de los datos")
        st.write(f"**Total de registros:** {len(df)}")
        st.write(f"**Columnas disponibles:** {', '.join(df.columns.tolist())}")
        
        # Mostrar primeros 10 registros
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
    
    # Validar números
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
                'url_format': format_number_for_url(clean_number)
            })
        else:
            invalid_numbers.append({
                'index': index,
                'original': number,
                'reason': 'Formato inválido o no es número colombiano'
            })
    
    # Mostrar resultados de validación
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("✅ Números Válidos", len(valid_numbers))
        
    with col2:
        st.metric("❌ Números Inválidos", len(invalid_numbers))
    
    if invalid_numbers:
        st.warning("⚠️ Se encontraron números con formato inválido:")
        invalid_df = pd.DataFrame(invalid_numbers)
        st.dataframe(invalid_df)
        
        st.info("💡 **Formato correcto:** Los números deben tener 10 dígitos y empezar con 3 (ej: 3008686725)")
    
    if valid_numbers:
        st.success(f"🎉 {len(valid_numbers)} números están listos para envío")
        
        # Mostrar muestra de números válidos
        if st.checkbox("Ver muestra de números válidos"):
            valid_sample = pd.DataFrame(valid_numbers[:10])
            st.dataframe(valid_sample)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Cargar Nueva Base", type="secondary"):
                # Reiniciar estados
                keys_to_reset = ['df', 'column_selected', 'numbers_validated', 'message_ready', 'sending_complete']
                for key in keys_to_reset:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        with col2:
            if st.button("✅ Continuar con Estos Números", type="primary"):
                st.session_state.valid_numbers = valid_numbers
                st.session_state.numbers_validated = True
                st.rerun()
    else:
        st.error("❌ No se encontraron números válidos en el archivo")

# Paso 4: Personalizar mensaje
if st.session_state.get('numbers_validated', False):
    st.markdown("---")
    st.header("4️⃣ Personalizar Mensaje")
    
    df = st.session_state.df
    available_columns = [col for col in df.columns if col != st.session_state.number_column]
    
    st.info("💡 **Tip:** Puedes usar variables de tu base de datos escribiendo el nombre entre llaves, ej: {NOMBRE}, {EMPRESA}")
    
    # Mostrar columnas disponibles
    if available_columns:
        st.write("**Columnas disponibles para personalización:**")
        cols_display = st.columns(min(len(available_columns), 4))
        for i, col in enumerate(available_columns):
            with cols_display[i % 4]:
                st.code(f"{{{col}}}")
    
    # Área de texto para el mensaje
    default_message = """Buenas tardes,

Tengo disponibles dos fechas para que podamos reunirnos y realizar la difusión de la metodología, los requisitos genéricos y los documentos. Usted puede escoger la que más le convenga:

Opción 1: Sábado 12 de abril a las 10:00 a.m., de manera virtual a través de Zoom.

Opción 2: Jueves 24 de abril a las 2:00 p.m., de manera presencial en las instalaciones del IDPAC (Avenida Calle 22 No. 68C-51).

Si prefiere la opción virtual, con gusto le envío de una vez el enlace para que pueda ingresar mañana.

Quedo atenta a la fecha que elija."""

    message_template = st.text_area(
        "Escribe tu mensaje:",
        value=default_message,
        height=300,
        help="Usa {NOMBRE_COLUMNA} para insertar datos de tu base"
    )
    
    # Configurar delay entre mensajes
    delay = st.slider(
        "Tiempo sugerido entre mensajes (segundos):",
        min_value=5,
        max_value=60,
        value=15,
        help="Tiempo recomendado entre el envío de cada mensaje"
    )
    
    # Vista previa del mensaje
    st.subheader("👁️ Vista Previa del Mensaje")
    
    if len(st.session_state.valid_numbers) > 0:
        # Tomar el primer registro válido para vista previa
        first_valid_index = st.session_state.valid_numbers[0]['index']
        sample_row = df.iloc[first_valid_index]
        
        try:
            # Crear diccionario para reemplazar variables
            replace_dict = {}
            for col in df.columns:
                replace_dict[col] = str(sample_row[col]) if pd.notna(sample_row[col]) else ""
            
            # Reemplazar variables en el mensaje
            preview_message = message_template
            for col, value in replace_dict.items():
                preview_message = preview_message.replace(f"{{{col}}}", value)
            
            st.text_area("Así se verá tu mensaje:", preview_message, height=200, disabled=True)
            
        except Exception as e:
            st.error(f"Error en la vista previa: {str(e)}")
    
    if st.button("📝 Confirmar Mensaje", type="primary"):
        st.session_state.message_template = message_template
        st.session_state.delay = delay
        st.session_state.message_ready = True
        st.success("✅ Mensaje configurado correctamente")
        st.rerun()

# Paso 5: Preparar envío de mensajes
if st.session_state.get('message_ready', False):
    st.markdown("---")
    st.header("5️⃣ Preparar Envío de Mensajes")
    
    total_messages = len(st.session_state.valid_numbers)
    st.info(f"📊 Se prepararán enlaces para **{total_messages}** números válidos")
    
    # Preparar URLs
    whatsapp_urls = []
    df = st.session_state.df
    
    for number_info in st.session_state.valid_numbers:
        try:
            # Obtener datos de la fila
            row_index = number_info['index']
            row_data = df.iloc[row_index]
            
            # Preparar mensaje personalizado
            personalized_message = st.session_state.message_template
            for col in df.columns:
                value = str(row_data[col]) if pd.notna(row_data[col]) else ""
                personalized_message = personalized_message.replace(f"{{{col}}}", value)
            
            # Generar URL de WhatsApp
            url_number = number_info['url_format']
            url = generate_whatsapp_url(url_number, personalized_message)
            
            # Crear información para mostrar
            display_info = f"+57{number_info['clean']}"
            if 'NOMBRE' in df.columns and pd.notna(row_data.get('NOMBRE')):
                display_info += f" - {row_data['NOMBRE']}"
            if 'EMPRESA' in df.columns and pd.notna(row_data.get('EMPRESA')):
                display_info += f" ({row_data['EMPRESA']})"
            
            whatsapp_urls.append({
                'numero': f"+57{number_info['clean']}",
                'url': url,
                'mensaje': personalized_message,
                'display_info': display_info
            })
            
        except Exception as e:
            st.error(f"Error preparando mensaje para {number_info['clean']}: {str(e)}")
    
    st.session_state.whatsapp_urls = whatsapp_urls
    
    # Mostrar opciones de envío
    st.subheader("🚀 Opciones de Envío")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Abrir Todos los Enlaces Automáticamente", type="primary"):
            st.session_state.sending_in_progress = True
            st.session_state.current_sending_index = 0
            st.rerun()
    
    with col2:
        # Descargar HTML con enlaces
        html_content = create_html_download_link(whatsapp_urls)
        b64 = base64.b64encode(html_content.encode()).decode()
        href = f'<a href="data:text/html;base64,{b64}" download="whatsapp_links.html">📥 Descargar Enlaces (HTML)</a>'
        st.markdown(href, unsafe_allow_html=True)

# Paso 6: Envío en progreso
if st.session_state.get('sending_in_progress', False):
    st.markdown("---")
    st.header("6️⃣ Envío en Progreso")
    
    total_urls = len(st.session_state.whatsapp_urls)
    current_index = st.session_state.current_sending_index
    
    if current_index < total_urls:
        current_url = st.session_state.whatsapp_urls[current_index]
        
        st.info(f"📤 Abriendo enlace {current_index + 1} de {total_urls}")
        st.write(f"**Número:** {current_url['numero']}")
        st.write(f"**Mensaje:** {current_url['mensaje'][:100]}...")
        
        # Abrir el enlace
        webbrowser.open_new_tab(current_url['url'])
        
        # Esperar antes del siguiente
        time.sleep(st.session_state.delay)
        
        # Actualizar índice
        st.session_state.current_sending_index += 1
        st.rerun()
    else:
        st.session_state.sending_in_progress = False
        st.session_state.sending_complete = True
        st.rerun()

# Paso 7: Resultados del envío
if st.session_state.get('sending_complete', False):
    st.markdown("---")
    st.header("7️⃣ Envío Completado")
    
    st.success("🎉 ¡Todos los enlaces han sido abiertos!")
    st.info("""
    **📋 Instrucciones:**
    1. WhatsApp Web se ha abierto en pestañas separadas
    2. Debes hacer clic manualmente en "Enviar" en cada pestaña
    3. Cierra cada pestaña después de enviar el mensaje
    4. El proceso continúa automáticamente con el siguiente número
    """)
    
    if st.button("🔄 Iniciar Nuevo Envío", type="primary"):
        # Reiniciar estados
        keys_to_reset = ['df', 'column_selected', 'numbers_validated', 'message_ready', 
                        'sending_complete', 'sending_in_progress', 'current_sending_index']
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Sidebar con información
st.sidebar.header("ℹ️ AutoWhatSend - Información")
st.sidebar.markdown("""
### 📋 Cómo funciona:
1. **Cargar Base de Datos** - Sube tu archivo Excel
2. **Seleccionar Columna** - Elige la columna con números
3. **Validar Números** - Verifica formato colombiano
4. **Personalizar Mensaje** - Crea tu mensaje personalizado
5. **Abrir Enlaces** - Los enlaces se abren automáticamente
6. **Enviar Manualmente** - Haz clic en enviar en cada pestaña

### 📞 Formato de números:
- ✅ Correcto: 3008686725
- ❌ Incorrecto: 08686725, +573008686725

### 🔧 Variables de personalización:
Usa el nombre de la columna entre llaves:
- `{NOMBRE}` - Para nombre
- `{EMPRESA}` - Para empresa
- `{CIUDAD}` - Para ciudad

### ⚠️ Importante:
- Debes tener WhatsApp Web abierto
- Debes hacer clic en "Enviar" manualmente
- No cierres el navegador principal
""")

st.sidebar.markdown("---")
st.sidebar.markdown("🚀 **AutoWhatSend v3.0** - Envío semi-automático")
