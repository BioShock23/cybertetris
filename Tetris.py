import sys
from random import randint
import pygame

# Инициализация PyGame, загрузка файлов и определение констант
pygame.init()
pygame.display.set_caption("Cybertetris 2021")
HEIGHT, WIDTH = 600, 575
screen = pygame.display.set_mode((WIDTH, HEIGHT))
GRIDSIZE = 25
COLUMNS, ROWS = 14, 24
LEVELS_TICKS = [90, 40, 20, 14, 10, 8, 6, 3, 2]
SCORE = 0
LEFT, RIGHT, MIDDLE, TOP, FLOOR = 0, 14, 7, 1, 25
cube_block = pygame.image.load('data/Previews/cube-block.png').convert_alpha()
t_block = pygame.image.load('data/Previews/t-block.png').convert_alpha()
i_block = pygame.image.load('data/Previews/i-block.png').convert_alpha()
L_block = pygame.image.load('data/Previews/L-block.png').convert_alpha()
r_s_block = pygame.image.load('data/Previews/r-s-block.png').convert_alpha()
j_block = pygame.image.load('data/Previews/j-block.png').convert_alpha()
s_block = pygame.image.load('data/Previews/s-block.png').convert_alpha()
block_img_lst = [r_s_block, s_block, L_block, j_block, i_block, t_block, cube_block]
favicon = pygame.image.load('data/images/favicon.png').convert_alpha()
pygame.display.set_icon(favicon)
pygame.font.init()
my_font = pygame.font.SysFont('Arial Black', 21)
pygame.mixer.set_num_channels(6)
interface_img = pygame.image.load('data/images/Tetris.jpg')
grid_img = pygame.image.load('data/images/gridbg.jpg')
pause_screen = pygame.image.load('data/images/Pause.jpg')
intro_screen = pygame.image.load('data/images/Intro.jpg')
outro_screen = pygame.image.load('data/images/Outro.jpg')
tetris_remove = pygame.mixer.Sound('data/Sounds/tetris-remove.ogg')
block_rotate = pygame.mixer.Sound('data/Sounds/block-rotate.ogg')
line_remove = pygame.mixer.Sound('data/Sounds/line-remove.ogg')
slow_hit = pygame.mixer.Sound('data/Sounds/slow-hit.ogg')
force_hit = pygame.mixer.Sound('data/Sounds/force-hit.ogg')
bg_music = pygame.mixer.Sound('data/Music/Cyberpunk.ogg')
colors_list = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 127, 0), (0, 183, 235),
               (255, 0, 255), (255, 255, 0), (255, 255, 255)]
all_sprites = pygame.sprite.Group()


# Классы
class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y):
        super().__init__(all_sprites)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)
        self.f = False

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(pygame.transform.scale(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)), (400, 420)))

    def update(self):
        if self.cur_frame > 36:
            self.f = True
        if not self.f:
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]


# Базовый класс квадратика на клеточном поле
class Block:
    def __init__(self, col=1, row=1, clr=1):
        self.col, self.row, self.clr = col, row, clr

    def __eq__(self, other):
        if self.col == other.col and self.row == other.row:
            return True
        return False

    def move_down(self):
        self.row += 1

    def draw(self, surface, gridsize):
        x, y = self.col * gridsize, self.row * gridsize
        color = colors_list[self.clr]
        pygame.draw.rect(surface, (0, 0, 0), (x, y, gridsize, gridsize), 3)
        pygame.draw.rect(surface, color, (x, y, gridsize - 3, gridsize - 3), 0)


# Группа блоков
class Figure:
    def __init__(self, col=1, row=1, blocks_num=1):
        self.col, self.row, self.clr = col, row, 0
        self.blocks = blocks_num * [Block()]
        self._colOffsets = blocks_num * [0]
        self._rowOffsets = blocks_num * [0]

    def draw(self, surface, gridsize):
        for block in self.blocks:
            block.draw(surface, gridsize)

    def collides(self, other):
        for block in self.blocks:
            for obstacle in other.blocks:
                if block == obstacle:
                    return True
        return False

    def append(self, other):
        for block in other.blocks:
            self.blocks.append(block)

    def _update(self):
        for i in range(len(self.blocks)):
            block_col = self.col + self._colOffsets[i]
            block_row = self.row + self._rowOffsets[i]
            block_clr = self.clr
            self.blocks[i] = Block(block_col, block_row, block_clr)


