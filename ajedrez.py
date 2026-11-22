"""Ajedrez de consola para Termux/tmux con Stockfish."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import sys
from datetime import datetime

import chess
import chess.engine
import chess.pgn
from color_latam import color_hex


RIVALES = (
    ("Luna", "Aprende contigo", 0, 0.12),
    ("Mateo", "Juega con calma", 4, 0.18),
    ("Sofía", "Busca tácticas", 9, 0.28),
    ("Valentina", "Defiende con firmeza", 15, 0.42),
    ("Gran Maestro", "Un reto mayor", 20, 0.7),
)

PIEZAS = {
    "P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",
    "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚",
}
LETRAS = str.maketrans({"R": "K", "D": "Q", "T": "R", "A": "B", "C": "N"})
INVERSAS = str.maketrans({"K": "R", "Q": "D", "R": "T", "B": "A", "N": "C"})


def pintar(texto: str, hex_color: str, activo: bool = True, *, fuerte: bool = False) -> str:
    return color_hex(texto, hex_color, negrita=fuerte) if activo else texto


def san_es(san: str) -> str:
    """Traduce las letras de piezas de SAN inglesa a española."""
    if san.startswith("O-O"):
        return san
    return re.sub(r"(?<=\=)[KQRBN]|^[KQRBN]", lambda m: m.group().translate(INVERSAS), san)


def leer_jugada(tablero: chess.Board, texto: str) -> chess.Move:
    texto = texto.strip().replace("0-0", "O-O")
    if not texto:
        raise ValueError("Escribe una jugada.")
    # Una coordenada UCI es útil como alternativa en pantallas pequeñas.
    if re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?", texto.lower()):
        return tablero.parse_uci(texto.lower())
    # Se admiten letras españolas R/D/T/A/C y la notación internacional.
    if texto[0] in "RDTAC":
        texto = texto[0].translate(LETRAS) + texto[1:]
    texto = re.sub(r"(?<=\=)[RDTAC]", lambda m: m.group().translate(LETRAS), texto)
    try:
        return tablero.parse_san(texto)
    except ValueError as exc:
        raise ValueError("Jugada ilegal o ambigua. Prueba 'ayuda' o escribe origen y destino, por ejemplo e2e4.") from exc


def tablero_texto(tablero: chess.Board, blancas_abajo: bool, colores: bool, ascii_: bool) -> str:
    columnas = range(8) if blancas_abajo else range(7, -1, -1)
    filas = range(7, -1, -1) if blancas_abajo else range(8)
    etiqueta = "  " + " ".join("abcdefgh"[i] for i in columnas)
    lineas = [pintar(etiqueta, "#8ca4b8", colores)]
    ultima = tablero.peek() if tablero.move_stack else None
    for fila in filas:
        casillas = []
        for columna in columnas:
            sq = chess.square(columna, fila)
            pieza = tablero.piece_at(sq)
            glifo = pieza.symbol() if ascii_ and pieza else PIEZAS[pieza.symbol()] if pieza else "·"
            fondo = (fila + columna) % 2 == 0
            tono = "#f2d6a2" if fondo else "#8198a8"
            if ultima and sq in (ultima.from_square, ultima.to_square):
                tono = "#f6c65d"
            if pieza:
                tono = "#fffaf0" if pieza.color == chess.WHITE else "#173047"
            casillas.append(pintar(glifo, tono, colores, fuerte=bool(pieza)))
        lineas.append(pintar(str(fila + 1), "#8ca4b8", colores) + " " + " ".join(casillas) + " " + pintar(str(fila + 1), "#8ca4b8", colores))
    lineas.append(pintar(etiqueta, "#8ca4b8", colores))
    return "\n".join(lineas)


def historial(tablero: chess.Board) -> str:
    copia = chess.Board()
    jugadas = []
    for indice, movimiento in enumerate(tablero.move_stack):
        san = san_es(copia.san(movimiento))
        if indice % 2 == 0:
            jugadas.append(f"{indice // 2 + 1}. {san}")
        else:
            jugadas[-1] += f" {san}"
        copia.push(movimiento)
    return "   ".join(jugadas[-4:]) if jugadas else "Aún no hay jugadas"


def guardar_pgn(tablero: chess.Board, rival: str, humano_blancas: bool, carpeta: Path) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    partida = chess.pgn.Game.from_board(tablero)
    partida.headers["Event"] = "Ajedrez Tmux"
    partida.headers["White"] = "Tú" if humano_blancas else rival
    partida.headers["Black"] = rival if humano_blancas else "Tú"
    partida.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
    partida.headers["Result"] = tablero.result(claim_draw=True)
    ruta = carpeta / f"partida-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pgn"
    with ruta.open("w", encoding="utf-8") as archivo:
        print(partida, file=archivo)
    return ruta


def estado(tablero: chess.Board) -> str | None:
    if tablero.is_checkmate():
        return "Jaque mate. ¡Ganaron las blancas!" if tablero.turn == chess.BLACK else "Jaque mate. ¡Ganaron las negras!"
    if tablero.is_stalemate():
        return "Tablas por ahogado."
    if tablero.is_insufficient_material():
        return "Tablas por material insuficiente."
    if tablero.can_claim_threefold_repetition() or tablero.is_fivefold_repetition():
        return "Tablas por repetición."
    if tablero.can_claim_fifty_moves() or tablero.is_seventyfive_moves():
        return "Tablas por regla de los 50 movimientos."
    return None


def buscar_stockfish(ruta: str | None) -> str:
    candidato = ruta or os.environ.get("STOCKFISH_PATH") or shutil.which("stockfish")
    if not candidato:
        raise FileNotFoundError("No encontré Stockfish. En Termux: pkg install stockfish. También puedes usar --stockfish RUTA.")
    if not Path(candidato).is_file():
        raise FileNotFoundError(f"No existe Stockfish en: {candidato}")
    return candidato


def elegir_rival() -> int:
    print("\nElige tu rival:\n")
    for indice, (nombre, detalle, _, _) in enumerate(RIVALES, 1):
        print(f"  {indice}. {nombre:<14} {detalle}")
    while True:
        try:
            valor = input("\nRival [1-5, Enter=1]: ").strip() or "1"
        except EOFError:
            raise SystemExit(0)
        if valor in "12345" and len(valor) == 1:
            return int(valor) - 1
        print("Elige un número del 1 al 5.")


def mostrar(tablero: chess.Board, rival: str, humano_blancas: bool, colores: bool, ascii_: bool, mensaje: str = "") -> None:
    if sys.stdout.isatty():
        print("\033[2J\033[H", end="")
    print(pintar("╭──────────────────────────────╮", "#66d9d0", colores))
    print(pintar("│      AJEDREZ  ·  TMUX        │", "#66d9d0", colores, fuerte=True))
    print(pintar("╰──────────────────────────────╯", "#66d9d0", colores))
    print(f"  Tú {'♙ blancas' if humano_blancas else '♟ negras'}  ·  {rival}\n")
    print(tablero_texto(tablero, humano_blancas, colores, ascii_))
    print("\n" + pintar(historial(tablero), "#b3c6d1", colores))
    if tablero.is_check():
        print(pintar("  ¡Jaque!", "#ff917c", colores, fuerte=True))
    if mensaje:
        print("\n" + pintar(mensaje, "#f4c774", colores))
    print("\n  e4 · Te2 · Cf3 · O-O  |  ayuda · deshacer · guardar · salir")


def jugar(args: argparse.Namespace) -> int:
    rival_id = args.rival - 1 if args.rival else elegir_rival()
    nombre, _, habilidad, tiempo = RIVALES[rival_id]
    humano_blancas = args.color != "negras"
    colores = not args.sin_color and sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    try:
        motor = chess.engine.SimpleEngine.popen_uci(buscar_stockfish(args.stockfish))
    except (FileNotFoundError, OSError, chess.engine.EngineError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    tablero = chess.Board()
    mensaje = f"¡Comienza la partida contra {nombre}!"
    try:
        motor.configure({"Skill Level": habilidad})
        while True:
            fin = estado(tablero)
            if fin:
                mostrar(tablero, nombre, humano_blancas, colores, args.ascii, fin)
                print(f"\nPartida guardada en {guardar_pgn(tablero, nombre, humano_blancas, Path('partidas'))}")
                return 0
            if tablero.turn != humano_blancas:
                mostrar(tablero, nombre, humano_blancas, colores, args.ascii, f"{nombre} está pensando…")
                jugada = motor.play(tablero, chess.engine.Limit(time=tiempo)).move
                san = san_es(tablero.san(jugada))
                tablero.push(jugada)
                mensaje = f"{nombre} jugó {san}."
                continue
            mostrar(tablero, nombre, humano_blancas, colores, args.ascii, mensaje)
            try:
                orden = input("\nTu jugada › ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nHasta pronto.")
                return 0
            if orden.lower() in ("salir", "exit", "q"):
                return 0
            if orden.lower() in ("ayuda", "?"):
                mensaje = "Escribe e4, Te2, Cf3, Dd1, O-O o e2e4. También: guardar, deshacer, salir."
                continue
            if orden.lower() == "guardar":
                mensaje = f"Partida guardada en {guardar_pgn(tablero, nombre, humano_blancas, Path('partidas'))}"
                continue
            if orden.lower() == "deshacer":
                if tablero.move_stack:
                    tablero.pop()
                    if tablero.move_stack and tablero.turn != humano_blancas:
                        tablero.pop()
                    mensaje = "Se deshizo el último turno."
                else:
                    mensaje = "Aún no hay jugadas para deshacer."
                continue
            try:
                movimiento = leer_jugada(tablero, orden)
                mensaje = f"Jugaste {san_es(tablero.san(movimiento))}."
                tablero.push(movimiento)
            except ValueError as exc:
                mensaje = str(exc)
    except (chess.engine.EngineError, chess.engine.EngineTerminatedError, OSError) as exc:
        print(f"\nStockfish dejó de responder: {exc}", file=sys.stderr)
        return 1
    finally:
        motor.quit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Ajedrez bonito para Termux y tmux")
    parser.add_argument("--rival", type=int, choices=range(1, 6), metavar="1-5", help="Selecciona uno de los cinco rivales")
    parser.add_argument("--color", choices=("blancas", "negras"), default="blancas", help="Color de tus piezas")
    parser.add_argument("--stockfish", help="Ruta del ejecutable de Stockfish")
    parser.add_argument("--sin-color", action="store_true", help="Desactiva los colores ANSI")
    parser.add_argument("--ascii", action="store_true", help="Usa letras en vez de piezas Unicode")
    return jugar(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
