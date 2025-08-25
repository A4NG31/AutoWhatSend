import streamlit as st
import pandas as pd
import time
import re
from io import BytesIO
import urllib.parse
import webbrowser

# Configuración de la página
st.set_page_config(
    page_title="AutoWhatSend",
    page_icon="📱",
    layout="wide"
)

# Función para detectar si pywhatkit está disponible
@st.cache_data
def check_pywhatkit_available():
    try:
        import pywhatkit as kit
        return True, kit
    except ImportError:
        return False, None
    except Exception as e:
        return False, None

# Detectar disponibilidad de pywhatkit
PYWHATKIT_AVAILABLE, pywhatkit_module = check_pywhatkit_available()

# Detectar si estamos en Streamlit Cloud
def is_streamlit_cloud():
    """Detecta si estamos ejecutando en Streamlit Cloud"""
    import os
    return os.getenv('STREAMLIT_SHARING_MODE') is not None or 'streamlit.app' in str(os.getenv('HOSTNAME', ''))

RUNNING_IN_CLOUD = is_streamlit_cloud()

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
if 'urls_generated' not in st.session_state:
    st.session_state.urls_generated = False
if 'failed_numbers' not in st.session_state:
    st.session_state.failed_numbers = []
if 'successful_numbers' not in st.session_state:
    st.session_state.successful_numbers = []
if 'whatsapp_urls' not in st.session_state:
    st.session_state.whatsapp_urls = []

def validate_colombian_number(number):
    """Valida que el número sea un número colombiano válido"""
    number_str = str(number).strip()
    clean_number = re.sub(r'[^\d]', '', number_str)
    
    if len(clean_number) == 10 and clean_number.startswith('3'):
        return True, clean_number
    
    return False, clean_number

def format_number_for_whatsapp(number):
    """Formatea el número para WhatsApp con código de país de Colombia"""
    return f"+57{number}"

def format_number_for_url(number):
    """Formatea el número para URLs de WhatsApp (sin +)"""
    return f"57{number}"

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

def send_with_pywhatkit_local(valid_numbers, df, message_template):
    """Función para envío local con pywhatkit (solo funciona localmente)"""
    if not PYWHATKIT_AVAILABLE or RUNNING_IN_CLOUD:
        return False, "pywhatkit no disponible o ejecutando en la nube"
    
    successful_numbers = []
    failed_numbers = []
    
    # Contenedores para mostrar progreso
    progress_bar = st.progress(0)
    status_text = st.empty()
    current_message = st.empty()
    
    current_time = time.localtime()
    
    for i, number_info in enumerate(valid_numbers):
        try:
            row_index = number_info['index']
            row_data = df.iloc[row_index]
            
            # Personalizar mensaje
            personalized_message = message_template
            for col in df.columns:
                value = str(row_data[col]) if pd.notna(row_data[col]) else ""
                personalized_message = personalized_message.replace(f"{{{col}}}", value)
            
            # Calcular tiempo
            minutes_offset = i + 1
            target_minute = (current_time.tm_min + minutes_offset) % 60
            target_hour = (current_time.tm_hour + (current_time.tm_min + minutes_offset) // 60) % 24
            
            current_message.text_area(
                f"📱 Enviando a {number_info['whatsapp']}:",
                personalized_message,
                height=100,
                disabled=True
            )
            
            # Enviar con pywhatkit
            whatsapp_number = number_info['whatsapp']
            pywhatkit_module.sendwhatmsg(whatsapp_number, personalized_message, target_hour, target_minute)
            
            successful_numbers.append({
                'numero': whatsapp_number,
                'indice': row_index,
                'estado': 'Enviado exitosamente',
                'hora_programada': f"{target_hour:02d}:{target_minute:02d}",
                'mensaje': personalized_message
            })
            
            progress = (i + 1) / len(valid_numbers)
            progress_bar.progress(progress)
            status_text.success(f"✅ Mensaje {i + 1} de {len(valid_numbers)} programado")
            
            if i < len(valid_numbers) - 1:
                for remaining in range(15, 0, -1):
                    status_text.info(f"⏱️ Esperando {remaining} segundos...")
                    time.sleep(1)
                    
        except Exception as e:
            failed_numbers.append({
                'numero': number_info['whatsapp'],
                'indice': number_info['index'],
                'error': str(e)
            })
            
            progress = (i + 1) / len(valid_numbers)
            progress_bar.progress(progress)
            status_text.error(f"❌ Error en mensaje {i + 1}")
    
    current_message.empty()
    return True, {'successful': successful_numbers, 'failed': failed_numbers}

# Título principal
st.title("📱 AutoWhatSend")

# Mostrar modo de funcionamiento
if RUNNING_IN_CLOUD:
    st.info("🌐 **Ejecutando en Streamlit Cloud** - Solo modo enlaces disponible")
    st.markdown("*Los enlaces se abrirán automáticamente en WhatsApp Web*")
elif PYWHATKIT_AVAILABLE:
    st.success("🖥️ **Ejecutando localmente** - Envío automático disponible")
else:
    st.warning("🖥️ **Ejecutando localmente** - Solo modo enlaces (instala pywhatkit para envío automático)")

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
                'whatsapp': format_number_for_whatsapp(clean_number),
                'url_format': format_number_for_url(clean_number)
            })
        else:
            invalid_numbers.append({
                'index': index,
                'original': number,
                'reason': 'Formato inválido'
            })
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("✅ Números Válidos", len(valid_numbers))
    with col2:
        st.metric("❌ Números Inválidos", len(invalid_numbers))
    
    if invalid_numbers:
        st.warning("⚠️ Números con formato inválido encontrados")
        if st.checkbox("Ver números inválidos"):
            st.dataframe(pd.DataFrame(invalid_numbers))
    
    if valid_numbers:
        st.success(f"🎉 {len(valid_numbers)} números listos para envío")
        
        if st.button("✅ Continuar con Estos Números", type="primary"):
            st.session_state.valid_numbers = valid_numbers
            st.session_state.numbers_validated = True
            st.rerun()

