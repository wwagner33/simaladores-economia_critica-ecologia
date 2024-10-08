from datetime import datetime
import json
import sys
import pygame as py
import pygame_gui
from pygame.locals import *
from ImageManager import ImageManager
from SimulatorThings.editing_tile import EditiongTile
from SimulatorThings.Gui.map_maker_gui import MapMakerGui
from Config import Config


class MapMaker:

    def __init__(
        self, map=None
    ) -> (
        None
    ):  # Depois colocar um botão que troca a edição de terreno pra edição de estrutura
        """Inicializa o Editor"""
        py.init()
        self.my_font = py.font.SysFont("Comic Sans MS", 30)
        self.screen = py.display.set_mode(
            (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT), DOUBLEBUF
        )
        self.images = ImageManager()
        py.display.set_caption("Criador de mapas interface")
        self.map: list[list] = map or [
            [0] * Config.WORLD_WIDTH for _ in range(Config.WORLD_HEIGHT)
        ]
        self.height_map = [[0] * Config.WORLD_WIDTH for _ in range(Config.WORLD_HEIGHT)]
        self.clock = py.time.Clock()
        self.blockSize = 80
        self.gridmap: list[list[EditiongTile]] = self.create_grid_tile(
            self.map, self.blockSize
        )

        self.gui = MapMakerGui(self.screen, self.images.tile_images)
        self.last_tile_clicked = None
        self.selected_tile = None
        self.hpopup_gui = None
        self.map_name = None

    def _load_map(self): ...


    def run(self):
        self.load_all_images()
        self.main_loop()


    def render_editor(self):
        self.screen.fill((0, 0, 0))
        self.drawGrid(self.map)


    def create_grid_tile(self, map=None, blockSize=80):
        blockSize = int(
            self.blockSize * Config.SCALE_MULTIPLIER
        )  # Set the size of the grid block

        if map:
            w = len(map[0])
            h = len(map)
        else:
            w = (Config.SCREEN_WIDTH - 200) // blockSize
            h = Config.SCREEN_HEIGHT // blockSize

        gridm = [[0] * w for _ in range(h)]

        for x in range(0, w):
            for y in range(0, h):
                gridm[x][y] = EditiongTile(x, y, blockSize, self.screen, map[x][y])

        return gridm

    def drawGrid(self, map=None):  # TODO Simplificar e refatorar
        blockSize = int(
            self.blockSize * Config.SCALE_MULTIPLIER
        )  # Set the size of the grid block
        if map:
            w = len(map[0])
            h = len(map)
        else:
            w = (Config.SCREEN_WIDTH - 200) // blockSize
            h = Config.SCREEN_HEIGHT // blockSize

        for x in range(0, w):
            for y in range(0, h):
                self.gridmap[x][y].render()

    def load_all_images(self):
        self.images.load_images()
        if not self.images.tile_images:
            print("Error: Tile images are not loaded.")
        else:
            print("Tile images loaded successfully.")

    def main_loop(self):
        while True:
            for event in py.event.get():
                if event.type == QUIT:
                    self.shutdown()

                elif (
                    event.type == py.MOUSEBUTTONUP
                ):  # Todo Fazer subir e diminuir a altura com o precionar do Shift
                    pos = py.mouse.get_pos()
                    if pos[0] < 200 and self.hpopup_gui:
                        self.hpopup_gui.painel.kill()

                    if self.map:  # TODO REfatorar
                        w = len(self.map[0])
                        h = len(self.map)
                    else:
                        w = (Config.SCREEN_WIDTH - 200) // self.blockSize
                        h = Config.SCREEN_HEIGHT // self.blockSize

                    for x in range(0, w):
                        for y in range(0, h):
                            if self.gridmap[x][y].has_been_clicked(pos):

                                if event.button == 3:  # Mouse Right Click

                                    if self.hpopup_gui:
                                        self.hpopup_gui.painel.kill()

                                    self.hpopup_gui = self.gui.show_height_popup(
                                        pos[0], pos[1]
                                    )
                                    self.last_tile_clicked = self.gridmap[x][y]

                                elif event.button == 1:  # Mouse Left Click:

                                    if self.selected_tile:
                                        if self.selected_tile == "R":
                                            self.gridmap[x][y].change_tile(None)
                                            self.map[x][y] = None
                                        else:
                                            self.gridmap[x][y].change_tile(
                                                int(self.selected_tile)
                                            )
                                            self.map[x][y] = int(self.selected_tile)

                # Eventos de Teclado
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.shutdown()

                # Gui parte por enquanto
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if "save_current_map" in event.ui_object_id:
                        self.__save_current_map()
                    if "mouse_changer" in event.ui_object_id:
                        self.gui.send_event(event)
                        self.selected_tile = event.ui_object_id[-1]
                    else:
                        self.selected_tile = None

                    if "Plus_height" in event.ui_object_id:
                        if self.last_tile_clicked.height < 7:  # ! Magic Number
                            self.last_tile_clicked.height += 1

                    if "Minus_height" in event.ui_object_id:
                        if self.last_tile_clicked.height > 0:
                            self.last_tile_clicked.height -= 1

                self.gui.manager.process_events(event)

            # self.update_game_state()
            self.render_editor()
            delta_time = self.clock.tick(Config.MAX_FPS) / 1000.0
            self.gui.render(delta_time)
            py.display.flip()


    def __update_height_map(self):
        for x in range(len(self.height_map)):
            for y in range(len(self.height_map)):
                self.height_map[x][y] = self.gridmap[x][y].height

    def __save_current_map(self):
        
        self.__update_height_map()
        self.map_name = self.gui.get_map_name_text()
        
        if not self.map_name:
            now = datetime.now()
            current_time = now.strftime("%H_%M_%S")
            m_name = f'map_saved{current_time}'
        
        else:
            m_name = self.map_name
        

        map = {
            "map_name": self.map_name,
            "map_relevo": self.height_map,
            "map_texture": self.map,
        }

        with open(
            f"./SimulatorThings/maps/{m_name}.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(map, f, ensure_ascii=False, indent=4)

    def shutdown(self):
        print("Shutting down...")
        py.quit()
        sys.exit()
