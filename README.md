# Generador de Repertorio con Cifrado (Cifra Club a Word .docx)

Herramienta en Python para generar automáticamente un cancionero / cancionero de repertorio en formato Word (`.docx`) a partir de una lista de canciones, consultando la versión más popular en Cifra Club sin necesidad de Docker ni navegadores externos (Selenium).

## Características

- **Sin Docker ni Selenium**: Se conecta directamente a la API interna de Cifra Club y parsea el HTML server-side en milisegundos.
- **Formato profesional en Word (.docx)**:
  - Diagramación a **2 columnas** por carilla con márgenes ajustados (0.5 in).
  - Cada canción arranca siempre en una **página nueva**.
  - Tipografía monoespaciada (`Consolas`) para garantizar que los acordes mantengan su posición exacta sobre las sílabas.
  - Acordes destacados en **color naranja y estilo negrita** (`#E65100`).
  - Encabezados claros por tema con artista, título y tono original.
- **Filtro inteligente de tablaturas**: Remueve automáticamente punteos y líneas de cuerdas (`E|---...`) para dejar exclusivamente acordes y letras.
- **Caché local automática**: Almacena las canciones resueltas en `.cache_cifras/`. Al re-ejecutar agregando nuevas canciones a `canciones.txt`, solo descarga las nuevas y re-ensambla el Word completo en segundos.

## Requisitos

Python 3.10+ con las siguientes dependencias:

```bash
pip install requests beautifulsoup4 python-docx
```

## Uso

1. Edita el archivo `canciones.txt` colocando una canción por línea:
   ```text
   de musica ligera
   the scientist
   sweet child o mine
   ```

2. Ejecuta el generador:
   ```bash
   python main.py
   ```

3. Abrí `repertorio.docx` con Microsoft Word, LibreOffice o Google Docs.

### Opciones avanzadas de CLI

```bash
python main.py -i mis_temas.txt -o cancionero_acustico.docx --cache-dir .mi_cache
```

## Tests

Para correr la suite de pruebas unitarias y de integración:

```bash
python -m pytest
```
