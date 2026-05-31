import pygame
import sys
import math

# 初始化
pygame.init()

# ====================== 配置参数 ======================
BOARD_SIZE = 15          # 棋盘大小 15x15
CELL_SIZE = 40           # 格子边长（像素）
MARGIN = 45              # 边缘留白（加大以显示按钮）
WINDOW_WIDTH = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1)
WINDOW_HEIGHT = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1) + 60  # 底部预留空间给按钮

# 颜色（精心搭配，更美观）
BOARD_COLOR = (235, 195, 110)      # 木质底色
LINE_COLOR = (50, 30, 20)          # 深褐色线条
BLACK_STONE = (40, 40, 40)         # 黑棋，带一点光泽
WHITE_STONE = (250, 250, 245)      # 白棋
HIGHLIGHT_COLOR = (200, 220, 180)  # 高亮颜色（绿色）
BUTTON_COLOR = (80, 120, 80)       # 按钮底色
BUTTON_HOVER_COLOR = (100, 150, 100)
TEXT_COLOR = (255, 255, 220)

# 棋子标识
EMPTY = 0
BLACK = 1   # 玩家
WHITE = 2   # AI

# 游戏状态
board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
current_turn = BLACK
game_over = False
winner = None

# 窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("五子棋 · 智能对战")

# ---------- 关键修改：避免 SysFont 崩溃，直接使用默认字体 ----------
font_large = pygame.font.Font(None, 28)
font_small = pygame.font.Font(None, 20)

# ====================== 辅助绘图函数 ======================
def draw_board():
    """绘制木质棋盘、星位和装饰边框"""
    screen.fill((80, 60, 40))   # 深色背景
    # 棋盘区域白色内阴影效果
    pygame.draw.rect(screen, (120, 85, 55), (MARGIN-5, MARGIN-5, 
                     CELL_SIZE*(BOARD_SIZE-1)+10, CELL_SIZE*(BOARD_SIZE-1)+10), border_radius=5)
    pygame.draw.rect(screen, BOARD_COLOR, (MARGIN-2, MARGIN-2, 
                     CELL_SIZE*(BOARD_SIZE-1)+4, CELL_SIZE*(BOARD_SIZE-1)+4), border_radius=3)
    # 画网格线
    for i in range(BOARD_SIZE):
        start = (MARGIN, MARGIN + i * CELL_SIZE)
        end = (WINDOW_WIDTH - MARGIN, MARGIN + i * CELL_SIZE)
        pygame.draw.line(screen, LINE_COLOR, start, end, 2)
        start = (MARGIN + i * CELL_SIZE, MARGIN)
        end = (MARGIN + i * CELL_SIZE, WINDOW_HEIGHT - MARGIN - 60)
        pygame.draw.line(screen, LINE_COLOR, start, end, 2)

    # 绘制星位（天元/小目）
    if BOARD_SIZE == 15:
        stars = [(3, 3), (11, 3), (7, 7), (3, 11), (11, 11)]
    elif BOARD_SIZE == 9:
        stars = [(2, 2), (6, 2), (4, 4), (2, 6), (6, 6)]
    else:
        stars = []
    for r, c in stars:
        x = MARGIN + c * CELL_SIZE
        y = MARGIN + r * CELL_SIZE
        pygame.draw.circle(screen, (200, 150, 80), (x, y), 6)   # 金色底
        pygame.draw.circle(screen, (50, 30, 15), (x, y), 4)     # 深色芯

def draw_pieces():
    """绘制棋子，带高光效果"""
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            stone = board[row][col]
            if stone == EMPTY:
                continue
            x = MARGIN + col * CELL_SIZE
            y = MARGIN + row * CELL_SIZE
            # 阴影
            pygame.draw.circle(screen, (30, 30, 30), (x+2, y+2), CELL_SIZE//2 - 2)
            # 主体
            color = BLACK_STONE if stone == BLACK else WHITE_STONE
            pygame.draw.circle(screen, color, (x, y), CELL_SIZE//2 - 2)
            # 高光
            if stone == BLACK:
                pygame.draw.circle(screen, (100, 100, 100), (x-3, y-3), 3)
            else:
                pygame.draw.circle(screen, (255, 255, 255), (x-3, y-3), 3)

def draw_button(text, x, y, w, h, hover=False):
    """绘制圆角按钮，返回矩形区域"""
    rect = pygame.Rect(x, y, w, h)
    color = BUTTON_HOVER_COLOR if hover else BUTTON_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=8)
    pygame.draw.rect(screen, (255, 255, 200), rect, 2, border_radius=8)
    text_surf = font_small.render(text, True, TEXT_COLOR)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)
    return rect

