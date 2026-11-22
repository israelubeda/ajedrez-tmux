import chess

from ajedrez import RIVALES, guardar_pgn, leer_jugada, san_es, tablero_texto


def test_notacion_espanola_y_movimientos_legales():
    tablero = chess.Board()
    tablero.push(leer_jugada(tablero, "e4"))
    tablero.push(leer_jugada(tablero, "e5"))
    jugada = leer_jugada(tablero, "Cf3")
    assert tablero.san(jugada) == "Nf3"
    assert san_es("Nf3") == "Cf3"
    tablero.push(jugada)
    assert leer_jugada(tablero, "b8c6") == chess.Move.from_uci("b8c6")


def test_tablero_y_pgn(tmp_path):
    tablero = chess.Board()
    texto = tablero_texto(tablero, True, False, True)
    lineas = texto.splitlines()
    assert len(lineas) == 10
    assert "A  B  C  D  E  F  G  H" in lineas[0]
    assert lineas[1].startswith(" 8  ")
    assert lineas[8].startswith(" 1  ")
    assert "H  G  F  E  D  C  B  A" in tablero_texto(tablero, False, False, True)
    tablero.push_san("e4")
    pintado = tablero_texto(tablero, True, True, False)
    assert pintado.count("\x1b[48;2;") == 64
    assert "\x1b[48;2;212;154;72m" in pintado  # origen
    assert "\x1b[48;2;229;200;91m" in pintado  # destino
    ruta = guardar_pgn(tablero, "Luna", True, tmp_path)
    assert '[White "Tú"]' in ruta.read_text(encoding="utf-8")


def test_cinco_rivales():
    assert len(RIVALES) >= 5
    assert len({r[2] for r in RIVALES}) == len(RIVALES)
