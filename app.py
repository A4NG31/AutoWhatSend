import streamlit as st
import pandas as pd
import time
import re
from io import BytesIO
import urllib.parse
import subprocess
import sys
import os

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
if 'send_method' not in st.session_state:
    st.session_state.send_method = "auto" if PYWHATKIT_AVAILABLE else "links"

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

# Mostrar método disponible
if PYWHATKIT_AVAILABLE:
    st.markdown("*🚀 Envío automático de WhatsApp disponible*")
    st.success("✅ **Modo Automático Activado** - Los mensajes se enviarán automáticamente")
else:
    st.markdown("*🔗 Generador de enlaces de WhatsApp*")
    st.info("ℹ️ **Modo Enlaces** - Se generarán enlaces para envío manual (Compatible con Streamlit Cloud)")

st.markdown("---")

# Selector de método si pywhatkit está disponible
if PYWHATKIT_AVAILABLE:
    st.header("⚙️ Método de Envío")
    send_method = st.radio(
        "¿Cómo quieres enviar los mensajes?",
        options=["auto", "links"],
        format_func=lambda x: "🚀 Envío Automático (recomendado)" if x == "auto" else "🔗 Generar Enlaces Manuales",
        help="Envío automático usa pywhatkit para enviar directamente. Enlaces requiere clic manual pero es más seguro."
    )
    st.session_state.send_method = send_method
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
                'whatsapp': format_number_for_whatsapp(clean_number),
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
        send_text = "envío automático" if st.session_state.send_method == "auto" else "generar enlaces"
        st.success(f"🎉 {len(valid_numbers)} números están listos para {send_text}")
        
        # Mostrar muestra de números válidos
        if st.checkbox("Ver muestra de números válidos"):
            valid_sample = pd.DataFrame(valid_numbers[:10])
            st.dataframe(valid_sample)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Cargar Nueva Base", type="secondary"):
                # Reiniciar estados
                keys_to_reset = ['df', 'column_selected', 'numbers_validated', 'message_ready', 'sending_complete', 'urls_generated']
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