def draw_info():
    """显示回合/胜利信息，并绘制新游戏和AI先手按钮"""
    if game_over:
        if winner == BLACK:
            msg = "You win! Press R or click [New Game]"
        elif winner == WHITE:
            msg = "AI wins! Press R or [New Game]"
        else:
            msg = "Game Over"
    else:
        if current_turn == BLACK:
            msg = "Your turn"
        else:
            msg = "AI is thinking ..."
    text = font_large.render(msg, True, (255, 245, 200))
    screen.blit(text, (MARGIN, WINDOW_HEIGHT - 45))

    # 绘制按钮（坐标动态，返回矩形供事件检测）
    btn_new = draw_button("New Game", WINDOW_WIDTH - 180, WINDOW_HEIGHT - 48, 80, 35,
                          hover=btn_new_rect.collidepoint(pygame.mouse.get_pos()) if 'btn_new_rect' in globals() else False)
    btn_ai = draw_button("AI First", WINDOW_WIDTH - 90, WINDOW_HEIGHT - 48, 80, 35,
                         hover=btn_ai_rect.collidepoint(pygame.mouse.get_pos()) if 'btn_ai_rect' in globals() else False)
    return btn_new, btn_ai

# ====================== AI 智能评分核心 ======================
DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]

def evaluate_direction(board, row, col, dr, dc, player):
    """评价在某个方向上的得分（模拟放置后计算连续长度和两端开口）"""
    if board[row][col] != EMPTY:
        return 0
    # 临时放置棋子
    board[row][col] = player
    count = 1
    left_open = False
    right_open = False

    # 正方向
    for step in range(1, 6):
        nr, nc = row + dr * step, col + dc * step
        if nr < 0 or nr >= BOARD_SIZE or nc < 0 or nc >= BOARD_SIZE:
            break
        if board[nr][nc] == player:
            count += 1
        else:
            if board[nr][nc] == EMPTY:
                right_open = True
            break
    # 反方向
    for step in range(1, 6):
        nr, nc = row - dr * step, col - dc * step
        if nr < 0 or nr >= BOARD_SIZE or nc < 0 or nc >= BOARD_SIZE:
            break
        if board[nr][nc] == player:
            count += 1
        else:
            if board[nr][nc] == EMPTY:
                left_open = True
            break
    # 恢复棋盘
    board[row][col] = EMPTY

    # 得分规则（经验值）
    if count >= 5:
        return 100000
    if count == 4:
        if left_open and right_open:
            return 10000   # 活四
        elif left_open or right_open:
            return 1000    # 冲四
    if count == 3:
        if left_open and right_open:
            return 800     # 活三
        elif left_open or right_open:
            return 100     # 眠三/弱三
    if count == 2:
        if left_open and right_open:
            return 50      # 活二
        elif left_open or right_open:
            return 10
    if count == 1:
        return 2
    return 0

def evaluate_position(board, row, col, player):
    """综合评估某个空位下子的总得分（所有方向求和）"""
    total = 0
    for dr, dc in DIRECTIONS:
        total += evaluate_direction(board, row, col, dr, dc, player)
    return total

def ai_get_best_move():
    """AI 选择最佳落子位置：进攻分 + 防守分 * 0.9"""
    best_score = -1
    best_move = None
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                continue
            offense = evaluate_position(board, r, c, WHITE)   # AI 进攻
            defense = evaluate_position(board, r, c, BLACK)  # 防守（模拟玩家下这里）
            total = offense + defense * 0.9
            if total > best_score:
                best_score = total
                best_move = (r, c)
    return best_move

def ai_move():
    """AI 走一步，并更新游戏状态"""
    global current_turn, game_over, winner
    if game_over:
        return
    move = ai_get_best_move()
    if move is None:   # 棋盘满了，平局
        game_over = True
        winner = None
        return
    row, col = move
    board[row][col] = WHITE
    if check_win(row, col, WHITE):
        game_over = True
        winner = WHITE
    else:
        current_turn = BLACK

