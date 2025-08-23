import streamlit as st
import pandas as pd
import pywhatkit as kit
import time
import re
from io import BytesIO
import traceback

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

def create_excel_download(data, filename):
    """Crea un archivo Excel para descarga"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        data.to_excel(writer, index=False, sheet_name='Datos')
    
    processed_data = output.getvalue()
    return processed_data

# Título principal
st.title("📱 AutoWhatSend")
st.markdown("*Envío masivo de mensajes de WhatsApp automatizado*")
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
        st.success(f"🎉 {len(valid_numbers)} números están listos para envío")
        
        # Mostrar muestra de números válidos
        if st.checkbox("Ver muestra de números válidos"):
            valid_sample = pd.DataFrame(valid_numbers[:10])
            st.dataframe(valid_sample)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Cargar Nueva Base", type="secondary"):
                # Reiniciar estados
                for key in ['df', 'column_selected', 'numbers_validated', 'message_ready', 'sending_complete']:
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

# Paso 5: Enviar mensajes
if st.session_state.get('message_ready', False):
    st.markdown("---")
    st.header("5️⃣ Enviar Mensajes")
    
    total_messages = len(st.session_state.valid_numbers)
    st.info(f"📊 Se enviarán mensajes a **{total_messages}** números válidos")
    
    if st.button("🚀 Iniciar Envío de Mensajes", type="primary"):
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
                
                # Calcular tiempo para envío (ahora + 1 minuto por mensaje)
                current_time = time.localtime()
                minutes_offset = i + 1
                target_minute = (current_time.tm_min + minutes_offset) % 60
                target_hour = (current_time.tm_hour + (current_time.tm_min + minutes_offset) // 60) % 24
                
                # Enviar mensaje
                whatsapp_number = number_info['whatsapp']
                kit.sendwhatmsg(whatsapp_number, personalized_message, target_hour, target_minute)
                
                successful_numbers.append({
                    'numero': whatsapp_number,
                    'indice': row_index,
                    'estado': 'Enviado'
                })
                
                # Actualizar progreso
                progress = (i + 1) / total_messages
                progress_bar.progress(progress)
                status_text.text(f"Enviando mensaje {i + 1} de {total_messages} - {whatsapp_number}")
                
                # Pausa entre mensajes
                time.sleep(15)
                
            except Exception as e:
                failed_numbers.append({
                    'numero': number_info['whatsapp'],
                    'indice': number_info['index'],
                    'error': str(e)
                })
                
                # Continuar con el siguiente
                progress = (i + 1) / total_messages
                progress_bar.progress(progress)
                status_text.text(f"Error en mensaje {i + 1} - Continuando...")
        
        # Guardar resultados en session state
        st.session_state.successful_numbers = successful_numbers
        st.session_state.failed_numbers = failed_numbers
        st.session_state.sending_complete = True
        
        st.success("🎉 **¡Envío completado!**")
        st.rerun()

# Paso 6: Resultados y reporte
if st.session_state.get('sending_complete', False):
    st.markdown("---")
    st.header("6️⃣ Resultados del Envío")
    
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

# Sidebar con información
st.sidebar.header("ℹ️ AutoWhatSend - Información")
st.sidebar.markdown("""
### 📋 Pasos del proceso:
1. **Cargar Base de Datos** - Sube tu archivo Excel
2. **Seleccionar Columna** - Elige la columna con números
3. **Validar Números** - Verifica formato colombiano
4. **Personalizar Mensaje** - Crea tu mensaje personalizado
5. **Enviar Mensajes** - Inicia el envío masivo
6. **Ver Resultados** - Revisa el reporte de envío

### 📞 Formato de números:
- ✅ Correcto: 300xxxxx25
- ❌ Incorrecto: 0xxxxx25, +57300xxxxx25

### 🔧 Variables de personalización:
Usa el nombre de la columna entre llaves:
- `{NOMBRE}` - Para nombre
- `{EMPRESA}` - Para empresa
- `{CIUDAD}` - Para ciudad
""")

st.sidebar.markdown("---")
st.sidebar.markdown("💡 **Tip:** Guarda una copia de tu base de datos antes de comenzar")
st.sidebar.markdown("---")
st.sidebar.markdown("🚀 **AutoWhatSend v1.0** - Automatización inteligente de WhatsApp")