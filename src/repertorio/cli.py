import argparse
import sys
from pathlib import Path

from repertorio.generator import generate_repertoire


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generador de cancionero / repertorio en Word (.docx) desde Cifra Club."
    )
    parser.add_argument(
        "-i",
        "--input",
        default="canciones.txt",
        help="Ruta al archivo .txt con la lista de canciones (default: canciones.txt)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="repertorio.docx",
        help="Ruta al archivo .docx de salida (default: repertorio.docx)",
    )
    parser.add_argument(
        "-c",
        "--cache-dir",
        default=".cache_cifras",
        help="Directorio para la cache local de canciones (default: .cache_cifras)",
    )
    parser.add_argument(
        "--columns",
        choices=[1, 2],
        type=int,
        default=2,
        help="Numero de columnas del cancionero (1 o 2, default: 2)",
    )
    parser.add_argument(
        "--chord-color",
        default="#E65100",
        help="Color hexadecimal de los acordes (default: #E65100)",
    )

    args = parser.parse_args()

    input_file = Path(args.input)
    if not input_file.exists():
        print(f"[!] No se encontro el archivo de entrada '{input_file}'.")
        print(f"[*] Creando un archivo '{input_file}' de ejemplo...")
        input_file.write_text(
            "# Agrega una cancion por linea (nombre, o 'Artista - Cancion')\n"
            "de musica ligera\n"
            "the scientist coldplay\n",
            encoding="utf-8",
        )
        print(f"[+] Archivo '{input_file}' creado con ejemplos. Ejecuta el script de nuevo o editalo.")
        sys.exit(0)

    stats = generate_repertoire(
        input_file,
        args.output,
        cache_dir=args.cache_dir,
        columns=args.columns,
        chord_color=args.chord_color,
    )
    print(f"\nResumen: {stats['total']} total | {stats['downloaded']} descargadas | {stats['cached']} en cache | {stats['failed']} fallidas.")


if __name__ == "__main__":
    main()
