# Ajedrez Tmux ♟

Un ajedrez de consola en Python para Android con Termux y tmux. Juega contra cinco rivales manejados por Stockfish. Escribe las jugadas directamente, por ejemplo `e4`, `Cf3`, `Te2`, `Dxd5`, `O-O` o `e2e4`.

## Instalar en Android

En **Termux**:

```sh
pkg update
pkg install python stockfish tmux git
git clone https://github.com/israelubeda/ajedrez-tmux.git
cd ajedrez-tmux
python -m pip install -r requirements.txt
tmux new -s ajedrez
python ajedrez.py
```

Si Termux no encuentra `stockfish`, consulta `command -v stockfish` y pásale la ruta mediante `--stockfish RUTA` o `STOCKFISH_PATH`. Para salir de tmux sin cerrar el juego, pulsa `Ctrl+B`, luego `D`; vuelve con `tmux attach -t ajedrez`.

## Jugar

Selecciona un rival del 1 al 5. También puedes iniciar directamente:

```sh
python ajedrez.py --rival 3 --color negras
```

| Rival | Estilo | Ajuste Stockfish |
| --- | --- | ---: |
| Luna | Aprende contigo | 0 |
| Mateo | Juega con calma | 4 |
| Sofía | Busca tácticas | 9 |
| Valentina | Defiende con firmeza | 15 |
| Gran Maestro | Un reto mayor | 20 |

La fuerza cambia con `Skill Level` y el tiempo de cálculo. Los nombres describen el nivel de juego, no representan personas distintas ni un Elo certificado.

Usa `ayuda`, `deshacer`, `guardar` y `salir` en el mismo campo de entrada. Las partidas terminadas se guardan automáticamente en `partidas/` como PGN; `guardar` permite crear uno durante la partida. La carpeta está excluida de Git para que tus partidas sean privadas.

Los colores se generan con [color-latam](https://pypi.org/project/color-latam/). Si tu terminal no muestra bien las piezas, ejecuta `python ajedrez.py --ascii`; para desactivar colores usa `--sin-color` o `NO_COLOR=1`.

El tablero usa casillas coloreadas, coordenadas grandes y resaltado separado para
origen y destino, adaptados del diseño de
[lector-pgn-terminal](https://github.com/israelubeda/lector-pgn-terminal).

## Requisitos

- Python 3.10 o posterior
- [Stockfish](https://stockfishchess.org/download/) instalado como programa independiente
- Dependencias Python de `requirements.txt`

Stockfish es software libre bajo GPLv3. Este repositorio no incluye el binario de Stockfish.

## Licencia

El código propio de este repositorio se distribuye bajo [MIT](LICENSE). El código
interno de registro es `IU-OSS-0001`; consulta [LICENSE_ID.txt](LICENSE_ID.txt).
Las dependencias y Stockfish conservan sus licencias respectivas.
