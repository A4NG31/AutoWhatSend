# 📱 AutoWhatSend

Una aplicación web desarrollada con Streamlit para envío masivo de mensajes de WhatsApp personalizados desde bases de datos Excel. **Automatización inteligente para tu marketing digital.**

## 🚀 Características

- **Carga de archivos Excel** - Sube tu base de datos directamente desde la web
- **Validación automática** - Verifica que los números tengan formato colombiano válido
- **Mensajes personalizados** - Usa variables de tu base de datos en los mensajes
- **Vista previa en tiempo real** - Ve cómo se verá tu mensaje antes de enviarlo
- **Progreso en tiempo real** - Barra de progreso durante el envío
- **Reportes detallados** - Descarga reportes de envíos exitosos y fallidos
- **Interfaz intuitiva** - Proceso paso a paso fácil de seguir

## 📋 Requisitos

- Python 3.8 o superior
- Google Chrome (requerido por pywhatkit)
- WhatsApp Web configurado en tu navegador

## 🛠️ Instalación Local

1. Clona el repositorio:
```bash
git clone https://github.com/tu-usuario/AutoWhatSend.git
cd AutoWhatSend
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecuta la aplicación:
```bash
streamlit run app.py
```

## 🌐 Despliegue en Streamlit Cloud

1. Sube tu código a GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu repositorio de GitHub
4. Selecciona el archivo `app.py` como punto de entrada
5. ¡Listo! Tu aplicación estará disponible en línea

## 📊 Formato de Archivo Excel

Tu archivo Excel debe contener:

- **Una columna con números de teléfono** (formato: 3008686725)
- **Columnas adicionales opcionales** para personalización (NOMBRE, EMPRESA, CIUDAD, etc.)

### Ejemplo de estructura:
| NUMERO     | NOMBRE | EMPRESA    | CIUDAD |
|------------|--------|------------|---------|
| 3008686725 | Juan   | ABC Corp   | Bogotá |
| 3109876543 | María  | XYZ Ltd    | Medellín |

## ✨ Uso de Variables

Puedes personalizar tus mensajes usando variables de tu base de datos:

```
Hola {NOMBRE},

Te escribimos desde {EMPRESA} para invitarte a nuestro evento en {CIUDAD}.

¡Esperamos contar contigo!
```

## 🔧 Funcionalidades Principales

### 1. Carga de Base de Datos
- Sube archivos .xlsx
- Vista previa de los primeros 10 registros
- Selección de columna de números

### 2. Validación de Números
- Verifica formato colombiano (10 dígitos, empieza con 3)
- Muestra números válidos vs inválidos
- Opción de corregir y recargar

### 3. Personalización de Mensajes
- Editor de texto integrado
- Vista previa en tiempo real
- Inserción automática de variables

### 4. Envío Masivo
- Barra de progreso en tiempo real
- Manejo de errores automático
- Retrasos entre mensajes para evitar spam

### 5. Reportes
- Métricas de éxito/fallo
- Descarga de reportes en Excel
- Tasa de éxito calculada

## ⚠️ Consideraciones Importantes

1. **WhatsApp Web**: Debes tener WhatsApp Web abierto y logueado
2. **Límites de WhatsApp**: Respeta los límites de envío para evitar bloqueos
3. **Tiempo entre mensajes**: La app incluye pausas automáticas de 15 segundos
4. **Navegador**: Google Chrome es requerido para pywhatkit

## 🐛 Solución de Problemas

### Error: "Chrome not found"
- Instala Google Chrome en tu sistema
- Asegúrate de que Chrome esté en el PATH del sistema

### Error: "WhatsApp Web not logged in"
- Abre WhatsApp Web manualmente
- Escanea el código QR para iniciar sesión
- Mantén la pestaña abierta durante el envío

### Números no válidos
- Los números deben tener exactamente 10 dígitos
- Deben comenzar con 3 (números móviles colombianos)
- Formato correcto: 3008686725

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para cambios importantes:

1. Abre un issue primero para discutir los cambios
2. Haz fork del proyecto
3. Crea una rama para tu feature
4. Commit tus cambios
5. Push a la rama
6. Abre un Pull Request

## 📞 Soporte

Si tienes problemas o preguntas, abre un issue en GitHub o contacta al desarrollador.

---

**⚡ AutoWhatSend - Hecho con Streamlit y Python!** 🚀

*Automatiza tu comunicación, potencia tu negocio* 📈