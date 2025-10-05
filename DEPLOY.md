# 🚀 Guía de Despliegue Web - NASA Earth Change

## 🌐 Plataformas Recomendadas (Gratuitas)

### 1. 🚂 **Railway** (Recomendado)
**✅ Pros:** Fácil configuración, base de datos incluida, dominio personalizado
**📋 Pasos:**

1. **Crear cuenta** en [railway.app](https://railway.app)
2. **Conectar GitHub:**
   - Fork este repositorio
   - En Railway: "New Project" → "Deploy from GitHub repo"
   - Selecciona tu fork
3. **Configurar variables de entorno:**
   ```
   GEMINI_API_KEY=tu_clave_gemini
   OPENWEATHER_API_KEY=tu_clave_openweather
   NASA_FIRMS_API_KEY=tu_clave_nasa
   OPENAQ_API_KEY=tu_clave_openaq
   FLASK_DEBUG=False
   ```
4. **Deploy automático** ✅ ¡Listo!

**🔗 URL:** `https://tu-app.railway.app`

---

### 2. 🎨 **Render** 
**✅ Pros:** SSL gratis, fácil configuración, buena documentación
**📋 Pasos:**

1. **Crear cuenta** en [render.com](https://render.com)
2. **Nuevo Web Service:**
   - Connect GitHub repository
   - Branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python mexico_interactive_map.py`
3. **Variables de entorno** (Environment):
   ```
   GEMINI_API_KEY=tu_clave_gemini
   OPENWEATHER_API_KEY=tu_clave_openweather
   NASA_FIRMS_API_KEY=tu_clave_nasa
   OPENAQ_API_KEY=tu_clave_openaq
   FLASK_DEBUG=False
   FLASK_HOST=0.0.0.0
   ```
4. **Deploy** ✅

**🔗 URL:** `https://tu-app.onrender.com`

---

### 3. ⚡ **Vercel**
**✅ Pros:** Deploy ultra rápido, CDN global
**📋 Pasos:**

1. **Instalar Vercel CLI:**
   ```bash
   npm i -g vercel
   ```
2. **En tu proyecto:**
   ```bash
   vercel
   ```
3. **Configurar variables** en dashboard de Vercel
4. **Deploy** ✅

**🔗 URL:** `https://tu-app.vercel.app`

---

### 4. 💜 **Heroku** (Requiere tarjeta)
**📋 Pasos:**

1. **Instalar Heroku CLI**
2. **Login y crear app:**
   ```bash
   heroku login
   heroku create tu-app-name
   ```
3. **Configurar variables:**
   ```bash
   heroku config:set GEMINI_API_KEY=tu_clave
   heroku config:set OPENWEATHER_API_KEY=tu_clave
   # ... otras variables
   ```
4. **Deploy:**
   ```bash
   git push heroku main
   ```

---

## 🔑 Variables de Entorno Obligatorias

```env
# MÍNIMO REQUERIDO
GEMINI_API_KEY=tu_clave_gemini_aqui
OPENWEATHER_API_KEY=tu_clave_openweather_aqui

# RECOMENDADO
NASA_FIRMS_API_KEY=tu_clave_nasa_aqui
OPENAQ_API_KEY=tu_clave_openaq_aqui

# CONFIGURACIÓN PRODUCCIÓN
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
PORT=5000
```

## 📋 Checklist Antes del Deploy

- [ ] ✅ Todas las claves de API configuradas
- [ ] ✅ `.env` NO incluido en el repositorio
- [ ] ✅ `requirements.txt` actualizado
- [ ] ✅ `Procfile` presente
- [ ] ✅ `runtime.txt` con versión de Python
- [ ] ✅ Código probado localmente
- [ ] ✅ Variables de entorno configuradas en la plataforma

## 🛠️ Solución de Problemas

### ❌ Error: Application failed to start
```bash
# Verifica logs:
heroku logs --tail  # Heroku
# O revisa logs en dashboard de Railway/Render
```

### ❌ Error: Module not found
- Verifica que `requirements.txt` esté completo
- Ejecuta `pip freeze > requirements.txt` localmente

### ❌ APIs no funcionan
- Verifica variables de entorno en dashboard
- Comprueba que las claves sean válidas
- Revisa límites de uso de las APIs

### ❌ Error 503/504
- Las APIs externas pueden tener límites
- Reinicia el servicio
- Verifica logs de errores

## 🚀 Deploy Rápido (Railway)

```bash
# 1. Subir a GitHub
git add .
git commit -m "Configuración para deploy"
git push origin main

# 2. Ir a railway.app
# 3. New Project → GitHub Repo
# 4. Configurar variables de entorno
# 5. ¡Deploy automático!
```

## 🔗 URLs de las Plataformas

- **Railway:** https://railway.app
- **Render:** https://render.com  
- **Vercel:** https://vercel.com
- **Heroku:** https://heroku.com

---

**💡 Tip:** Railway es la opción más fácil para principiantes. Render es excelente para aplicaciones más complejas.

**⚠️ Importante:** Todas las APIs gratuitas tienen límites de uso. Monitorea tu consumo.

**🎉 ¡Una vez desplegado, tu aplicación estará disponible 24/7 en la web!**