# Препятствия для падающих блоков, т.е уже упавшие блоки
class Obstacles(Figure):
    def __init__(self, col=0, row=0, blocks_num=0):
        Figure.__init__(self, col, row, blocks_num)

    def find_completed_rows(self, top, bottom, columns):
        completed_rows = []
        rows = []
        for block in self.blocks:
            rows.append(block.row)
        for row in range(top, bottom):
            if rows.count(row) == columns:
                completed_rows.append(row)
        return completed_rows

    def del_completed_rows(self, completed_rows):
        for row in completed_rows:
            for i in reversed(range(len(self.blocks))):
                if self.blocks[i].row == row:
                    self.blocks.pop(i)
                elif self.blocks[i].row < row:
                    self.blocks[i].move_down()


# Фигура со свойствами и действиями
class Tetramino(Figure):
    def __init__(self, col=1, row=1, clr=1, rot=1):
        Figure.__init__(self, col, row, 4)
        self.clr = clr
        self._rot = rot
        self._colOffsets = [-1, 0, 0, 1]
        self._rowOffsets = [-1, -1, 0, 0]
        self._rotate()

    def _rotate(self):
        global _rowOffsets, _colOffsets
        if self.clr == 1:
            _colOffsets = [[-1, -1, 0, 0], [-1, 0, 0, 1], [1, 1, 0, 0], [1, 0, 0, -1]]
            _rowOffsets = [[1, 0, 0, -1], [-1, -1, 0, 0], [-1, 0, 0, 1], [1, 1, 0, 0]]
        elif self.clr == 2:
            _colOffsets = [[-1, -1, 0, 0], [1, 0, 0, -1], [1, 1, 0, 0], [-1, 0, 0, 1]]
            _rowOffsets = [[-1, 0, 0, 1], [-1, -1, 0, 0], [1, 0, 0, -1], [1, 1, 0, 0]]
        elif self.clr == 3:
            _colOffsets = [[-1, 0, 0, 0], [-1, -1, 0, 1], [1, 0, 0, 0], [1, 1, 0, -1]]
            _rowOffsets = [[1, 1, 0, -1], [-1, 0, 0, 0], [-1, -1, 0, 1], [1, 0, 0, 0]]
        elif self.clr == 4:
            _colOffsets = [[-1, 0, 0, 0], [1, 1, 0, -1], [1, 0, 0, 0], [-1, -1, 0, 1]]
            _rowOffsets = [[-1, -1, 0, 1], [-1, 0, 0, 0], [1, 1, 0, -1], [1, 0, 0, 0]]
        elif self.clr == 5:
            _colOffsets = [[0, 0, 0, 0], [2, 1, 0, -1], [0, 0, 0, 0], [-2, -1, 0, 1]]
            _rowOffsets = [[-2, -1, 0, 1], [0, 0, 0, 0], [2, 1, 0, -1], [0, 0, 0, 0]]
        elif self.clr == 6:
            _colOffsets = [[0, -1, 0, 0], [-1, 0, 0, 1], [0, 1, 0, 0], [1, 0, 0, -1]]
            _rowOffsets = [[1, 0, 0, -1], [0, -1, 0, 0], [-1, 0, 0, 1], [0, 1, 0, 0]]
        elif self.clr == 7:
            _colOffsets = [[-1, -1, 0, 0], [-1, -1, 0, 0], [-1, -1, 0, 0], [-1, -1, 0, 0]]
            _rowOffsets = [[0, -1, 0, -1], [0, -1, 0, -1], [0, -1, 0, -1], [0, -1, 0, -1]]
        self._colOffsets = _colOffsets[self._rot]
        self._rowOffsets = _rowOffsets[self._rot]
        self._update()

    def move_left(self):
        self.col = self.col - 1
        self._update()

    def move_right(self):
        self.col = self.col + 1
        self._update()

    def move_up(self):
        self.row = self.row - 1
        self._update()

    def move_down(self):
        self.row = self.row + 1
        self._update()

    def rotate_left(self):
        self._rot = (self._rot - 1) % 4

    def rotate_right(self):
        self._rot = (self._rot + 1) % 4


