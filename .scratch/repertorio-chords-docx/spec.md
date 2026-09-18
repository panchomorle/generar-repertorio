# Spec: Generador de Repertorio con Cifrado desde Cifra Club a Word (.docx)

Status: ready-for-agent

## Problem Statement

Los músicos y guitarristas que desean armar cancioneros o repertorios impresos o digitales enfrentan una tarea manual tediosa: buscar tema por tema en Cifra Club, copiar la letra, pegar los acordes, mantener la alineación vertical de cada acorde sobre su sílaba correspondiente, colorear los acordes a mano para distinguirlos y armar la diagramación a dos columnas para aprovechar el papel.

Las soluciones automatizadas de scraping existentes en la comunidad (como `code4music/cifraclub-api`) obligan a levantar contenedores Docker con Selenium y navegadores headless, agregando una sobrecarga excesiva, lentitud y fragilidad para una tarea que debería ser inmediata y local.

## Solution

Un script/CLI en Python liviano y directo que toma una lista de canciones en texto plano (`canciones.txt`), consulta la API interna Solr de Cifra Club para rankear automáticamente el resultado más popular de cada búsqueda, extrae los acordes y la letra directamente del HTML server-side, filtra las líneas de tablatura invasivas, persiste cada canción resuelta en una caché local en JSON (garantizando idempotencia y re-ejecución instantánea) y genera un documento Word (`repertorio.docx`) profesional a dos columnas por carilla, con cada canción comenzando en una página nueva, tipografía monoespaciada Consolas y acordes en negrita color naranja.

## User Stories

1. Como músico, quiero listar nombres de canciones en un archivo `canciones.txt` con formato libre (ej. "de musica ligera", "coldplay the scientist"), para armar mi repertorio sin tener que buscar URLs exactas a mano.
2. Como usuario, quiero que el sistema seleccione automáticamente la versión más popular en Cifra Club para cada búsqueda, para obtener las versiones estándar y reconocidas de los temas.
3. Como usuario, quiero que cada canción descargada se guarde en una caché local (`.cache_cifras/`), para que re-ejecutar el programa no vuelva a consultar la web para temas ya procesados.
4. Como usuario, quiero poder agregar nuevas canciones al `canciones.txt` y re-ejecutar el script, para que solo descargue las nuevas y re-genere el documento Word completo.
5. Como guitarrista, quiero que cada canción comience siempre en una carilla/página nueva del Word, para poder tocar en vivo sin saltos de página incómodos en medio de un tema.
6. Como guitarrista, quiero que las líneas de tablatura (solos/intros de cuerdas tipo `E|---...`) se filtren automáticamente, para que el cancionero quede limpio y centrado exclusivamente en acordes y letra.
7. Como lector, quiero que el documento esté maquetado a dos columnas por carilla, para aprovechar al máximo el espacio horizontal de la página.
8. Como lector, quiero que los acordes estén formateados en estilo negrita y color naranja (`#E65100`), para que resalten inmediatamente sobre la letra al tocar.
9. Como músico, quiero que las letras y acordes utilicen una tipografía monoespaciada (`Consolas`), para que los acordes ubicados sobre sílabas específicas no pierdan su alineación.
10. Como músico, quiero que cada canción tenga un encabezado claro con el título, artista y tono original (si está disponible), para identificar rápidamente la pieza.
11. Como usuario, quiero ejecutar la herramienta directamente con Python sin Docker ni dependencias de navegadores externos, para tener un flujo de trabajo ágil y sin fricción de configuración.
12. Como usuario, quiero que los encabezados de sección del tema (ej. `[Intro]`, `[Estribillo]`, `[Primeira Parte]`) se formateen limpiamente sin confundirse con acordes sueltos.
13. Como usuario, quiero que el script informe en consola el progreso de resolución de cada canción y advierta si alguna búsqueda no arrojó resultados, sin interrumpir el procesamiento del resto de las canciones.

## Implementation Decisions

- **Pipeline modular en Python**:
  - `resolver`: Consulta el endpoint Solr de Cifra Club (`https://solr.sscdn.co/cc/c7/?q={query}`) y extrae los metadatos canónicos del primer documento (`art`, `txt`, `dns`, `url`).
  - `scraper`: Descarga el HTML de `https://www.cifraclub.com.br/{dns}/{url}/` con User-Agent estándar y parsea el contenedor `<pre class="_crVx">`.
  - `parser_cleaner`: Separa líneas de acordes y texto preservando espaciados. Filtra líneas que coincidan con patrones de tablatura (`^[eEaAdDgGbB]\|`, `|---`, etc.).
  - `cache_repository`: Guarda y recupera canciones estructuradas en `.cache_cifras/<dns>_<url>.json`.
  - `docx_builder`: Construye `repertorio.docx` utilizando `python-docx`, configurando márgenes de 0.5 pulgadas, secciones de 2 columnas, saltos de página por canción y estilos tipográficos en Consolas con colores RGB para acordes.
  - `cli`: Lee `canciones.txt`, coordina el pipeline y reporta estado.

- **Estructura de datos en caché**:
  ```json
  {
    "query": "de musica ligera",
    "artist": "Soda Stereo",
    "title": "De Música Ligera",
    "url": "https://www.cifraclub.com.br/soda-stereo/de-musica-ligera/",
    "key": "Bm",
    "sections": [
      {
        "type": "block",
        "lines": [
          {
            "tokens": [
              {"text": "Bm", "is_chord": true},
              {"text": "        ", "is_chord": false},
              {"text": "G", "is_chord": true}
            ]
          },
          {
            "tokens": [
              {"text": "Ella durmió", "is_chord": false}
            ]
          }
        ]
      }
    ]
  }
  ```

- **Sin dependencias pesadas**: `requests`, `beautifulsoup4` y `python-docx` nativos.

## Testing Decisions

- **Seam único de testing (End-to-End Orchestrator)**:
  - Se prueba la función principal del orquestador desacoplando las llamadas de red mediante mocks de las respuestas HTTP de Solr y de la página web.
  - Se valida:
    1. Que ante una entrada con temas conocidos, se genere el archivo `.docx` con sus secciones a dos columnas y saltos de página.
    2. Que las líneas de tablatura queden completamente excluidas del documento final.
    3. Que los archivos JSON de caché se creen en el primer ciclo y se reutilicen en el segundo sin disparar llamadas de red adicionales.

## Out of Scope

- Transposición armónica de tonos (cambio de tonalidad en vivo).
- Generación de diagramas gráficos de acordes (dibujos de pisadas de guitarra).
- Exportación directa a PDF desde el script (se realiza directamente desde Word o herramientas externas).
- Interfaz gráfica (GUI o web).

## Further Notes

- El uso de tipografía Consolas en tamaño 9pt con espaciado de línea exacto (10-11pt) garantiza que entren estrofas completas en dos columnas sin partir líneas horizontales.
