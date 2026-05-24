import os
import sys
import time
from ui import Screen, TitleScene

TICK = 1 / 30  # ~33ms per frame


def main():
    restart = False
    try:
        with Screen() as screen:
            scene = TitleScene(screen)
            scene.enter()

            last = time.monotonic()
            while scene is not None:
                now = time.monotonic()
                dt = now - last
                last = now

                next_scene = scene.update(dt)
                if next_scene is not None and next_scene is not scene:
                    next_scene.enter()
                    scene = next_scene

                scene.draw()

                key = screen.read_key(timeout=TICK)
                if not key: continue

                if key.is_sequence and key.name == 'KEY_F5':
                    restart = True
                    break

                next_scene = scene.handle_key(key)
                if next_scene is not scene:
                    if next_scene is None: break
                    next_scene.enter()
                scene = next_scene

    except KeyboardInterrupt: pass

    if restart: os.execv(sys.executable, [sys.executable] + sys.argv)


if __name__ == '__main__': main()