# Препятствие в виде стены
class Wall(Figure):
    def __init__(self, col=1, row=1, blocks_num=1):
        Figure.__init__(self, col, row, blocks_num)
        for i in range(blocks_num):
            self._rowOffsets[i] = i
        self._update()


# Препятствие в виде пола
class Floor(Figure):
    def __init__(self, col=1, row=1, blocks_num=1):
        Figure.__init__(self, col, row, blocks_num)
        for i in range(blocks_num):
            self._colOffsets[i] = i
        self._update()


# Функции
# Отрисовка клеточного поля
def draw_grid():
    for i in range(24):
        pygame.draw.line(screen, (0, 0, 0), (0, i * GRIDSIZE), (GRIDSIZE * 24, i * GRIDSIZE), 1)
    for i in range(15):
        pygame.draw.line(screen, (0, 0, 0), (i * GRIDSIZE, 0), (i * GRIDSIZE, HEIGHT), 1)


# Перерисовка всего экрана
def redraw_screen():
    score_text = my_font.render(str(SCORE), True, (0, 0, 0))
    level_text = my_font.render(str(level + 1), True, (0, 0, 0))
    high_score_text = my_font.render(str(get_high_score()), True, (0, 0, 0))
    screen.blit(grid_img, (0, 0))
    draw_grid()
    screen.blit(interface_img, (GRIDSIZE * 14, 0))
    shape.draw(screen, GRIDSIZE)
    obstacles.draw(screen, GRIDSIZE)
    screen.blit(score_text, ((GRIDSIZE * 14) + 90, 460))
    screen.blit(high_score_text, ((GRIDSIZE * 14) + 85, 538))
    screen.blit(level_text, ((GRIDSIZE * 14) + 100, 380))
    screen.blit(block_img_lst[next_shape_num - 1], ((GRIDSIZE * 14) + 72, 240))
    save_game(SCORE)
    pygame.display.flip()


# Принудительное падение фигуры
def drop(shape):
    crashed = False
    while not crashed:
        shape.move_down()
        if shape.collides(floor) or shape.collides(obstacles):
            shape.move_up()
            crashed = True
    pygame.mixer.Channel(2).play(force_hit)


# Сохранение лучшего рез-та в файл
def save_game(score):
    f = open('data/saves.txt', mode='r', encoding='utf-8')
    high_score = get_high_score()
    if score > high_score:
        f = open('data/saves.txt', mode='w', encoding='utf-8')
        f.write(str(score))
    f.close()


# Получение лучшего рез-за из файла
def get_high_score():
    f = open('data/saves.txt', mode='r', encoding='utf-8')
    high_score = int(f.readline().rstrip())
    return high_score


# Определение нужных для игрового цикла переменных
clock = pygame.time.Clock()
ticks_counter = 0
shape_num = randint(1, 7)
next_shape_num = randint(1, 7)
shape = Tetramino(MIDDLE, TOP, shape_num)
floor = Floor(LEFT, ROWS, COLUMNS)
left_wall = Wall(LEFT - 1, 0, ROWS)
right_wall = Wall(RIGHT, 0, ROWS)
obstacles = Obstacles(LEFT, FLOOR)
playing = False
has_played = False
level = 0
pygame.mixer.Channel(0).play(bg_music, -1)
paused = False
keanu = AnimatedSprite(pygame.image.load('data/images/keanu.png'), 38, 1, 80, 0)