# ====================== 游戏逻辑函数 ======================
def check_win(row, col, player):
    """五子连珠胜利判定"""
    for dr, dc in DIRECTIONS:
        count = 1
        # 正方向
        for step in range(1, 5):
            nr, nc = row + dr * step, col + dc * step
            if nr < 0 or nr >= BOARD_SIZE or nc < 0 or nc >= BOARD_SIZE:
                break
            if board[nr][nc] == player:
                count += 1
            else:
                break
        # 反方向
        for step in range(1, 5):
            nr, nc = row - dr * step, col - dc * step
            if nr < 0 or nr >= BOARD_SIZE or nc < 0 or nc >= BOARD_SIZE:
                break
            if board[nr][nc] == player:
                count += 1
            else:
                break
        if count >= 5:
            return True
    return False

def place_stone(row, col, player):
    """落子，成功返回 True，失败返回 False"""
    if row is None or col is None:
        return False
    if board[row][col] != EMPTY:
        return False
    board[row][col] = player
    return True

def reset_game():
    """重置游戏状态"""
    global board, current_turn, game_over, winner
    board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    current_turn = BLACK
    game_over = False
    winner = None

def get_grid_pos(mx, my):
    """获取鼠标点击的棋盘坐标 (row, col)"""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            x = MARGIN + c * CELL_SIZE
            y = MARGIN + r * CELL_SIZE
            if ((mx - x) ** 2 + (my - y) ** 2) ** 0.5 < CELL_SIZE // 2:
                return r, c
    return None

# ====================== 主循环 ======================
clock = pygame.time.Clock()
running = True
btn_new_rect = pygame.Rect(0, 0, 0, 0)
btn_ai_rect = pygame.Rect(0, 0, 0, 0)

while running:
    # 绘制静态元素
    draw_board()
    draw_pieces()
    
    # 获取鼠标位置用于按钮高亮
    mouse_pos = pygame.mouse.get_pos()
    # 绘制按钮并更新全局矩形（用于事件检测）
    btn_new_rect = draw_button("New Game", WINDOW_WIDTH - 180, WINDOW_HEIGHT - 48, 80, 35,
                               hover=btn_new_rect.collidepoint(mouse_pos))
    btn_ai_rect = draw_button("AI First", WINDOW_WIDTH - 90, WINDOW_HEIGHT - 48, 80, 35,
                              hover=btn_ai_rect.collidepoint(mouse_pos))
    draw_info()   # 此函数内部会使用 btn_new_rect/btn_ai_rect 来判断悬停（但这里已提前计算，无妨）

    # 鼠标悬停高亮（仅在未结束时且轮到玩家时显示）
    if not game_over and current_turn == BLACK:
        mx, my = pygame.mouse.get_pos()
        pos = get_grid_pos(mx, my)
        if pos and board[pos[0]][pos[1]] == EMPTY:
            x = MARGIN + pos[1] * CELL_SIZE
            y = MARGIN + pos[0] * CELL_SIZE
            pygame.draw.circle(screen, HIGHLIGHT_COLOR, (x, y), CELL_SIZE//2 - 2, 3)

    pygame.display.update()

    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:   # 重置游戏
                reset_game()
            if event.key == pygame.K_f and not game_over and current_turn == BLACK:  # AI 先手
                current_turn = WHITE

        if event.type == pygame.MOUSEBUTTONDOWN:
            # 按钮点击
            if btn_new_rect.collidepoint(event.pos):
                reset_game()
                continue
            if btn_ai_rect.collidepoint(event.pos):
                if not game_over and current_turn == BLACK:
                    current_turn = WHITE
                continue

            # 玩家落子（仅当未结束且轮到玩家时）
            if not game_over and current_turn == BLACK:
                pos = get_grid_pos(*event.pos)
                if pos and place_stone(pos[0], pos[1], BLACK):
                    if check_win(pos[0], pos[1], BLACK):
                        game_over = True
                        winner = BLACK
                    else:
                        current_turn = WHITE

    # AI 回合
    if not game_over and current_turn == WHITE:
        pygame.time.wait(50)   # 略微延时，体现思考过程
        ai_move()

    clock.tick(60)

pygame.quit()