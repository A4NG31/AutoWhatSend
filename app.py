import streamlit as st
import pandas as pd
import time
import re
from io import BytesIO
import urllib.parse

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
if 'urls_generated' not in st.session_state:
    st.session_state.urls_generated = False
if 'whatsapp_urls' not in st.session_state:
    st.session_state.whatsapp_urls = []

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

def format_number_for_whatsapp(number):
    """Formatea el número para WhatsApp con código de país de Colombia"""
    return f"57{number}"  # Sin el + para URLs

def generate_whatsapp_url(number, message):
    """Genera URL de WhatsApp Web"""
    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/{number}?text={encoded_message}"

def create_excel_download(data, filename):
    """Crea un archivo Excel para descarga"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        data.to_excel(writer, index=False, sheet_name='Datos')
    
    processed_data = output.getvalue()
    return processed_data

def create_whatsapp_links_html(urls_data):
    """Crea HTML con enlaces de WhatsApp"""
    html = """
    <style>
    .whatsapp-link {
        display: inline-block;
        background-color: #25D366;
        color: white;
        padding: 10px 15px;
        margin: 5px;
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
        padding: 10px;
        margin: 5px;
        border-radius: 10px;
        border-left: 4px solid #25D366;
    }
    </style>
    """
    
    for i, data in enumerate(urls_data):
        html += f"""
        <div class="contact-info">
            <strong>Contacto {i+1}:</strong> {data['display_info']}<br>
            <a href="{data['url']}" target="_blank" class="whatsapp-link">
                📱 Enviar por WhatsApp
            </a>
        </div>
        """
    
    return html

# Título principal
st.title("📱 AutoWhatSend")
st.markdown("*Generador de enlaces de WhatsApp para envío masivo personalizado*")
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
                'whatsapp': format_number_for_whatsapp(clean_number)
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
        st.success(f"🎉 {len(valid_numbers)} números están listos para generar enlaces")
        
        # Mostrar muestra de números válidos
        if st.checkbox("Ver muestra de números válidos"):
            valid_sample = pd.DataFrame(valid_numbers[:10])
            st.dataframe(valid_sample)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Cargar Nueva Base", type="secondary"):
                # Reiniciar estados
                for key in ['df', 'column_selected', 'numbers_validated', 'message_ready', 'urls_generated']:
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
        st.session_state.message_ready = True
        st.success("✅ Mensaje configurado correctamente")
        st.rerun()

# Paso 5: Generar enlaces de WhatsApp
if st.session_state.get('message_ready', False):
    st.markdown("---")
    st.header("5️⃣ Generar Enlaces de WhatsApp")
    
    total_messages = len(st.session_state.valid_numbers)
    st.info(f"📊 Se generarán enlaces para **{total_messages}** números válidos")
    
    if st.button("🔗 Generar Enlaces de WhatsApp", type="primary"):
        df = st.session_state.df
        valid_numbers = st.session_state.valid_numbers
        message_template = st.session_state.message_template
        
        # Contenedores para mostrar progreso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        whatsapp_urls = []
        
        for i, number_info in enumerate(valid_numbers):
            try:
                # Obtener datos de la fila
                row_index = number_info['index']
                row_data = df.iloc[row_index]
                
                # Preparar mensaje personalizado
                personalized_message = message_template
                for col in df.columns:
                    value = str(row_data[col]) if pd.notna(row_data[col]) else ""
                    personalized_message = personalized_message.replace(f"{{{col}}}", value)
                
                # Generar URL de WhatsApp
                whatsapp_number = number_info['whatsapp']
                url = generate_whatsapp_url(whatsapp_number, personalized_message)
                
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
                
                # Actualizar progreso
                progress = (i + 1) / total_messages
                progress_bar.progress(progress)
                status_text.text(f"Generando enlace {i + 1} de {total_messages}")
                
            except Exception as e:
                st.error(f"Error generando enlace para {number_info['whatsapp']}: {str(e)}")
        
        # Guardar resultados en session state
        st.session_state.whatsapp_urls = whatsapp_urls
        st.session_state.urls_generated = True
        
        st.success("🎉 **¡Enlaces generados exitosamente!**")
        st.rerun()

# Paso 6: Mostrar enlaces y opciones de envío
if st.session_state.get('urls_generated', False):
    st.markdown("---")
    st.header("6️⃣ Enlaces de WhatsApp Generados")
    
    urls_count = len(st.session_state.whatsapp_urls)
    st.success(f"✅ Se generaron {urls_count} enlaces de WhatsApp")
    
    # Opciones de visualización
    tab1, tab2, tab3 = st.tabs(["🔗 Enlaces Interactivos", "📋 Lista Completa", "📊 Descargar Datos"])
    
    with tab1:
        st.markdown("### Enlaces Interactivos")
        st.info("💡 **Instrucciones:** Haz clic en cada botón verde para abrir WhatsApp Web con el mensaje prellenado. Se abrirá en una nueva pestaña.")
        
        # Mostrar enlaces interactivos (primeros 10)
        display_count = min(10, len(st.session_state.whatsapp_urls))
        
        if len(st.session_state.whatsapp_urls) > 10:
            st.warning(f"⚠️ Mostrando los primeros {display_count} enlaces. Ve a la pestaña 'Lista Completa' para ver todos.")
        
        # Generar HTML con enlaces
        html_links = create_whatsapp_links_html(st.session_state.whatsapp_urls[:display_count])
        st.markdown(html_links, unsafe_allow_html=True)
        
        # Botón para mostrar todos
        if len(st.session_state.whatsapp_urls) > 10:
            if st.button("📱 Mostrar Todos los Enlaces"):
                html_all_links = create_whatsapp_links_html(st.session_state.whatsapp_urls)
                st.markdown(html_all_links, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Lista Completa de Enlaces")
        
        # Crear DataFrame para mostrar
        display_data = []
        for i, data in enumerate(st.session_state.whatsapp_urls):
            display_data.append({
                'N°': i + 1,
                'Número': data['numero'],
                'Información': data['display_info'],
                'URL': data['url'][:50] + '...' if len(data['url']) > 50 else data['url']
            })
        
        display_df = pd.DataFrame(display_data)
        st.dataframe(display_df, use_container_width=True)
        
        # Copiar todas las URLs
        all_urls = '\n'.join([data['url'] for data in st.session_state.whatsapp_urls])
        st.text_area("📋 Todas las URLs (para copiar):", all_urls, height=200)
    
    with tab3:
        st.markdown("### Descargar Datos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Excel con URLs
            excel_data_urls = pd.DataFrame(st.session_state.whatsapp_urls)
            excel_urls = create_excel_download(excel_data_urls, "enlaces_whatsapp.xlsx")
            
            st.download_button(
                label="📥 Descargar Enlaces (Excel)",
                data=excel_urls,
                file_name="enlaces_whatsapp.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            # TXT con URLs
            urls_text = '\n'.join([f"{data['display_info']}: {data['url']}" for data in st.session_state.whatsapp_urls])
            
            st.download_button(
                label="📝 Descargar URLs (TXT)",
                data=urls_text,
                file_name="enlaces_whatsapp.txt",
                mime="text/plain"
            )
    
    # Botón para nuevo proceso
    st.markdown("---")
    if st.button("🔄 Generar Nuevos Enlaces", type="secondary"):
        # Reiniciar para nuevo envío
        keys_to_reset = ['df', 'column_selected', 'numbers_validated', 'message_ready', 'urls_generated']
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
5. **Generar Enlaces** - Crea enlaces de WhatsApp
6. **Enviar Mensajes** - Usa los enlaces generados

### 📞 Formato de números:
- ✅ Correcto: 3008686725
- ❌ Incorrecto: 08686725, +573008686725

### 🔧 Variables de personalización:
Usa el nombre de la columna entre llaves:
- `{NOMBRE}` - Para nombre
- `{EMPRESA}` - Para empresa
- `{CIUDAD}` - Para ciudad

### 💡 Ventajas de este método:
- ✅ Funciona en cualquier dispositivo
- ✅ No requiere instalaciones adicionales
- ✅ Mayor control sobre cada envío
- ✅ Compatible con Streamlit Cloud
""")

st.sidebar.markdown("---")
st.sidebar.markdown("💡 **Tip:** Los enlaces se abren en WhatsApp Web automáticamente")
st.sidebar.markdown("---")
st.sidebar.markdown("🚀 **AutoWhatSend v2.0** - Generador de enlaces inteligente")
