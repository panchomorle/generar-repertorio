# Generador de Repertorio con Cifrado (Cifra Club a Word .docx)

Aplicación de escritorio en Python para buscar canciones en Cifra Club y generar automáticamente un cancionero / repertorio en Word (`.docx`) diagramado a 2 columnas con acordes en negrita y naranja.

Disponible tanto como **aplicación gráfica de escritorio (.exe para Windows)** como **interfaz por línea de comandos (CLI)**.

## Características

- **Aplicación de Escritorio con Interfaz Gráfica (CustomTkinter)**:
  - Búsqueda interactiva en tiempo real sobre Cifra Club (previsualización de artista y tema).
  - Gestión de **Setlist** ordenada (agregar, reordenar con flechas, eliminar).
  - **Persistencia automática**: Recuerda las canciones elegidas entre aperturas y permite exportar/importar listas en formato JSON.
  - Generación en hilo secundario (background thread) con barra de progreso en vivo para una UI siempre fluida.
  - Acceso directo para **Abrir documento (.docx)** y **Abrir en explorador de Windows** al finalizar.
- **Formato profesional en Word (.docx)**:
  - Diagramación a **2 columnas** por carilla con márgenes ajustados (0.5 in).
  - Cada canción arranca siempre en una **página nueva**.
  - Tipografía monoespaciada (`Consolas`) para garantizar alineación precisa de acordes sobre la letra.
  - Acordes destacados en **color naranja y estilo negrita** (`#E65100`).
  - Encabezados claros por tema con artista, título y tono original.
- **Filtro inteligente de tablaturas**: Remueve automáticamente punteos y líneas de cuerdas (`E|---...`) para dejar exclusivamente acordes y letras.
- **Caché local automática**: Almacena las canciones resueltas en `.cache_cifras/`. Si ya descargaste un tema, no vuelve a consultar la red.

---

## Descargas (Windows .exe)

Podes descargar el ejecutable listo para usar directamente desde la sección de **[Releases](https://github.com/panchomorle/generar-repertorio/releases)**. No requiere tener Python instalado.

---

## Uso desde código fuente

### Requisitos

Python 3.10+ en Windows, Linux o macOS.

```bash
pip install -r requirements.txt
```

### Ejecutar la Aplicación Gráfica (GUI)

```bash
python main.py
```

### Ejecutar en modo Línea de Comandos (CLI)

Podés seguir usando la herramienta por terminal indicando flags como `-i` o `--cli`:

```bash
python main.py -i canciones.txt -o cancionero.docx
```

---

## Compilación local de ejecutable (.exe)

Para compilar el `.exe` autónomo en tu máquina Windows con PyInstaller:

```cmd
build.bat
```

El ejecutable se generará en `dist\GeneradorRepertorio.exe`.

---

## Integración Continua y Releases Automáticos

El repositorio cuenta con un workflow de **GitHub Actions** (`.github/workflows/release.yml`) que compila automáticamente el ejecutable en un runner Windows puro y lo publica en **GitHub Releases** cada vez que se sube un tag de versión:

```bash
git tag v1.0.0
git push --tags
```

---

## Tests

Para correr la suite de pruebas automatizadas:

```bash
pytest
```