# Стартовый экран
while not playing and not has_played:
    screen.blit(intro_screen, (0, 0))
    all_sprites.draw(screen)
    clock.tick(20)
    keanu.update()
    pygame.display.flip()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                playing = True
                has_played = True

# Главный экран игрового процесса
while playing:
    if not paused:
        pygame.mixer.unpause()
        if ticks_counter % LEVELS_TICKS[level] == 0:
            shape.move_down()
            if shape.collides(floor) or shape.collides(obstacles):
                shape.move_up()
                obstacles.append(shape)
                pygame.mixer.Channel(5).play(slow_hit)
                full_rows = obstacles.find_completed_rows(TOP, FLOOR, COLUMNS)
                if 0 < len(full_rows) < 4:
                    SCORE += 100 * len(full_rows)
                    pygame.mixer.Channel(3).play(line_remove)
                elif len(full_rows) >= 4:
                    SCORE += 1000 + (100 * (len(full_rows) - 4))
                    pygame.mixer.Channel(4).play(tetris_remove)
                obstacles.del_completed_rows(full_rows)
                shape_num = next_shape_num
                next_shape_num = randint(1, 7)
                if shape.row > 1:
                    shape = Tetramino(MIDDLE, TOP, shape_num)
                else:
                    playing = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            playing = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                paused = not paused
            if not paused:
                if event.key == pygame.K_UP or event.key == ord('w'):
                    shape.rotate_right()
                    shape._rotate()
                    if shape.collides(left_wall) or shape.collides(right_wall) or shape.collides(
                            floor) or shape.collides(
                        obstacles):
                        shape.rotate_left()
                        shape._rotate()
                    else:
                        pygame.mixer.Channel(1).play(block_rotate)

                if event.key == pygame.K_LEFT or event.key == ord('a'):
                    shape.move_left()
                    if shape.collides(left_wall):
                        shape.move_right()
                    elif shape.collides(obstacles):
                        shape.move_right()

                if event.key == pygame.K_RIGHT or event.key == ord('d'):
                    shape.move_right()
                    if shape.collides(right_wall):
                        shape.move_left()
                    elif shape.collides(obstacles):
                        shape.move_left()

                if event.key == pygame.K_SPACE or event.key == ord('s') or event.key == pygame.K_DOWN:
                    drop(shape)
                    obstacles.append(shape)
                    shape_num = next_shape_num
                    next_shape_num = randint(1, 7)
                    shape = Tetramino(MIDDLE, TOP, shape_num)
                    full_rows = obstacles.find_completed_rows(TOP, FLOOR, COLUMNS)
                    if 0 < len(full_rows) < 4:
                        SCORE += 100 * len(full_rows)
                        pygame.mixer.Channel(3).play(line_remove)
                    elif len(full_rows) >= 4:
                        SCORE += 1000 + (100 * (len(full_rows) - 4))
                        pygame.mixer.Channel(4).play(tetris_remove)
                        pygame.mixer.Channel(4).play(tetris_remove)
                    obstacles.del_completed_rows(full_rows)
    if not paused:
        if 1000 >= SCORE >= 500:
            level = 1
        elif 1500 >= SCORE > 1000:
            level = 2
        elif 2000 >= SCORE > 1500:
            level = 3
        elif 2250 >= SCORE > 2000:
            level = 4
        elif 2500 >= SCORE > 2250:
            level = 5
        elif 2750 >= SCORE > 2500:
            level = 6
        elif 3000 >= SCORE > 2750:
            level = 7
        elif 3250 >= SCORE > 3000:
            level = 8
        elif SCORE >= 3250:
            level = 9
        ticks_counter += 1
        redraw_screen()
    if paused:
        screen.blit(pause_screen, (0, 0))
        pygame.mixer.pause()
        pygame.display.flip()

# Конечный экран
while not playing and has_played:
    screen.blit(outro_screen, (0, 0))
    end_text = my_font.render(str(SCORE), True, (253, 248, 0))
    screen.blit(end_text, (350, 275))
    pygame.display.flip()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                pygame.quit()
                sys.exit(0)