# Paso 4: Personalizar mensaje
if st.session_state.get('numbers_validated', False):
    st.markdown("---")
    st.header("4️⃣ Personalizar Mensaje")
    
    df = st.session_state.df
    available_columns = [col for col in df.columns if col != st.session_state.number_column]
    
    st.info("💡 **Tip:** Usa variables de tu base escribiendo {NOMBRE_COLUMNA}")
    
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

    message_template = st.text_area(
        "Escribe tu mensaje:",
        value=default_message,
        height=300
    )
    
    # Vista previa
    st.subheader("👁️ Vista Previa")
    if len(st.session_state.valid_numbers) > 0:
        first_valid_index = st.session_state.valid_numbers[0]['index']
        sample_row = df.iloc[first_valid_index]
        
        preview_message = message_template
        for col in df.columns:
            value = str(sample_row[col]) if pd.notna(sample_row[col]) else ""
            preview_message = preview_message.replace(f"{{{col}}}", value)
        
        st.text_area("Así se verá:", preview_message, height=200, disabled=True)
    
    if st.button("📝 Confirmar Mensaje", type="primary"):
        st.session_state.message_template = message_template
        st.session_state.message_ready = True
        st.rerun()

# Paso 5: Envío (automático local o enlaces para cloud)
if st.session_state.get('message_ready', False):
    st.markdown("---")
    
    if not RUNNING_IN_CLOUD and PYWHATKIT_AVAILABLE:
        # MODO LOCAL - Envío automático con pywhatkit
        st.header("5️⃣ Envío Automático (Local)")
        
        total_messages = len(st.session_state.valid_numbers)
        st.info(f"📊 Se enviarán {total_messages} mensajes automáticamente")
        st.warning("⚠️ **Asegúrate de tener WhatsApp Web abierto**")
        
        if st.button("🚀 Iniciar Envío Automático", type="primary"):
            success, result = send_with_pywhatkit_local(
                st.session_state.valid_numbers,
                st.session_state.df,
                st.session_state.message_template
            )
            
            if success:
                st.session_state.successful_numbers = result['successful']
                st.session_state.failed_numbers = result['failed']
                st.session_state.sending_complete = True
                st.success("🎉 ¡Envío completado!")
                st.rerun()
            else:
                st.error(f"Error: {result}")
    
    else:
        # MODO CLOUD - Generación de enlaces con apertura automática
        st.header("5️⃣ Generar Enlaces de WhatsApp")
        
        total_messages = len(st.session_state.valid_numbers)
        st.info(f"📊 Se generarán {total_messages} enlaces de WhatsApp")
        
        # Opción de apertura automática
        auto_open = st.checkbox(
            "🚀 Abrir enlaces automáticamente (uno por uno)",
            value=True,
            help="Los enlaces se abrirán automáticamente en WhatsApp Web con pausa entre cada uno"
        )
        
        if auto_open:
            delay_seconds = st.slider(
                "⏱️ Segundos entre cada apertura:",
                min_value=3,
                max_value=30,
                value=5,
                help="Tiempo de espera entre cada enlace"
            )
        
        if st.button("🔗 Generar y Enviar Enlaces", type="primary"):
            df = st.session_state.df
            valid_numbers = st.session_state.valid_numbers
            message_template = st.session_state.message_template
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            whatsapp_urls = []
            
            for i, number_info in enumerate(valid_numbers):
                try:
                    row_index = number_info['index']
                    row_data = df.iloc[row_index]
                    
                    # Personalizar mensaje
                    personalized_message = message_template
                    for col in df.columns:
                        value = str(row_data[col]) if pd.notna(row_data[col]) else ""
                        personalized_message = personalized_message.replace(f"{{{col}}}", value)
                    
                    # Generar URL
                    url_number = number_info['url_format']
                    url = generate_whatsapp_url(url_number, personalized_message)
                    
                    display_info = number_info['whatsapp']
                    if 'NOMBRE' in df.columns and pd.notna(row_data.get('NOMBRE')):
                        display_info += f" - {row_data['NOMBRE']}"
                    
                    whatsapp_urls.append({
                        'numero': number_info['whatsapp'],
                        'url': url,
                        'mensaje': personalized_message,
                        'display_info': display_info
                    })
                    
                    progress = (i + 1) / len(valid_numbers)
                    progress_bar.progress(progress)
                    status_text.text(f"Generando enlace {i + 1} de {len(valid_numbers)}")
                    
                    # Si está habilitada la apertura automática
                    if auto_open:
                        status_text.success(f"🚀 Abriendo WhatsApp para {display_info}")
                        
                        # Crear componente HTML que abre el enlace automáticamente
                        st.markdown(
                            f"""
                            <script>
                                window.open('{url}', '_blank');
                            </script>
                            <p>📱 <strong>Enlace abierto para:</strong> {display_info}</p>
                            <p><a href="{url}" target="_blank">🔗 Abrir manualmente si no se abrió</a></p>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        if i < len(valid_numbers) - 1:
                            for remaining in range(delay_seconds, 0, -1):
                                status_text.info(f"⏱️ Siguiente enlace en {remaining} segundos...")
                                time.sleep(1)
                
                except Exception as e:
                    st.error(f"Error generando enlace para {number_info['whatsapp']}: {str(e)}")
            
            st.session_state.whatsapp_urls = whatsapp_urls
            st.session_state.urls_generated = True
            
            if auto_open:
                st.success("🎉 **¡Todos los enlaces fueron abiertos automáticamente!**")
                st.info("📱 Revisa las pestañas de tu navegador - cada una tiene un chat de WhatsApp listo para enviar")
            else:
                st.success("🎉 **¡Enlaces generados exitosamente!**")
            
            st.rerun()

# Mostrar resultados
if st.session_state.get('sending_complete', False):
    st.markdown("---")
    st.header("6️⃣ Reporte de Envío Automático")
    
    successful_count = len(st.session_state.successful_numbers)
    failed_count = len(st.session_state.failed_numbers)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Exitosos", successful_count)
    with col2:
        st.metric("❌ Fallidos", failed_count)
    with col3:
        total = successful_count + failed_count
        rate = (successful_count / total * 100) if total > 0 else 0
        st.metric("📊 Éxito", f"{rate:.1f}%")
    
    # Mostrar detalles en pestañas
    if successful_count > 0 or failed_count > 0:
        tab1, tab2 = st.tabs(["✅ Exitosos", "❌ Fallidos"])
        
        with tab1:
            if successful_count > 0:
                success_df = pd.DataFrame(st.session_state.successful_numbers)
                st.dataframe(success_df)
                
                excel_data = create_excel_download(success_df, "exitosos.xlsx")
                st.download_button("📥 Descargar Exitosos", excel_data, "exitosos.xlsx")
        
        with tab2:
            if failed_count > 0:
                failed_df = pd.DataFrame(st.session_state.failed_numbers)
                st.dataframe(failed_df)
                
                excel_data = create_excel_download(failed_df, "fallidos.xlsx")
                st.download_button("📥 Descargar Fallidos", excel_data, "fallidos.xlsx")

elif st.session_state.get('urls_generated', False):
    st.markdown("---")
    st.header("6️⃣ Enlaces Generados")
    
    urls_count = len(st.session_state.whatsapp_urls)
    st.success(f"✅ Se generaron {urls_count} enlaces")
    
    st.info("💡 **Tip:** Si activaste la apertura automática, revisa las pestañas de tu navegador")
    
    # Mostrar algunos enlaces como botones
    st.subheader("🔗 Enlaces de WhatsApp")
    
    for i, data in enumerate(st.session_state.whatsapp_urls[:5]):  # Mostrar primeros 5
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{i+1}.** {data['display_info']}")
        with col2:
            st.link_button(
                "📱 Abrir WhatsApp",
                data['url'],
                use_container_width=True
            )
    
    if len(st.session_state.whatsapp_urls) > 5:
        st.write(f"... y {len(st.session_state.whatsapp_urls) - 5} enlaces más")
    
    # Descargar todos los enlaces
    all_urls_text = '\n'.join([f"{data['display_info']}: {data['url']}" for data in st.session_state.whatsapp_urls])
    st.download_button(
        "📥 Descargar Todos los Enlaces",
        all_urls_text,
        "enlaces_whatsapp.txt"
    )

# Botón para reiniciar
if st.session_state.get('sending_complete', False) or st.session_state.get('urls_generated', False):
    st.markdown("---")
    if st.button("🔄 Procesar Nueva Base", type="primary"):
        for key in ['df', 'column_selected', 'numbers_validated', 'message_ready', 'sending_complete', 'urls_generated']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Sidebar
st.sidebar.header("ℹ️ Información")

if RUNNING_IN_CLOUD:
    st.sidebar.info("🌐 **Streamlit Cloud**")
    st.sidebar.markdown("✅ Enlaces con apertura automática")
    st.sidebar.markdown("❌ pywhatkit no funciona en la nube")
elif PYWHATKIT_AVAILABLE:
    st.sidebar.success("🖥️ **Local + pywhatkit**")
    st.sidebar.markdown("✅ Envío automático real")
else:
    st.sidebar.warning("🖥️ **Solo enlaces locales**")
    st.sidebar.markdown("Instala: `pip install pywhatkit`")

st.sidebar.markdown("""
### 📋 Funcionalidades:

**🌐 En Streamlit Cloud:**
- Apertura automática de enlaces
- Un enlace por pestaña del navegador
- Control de tiempo entre aperturas
- Compatible con móviles

**🖥️ En local con pywhatkit:**
- Envío automático real
- Control total de WhatsApp Web
- Reportes detallados
- Sin intervención manual

### 📞 Formato números:
✅ 3008686725 (10 dígitos, empiece con 3)
❌ 8686725, +573008686725

### 🔧 Variables:
`{NOMBRE}`, `{EMPRESA}`, etc.
""")

st.sidebar.markdown("---")
st.sidebar.success("🚀 **AutoWhatSend v5.0** - Híbrido Cloud/Local")
