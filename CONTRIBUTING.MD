# 🚀 Guía de Trabajo en Equipo con Git y GitHub

¡Bienvenido al equipo! Si nunca has usado Git o GitHub, no te preocupes. Esta guía te enseñará paso a paso cómo configurar tu entorno, crear tu propia rama y subir tus cambios sin romper el código de tus compañeros.

Sigue estas instrucciones al pie de la letra para que nuestro desarrollo sea fluido y sin errores.

---

## 📌 Configuración Inicial (Solo se hace la primera vez)

Antes de empezar, debes tener instalada la terminal de Git ([Git Bash](https://gitfor-windows.github.io/) en Windows o la Terminal en Mac/Linux) y haber clonado el repositorio en tu computadora.

Una vez que estés dentro de la carpeta del proyecto en tu terminal, sigue estos pasos para **crear tu propia rama con tu nombre**:

### Paso 1: Asegúrate de estar en la rama base (`dev`)
```bash
git checkout dev
```

### Paso 2: Trae los últimos cambios del servidor
```bash
git pull origin dev
```

### Paso 3: Crea y cámbiate a tu rama propia
Reemplaza `tu-nombre` por tu nombre real en minúsculas y sin espacios (ejemplo: `git checkout -b juan`).
```bash
git checkout -b tu-nombre
```
*💡 ¿Qué hace esto? Crea una copia exacta de la rama `dev` en este momento y te mete dentro de ella para que trabajes de forma segura.*

### Paso 4: Publica tu rama en GitHub
Para que tus compañeros y GitHub sepan que tu rama existe, súbela por primera vez con este comando:
```bash
git push -u origin tu-nombre
```

¡Listo! Ya tienes tu espacio de trabajo propio en tu computadora y en la web de GitHub.

---

## 📆 Rutina de Trabajo Diaria

Para evitar que tu código se quede desactualizado y tengas problemas al unirlo con el de los demás, sigue este ciclo **todos los días** antes de empezar a programar.

### ☀️ Por la mañana: Actualiza tu código
1. Cámbiate a la rama del equipo (`dev`):
   ```bash
   git checkout dev
   ```
2. Descarga lo que tus compañeros subieron ayer:
   ```bash
   git pull origin dev
   ```
3. Vuelve a tu rama propia:
   ```bash
   git checkout tu-nombre
   ```
4. Mete el código nuevo de tus compañeros dentro de tu rama:
   ```bash
   git merge dev
   ```
   *(Si la terminal te abre un editor de texto pidiendo un mensaje, solo escribe `:wq` y presiona Enter para guardar y salir).*

### 💻 Durante el día: Trabaja normalmente
Escribe tu código, crea tus archivos y haz tus pruebas dentro de tu rama propia. Tu código está aislado, así que no tengas miedo de experimentar.

### 🌙 Al terminar el día (o al finalizar una tarea): Guarda y sube tus cambios
1. Dile a Git qué archivos quieres guardar (el punto significa "todos los archivos"):
   ```bash
   git add .
   ```
2. Ponle un título/mensaje a tu avance (explica brevemente qué hiciste):
   ```bash
   git commit -m "Terminé el diseño de la barra de navegación"
   ```
3. Sube tus cambios a GitHub:
   ```bash
   git push origin tu-nombre
   ```

---

## 🤝 Cómo enviar tus cambios a la rama principal del equipo (`dev`)

Cuando termines una tarea por completo y quieras que tus compañeros tengan tus cambios en la rama `dev`, **no lo hagas desde la terminal**. Usaremos la web de GitHub para hacerlo de forma visual y segura.

1. Entra a nuestro repositorio en **GitHub**.
2. Verás un cuadro amarillo arriba que dice **"Compare & pull request"** al lado del nombre de tu rama. Haz clic ahí.
   * *Si no aparece, ve a la pestaña **Pull Requests** y haz clic en el botón verde **New Pull Request**.*
3. Configura las ramas de la siguiente manera:
   * **base:** `dev` (la rama del equipo que recibirá el código)
   * **compare:** `tu-nombre` (tu rama con el código nuevo)
4. Escribe un título y una descripción de lo que cambiaste.
5. Haz clic en el botón verde **"Create pull request"**.
6. Avisa al equipo por nuestro canal de comunicación. Otro miembro revisará tu código en la pestaña *Files changed* y, si todo está correcto, presionará el botón **"Merge pull request"** para unirlo oficialmente.

---

## 🚨 En caso de emergencia: Conflictos de Código (Merge Conflicts)

A veces, si tú y un compañero modifican **la misma línea del mismo archivo** al mismo tiempo, Git no sabrá cuál versión dejar y te mostrará un mensaje de alerta: `CONFLICT (content): Merge conflict in...`

Si esto te pasa al hacer el paso de `git merge dev`:
1. Abre el archivo que tiene el conflicto en tu editor de código (como VS Code).
2. Verás unas marcas extrañas como `<<<<<<< HEAD`, `=======`, y `>>>>>>> dev`.
3. Tu código estará arriba de la línea `=======` y el de tu compañero abajo.
4. **Habla con tu compañero** para decidir qué código se queda y cuál se borra.
5. Borra las líneas conflictivas que no sirvan y elimina las marcas (`<<<`, `===`, `>>>`).
6. Guarda el archivo, ve a la terminal y ejecuta:
   ```bash
   git add .
   git commit -m "Conflicto resuelto"
   git push origin tu-nombre
   ```