# Paso 5A: Envío automático (si está disponible pywhatkit)
if st.session_state.get('message_ready', False) and st.session_state.send_method == "auto" and PYWHATKIT_AVAILABLE:
    st.markdown("---")
    st.header("5️⃣ Envío Automático de Mensajes")
    
    total_messages = len(st.session_state.valid_numbers)
    st.info(f"📊 Se enviarán mensajes automáticamente a **{total_messages}** números válidos")
    
    st.warning("⚠️ **Importante:** Asegúrate de tener WhatsApp Web abierto y logueado en Chrome")
    
    if st.button("🚀 Iniciar Envío Automático", type="primary"):
        df = st.session_state.df
        valid_numbers = st.session_state.valid_numbers
        message_template = st.session_state.message_template
        
        # Contenedores para mostrar progreso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        successful_numbers = []
        failed_numbers = []
        
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
                
                # Calcular tiempo para envío (ahora + minutos de offset)
                current_time = time.localtime()
                minutes_offset = i + 1
                target_minute = (current_time.tm_min + minutes_offset) % 60
                target_hour = (current_time.tm_hour + (current_time.tm_min + minutes_offset) // 60) % 24
                
                # Enviar mensaje usando pywhatkit
                whatsapp_number = number_info['whatsapp']
                pywhatkit_module.sendwhatmsg(whatsapp_number, personalized_message, target_hour, target_minute)
                
                successful_numbers.append({
                    'numero': whatsapp_number,
                    'indice': row_index,
                    'estado': 'Enviado',
                    'mensaje': personalized_message
                })
                
                # Actualizar progreso
                progress = (i + 1) / total_messages
                progress_bar.progress(progress)
                status_text.text(f"✅ Mensaje enviado {i + 1} de {total_messages} - {whatsapp_number}")
                
                # Pausa entre mensajes
                time.sleep(15)
                
            except Exception as e:
                failed_numbers.append({
                    'numero': number_info['whatsapp'],
                    'indice': number_info['index'],
                    'error': str(e),
                    'mensaje': personalized_message if 'personalized_message' in locals() else message_template
                })
                
                # Continuar con el siguiente
                progress = (i + 1) / total_messages
                progress_bar.progress(progress)
                status_text.text(f"❌ Error en mensaje {i + 1} - Continuando...")
        
        # Guardar resultados en session state
        st.session_state.successful_numbers = successful_numbers
        st.session_state.failed_numbers = failed_numbers
        st.session_state.sending_complete = True
        
        progress_bar.progress(1.0)
        status_text.text("🎉 ¡Envío completado!")
        st.success("🎉 **¡Envío automático completado!**")
        st.rerun()

# Paso 5B: Generar enlaces (modo alternativo)
elif st.session_state.get('message_ready', False) and st.session_state.send_method == "links":
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
                url_number = number_info['url_format']
                url = generate_whatsapp_url(url_number, personalized_message)
                
                # Crear información para mostrar
                display_info = number_info['whatsapp']
                if 'NOMBRE' in df.columns and pd.notna(row_data.get('NOMBRE')):
                    display_info += f" - {row_data['NOMBRE']}"
                if 'EMPRESA' in df.columns and pd.notna(row_data.get('EMPRESA')):
                    display_info += f" ({row_data['EMPRESA']})"
                
                whatsapp_urls.append({
                    'numero': number_info['whatsapp'],
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

# Paso 6A: Resultados del envío automático
if st.session_state.get('sending_complete', False):
    st.markdown("---")
    st.header("6️⃣ Resultados del Envío Automático")
    
    successful_count = len(st.session_state.successful_numbers)
    failed_count = len(st.session_state.failed_numbers)
    total_count = successful_count + failed_count
    
    # Mostrar métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("✅ Envíos Exitosos", successful_count)
        
    with col2:
        st.metric("❌ Envíos Fallidos", failed_count)
        
    with col3:
        success_rate = (successful_count / total_count * 100) if total_count > 0 else 0
        st.metric("📊 Tasa de Éxito", f"{success_rate:.1f}%")
    
    # Botones de acción
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Enviar Nuevos Mensajes"):
            # Reiniciar para nuevo envío
            keys_to_reset = ['df', 'column_selected', 'numbers_validated', 'message_ready', 'sending_complete']
            for key in keys_to_reset:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col2:
        if failed_count > 0:
            if st.button("📋 Ver Números Fallidos"):
                st.subheader("📋 Reporte de Números Fallidos")
                failed_df = pd.DataFrame(st.session_state.failed_numbers)
                st.dataframe(failed_df, use_container_width=True)
                
                # Opción de descarga
                excel_data = create_excel_download(failed_df, "numeros_fallidos.xlsx")
                st.download_button(
                    label="📥 Descargar Números Fallidos (Excel)",
                    data=excel_data,
                    file_name="numeros_fallidos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col3:
        if successful_count > 0:
            if st.button("📈 Ver Números Exitosos"):
                st.subheader("📈 Reporte de Números Exitosos")
                success_df = pd.DataFrame(st.session_state.successful_numbers)
                st.dataframe(success_df, use_container_width=True)
                
                # Opción de descarga
                excel_data = create_excel_download(success_df, "numeros_exitosos.xlsx")
                st.download_button(
                    label="📥 Descargar Números Exitosos (Excel)",
                    data=excel_data,
                    file_name="numeros_exitosos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# Paso 6B: Mostrar enlaces generados
elif st.session_state.get('urls_generated', False):
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

# Mostrar estado actual
if PYWHATKIT_AVAILABLE:
    st.sidebar.success("🚀 **Modo Automático Disponible**")
    st.sidebar.markdown("pywhatkit está instalado")
else:
    st.sidebar.info("🔗 **Modo Enlaces Activo**")
    st.sidebar.markdown("Para envío automático, instala: `pip install pywhatkit`")

st.sidebar.markdown("""
### 📋 Cómo funciona:
1. **Cargar Base de Datos** - Sube tu archivo Excel
2. **Seleccionar Columna** - Elige la columna con números
3. **Validar Números** - Verifica formato colombiano
4. **Personalizar Mensaje** - Crea tu mensaje personalizado
5. **Enviar/Generar** - Envío automático o enlaces
6. **Ver Resultados** - Revisa el reporte

### 📞 Formato de números:
- ✅ Correcto: 3008686725
- ❌ Incorrecto: 08686725, +573008686725

### 🔧 Variables de personalización:
Usa el nombre de la columna entre llaves:
- `{NOMBRE}` - Para nombre
- `{EMPRESA}` - Para empresa
- `{CIUDAD}` - Para ciudad
""")

if PYWHATKIT_AVAILABLE:
    st.sidebar.markdown("""
### 🚀 Envío Automático:
- ✅ Envío directo a WhatsApp Web
- ✅ Progreso en tiempo real
- ⚠️ Requiere Chrome y WhatsApp Web logueado
- 📱 Pausa de 15 segundos entre mensajes
""")
else:
    st.sidebar.markdown("""
### 🔗 Modo Enlaces:
- ✅ Funciona en cualquier dispositivo
- ✅ Compatible con Streamlit Cloud
- ✅ Mayor control sobre cada envío
- 🔒 Más seguro (sin automatización)
""")

st.sidebar.markdown("---")
st.sidebar.markdown("💡 **Tip:** Para usar localmente con envío automático, instala pywhatkit")
st.sidebar.markdown("---")
st.sidebar.markdown("🚀 **AutoWhatSend v3.0** - Híbrido inteligente")
