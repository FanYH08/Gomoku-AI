import pygame
import sys
import time

# ------------------- 配置参数 -------------------
BOARD_SIZE = 15          # 棋盘大小 15x15
CELL_SIZE = 40
MARGIN = 40
WINDOW_WIDTH = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1)
WINDOW_HEIGHT = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1)

# 棋子类型
EMPTY = 0
BLACK = 1   # 玩家（先手）
WHITE = 2   # AI（后手）

# 搜索深度（AI 思考的步数，2~3 可保证速度，深度越大越慢）
SEARCH_DEPTH = 2

# 颜色
BOARD_COLOR = (210, 180, 140)
LINE_COLOR = (0, 0, 0)
BLACK_STONE = (0, 0, 0)
WHITE_STONE = (255, 255, 255)

# 初始化 pygame
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Gomoku AI - Human vs AI")

# 使用默认字体（避免 SysFont 的兼容性问题）
font = pygame.font.Font(None, 24)
font_small = pygame.font.Font(None, 20)

# ------------------- 1. 棋盘与界面（李锦程部分） -------------------
def draw_board():
    screen.fill(BOARD_COLOR)
    for i in range(BOARD_SIZE):
        pygame.draw.line(screen, LINE_COLOR, (MARGIN, MARGIN + i*CELL_SIZE), (WINDOW_WIDTH-MARGIN, MARGIN + i*CELL_SIZE), 1)
        pygame.draw.line(screen, LINE_COLOR, (MARGIN + i*CELL_SIZE, MARGIN), (MARGIN + i*CELL_SIZE, WINDOW_HEIGHT-MARGIN), 1)
    # 星位标记（天元/小目）
    if BOARD_SIZE == 15:
        stars = [(3,3),(11,3),(7,7),(3,11),(11,11)]
    elif BOARD_SIZE == 9:
        stars = [(2,2),(6,2),(4,4),(2,6),(6,6)]
    else:
        stars = []
    for r,c in stars:
        x = MARGIN + c*CELL_SIZE
        y = MARGIN + r*CELL_SIZE
        pygame.draw.circle(screen, BLACK_STONE, (x,y), 5)

def draw_pieces(board):
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] == BLACK:
                color = BLACK_STONE
            elif board[row][col] == WHITE:
                color = WHITE_STONE
            else:
                continue
            x = MARGIN + col*CELL_SIZE
            y = MARGIN + row*CELL_SIZE
            pygame.draw.circle(screen, color, (x,y), CELL_SIZE//2 - 2)

def get_grid_pos(mx, my):
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            x = MARGIN + col*CELL_SIZE
            y = MARGIN + row*CELL_SIZE
            if ((mx - x)**2 + (my - y)**2)**0.5 < CELL_SIZE // 2:
                return row, col
    return None

# ------------------- 2. 胜负判断（蔡语霏部分） -------------------
def check_win(board, row, col, player):
    """检查在(row,col)落子后，player是否胜利"""
    dirs = [(1,0),(0,1),(1,1),(1,-1)]
    for dr, dc in dirs:
        count = 1
        # 正方向
        for step in range(1,5):
            nr, nc = row + dr*step, col + dc*step
            if nr<0 or nr>=BOARD_SIZE or nc<0 or nc>=BOARD_SIZE:
                break
            if board[nr][nc] == player:
                count += 1
            else:
                break
        # 反方向
        for step in range(1,5):
            nr, nc = row - dr*step, col - dc*step
            if nr<0 or nr>=BOARD_SIZE or nc<0 or nc>=BOARD_SIZE:
                break
            if board[nr][nc] == player:
                count += 1
            else:
                break
        if count >= 5:
            return True
    return False

# ------------------- 3. 评估函数（改编自蔡语霏的 evaluate.py） -------------------
WIN_SCORE = 100000

def get_line(board, row, col, dr, dc, piece):
    """返回 (连续相同棋子的个数, 左端是否开放, 右端是否开放)"""
    count = 1
    # 正方向
    r, c = row + dr, col + dc
    while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == piece:
        count += 1
        r += dr
        c += dc
    right_open = (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == EMPTY)
    # 负方向
    r, c = row - dr, col - dc
    while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == piece:
        count += 1
        r -= dr
        c -= dc
    left_open = (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == EMPTY)
    return count, left_open, right_open

def evaluate_direction(count, left_open, right_open):
    if count >= 5:
        return WIN_SCORE
    if count == 4 and left_open and right_open:
        return 100000
    if count == 4 and (left_open or right_open):
        return 50000
    if count == 3 and left_open and right_open:
        return 5000
    if count == 3 and (left_open ^ right_open):
        return 800
    if count == 2 and left_open and right_open:
        return 200
    if count == 2 and (left_open ^ right_open):
        return 50
    return 0

def evaluate_board(board, piece):
    """评估整个棋盘上 piece 方的总分数"""
    total_score = 0
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == piece:
                for dr, dc in directions:
                    # 避免重复计算同一条线段：只从线段起点开始
                    prev_r, prev_c = i - dr, j - dc
                    if 0 <= prev_r < BOARD_SIZE and 0 <= prev_c < BOARD_SIZE and board[prev_r][prev_c] == piece:
                        continue
                    count, left_open, right_open = get_line(board, i, j, dr, dc, piece)
                    score = evaluate_direction(count, left_open, right_open)
                    total_score += score
                    if score >= WIN_SCORE:
                        return WIN_SCORE
    return total_score

# ------------------- 4. AI 决策（Minimax + Alpha-Beta） -------------------
def get_legal_moves(board):
    """返回所有空位坐标列表（为加速，可以只考虑已有棋子周边2格，但先全遍历）"""
    moves = []
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == EMPTY:
                moves.append((i, j))
    return moves

def minimax(board, depth, alpha, beta, is_maximizing, last_move=None):
    """
    is_maximizing = True: AI（白棋）最大化自己分数
    返回当前局面的评估分数（从AI视角）
    """
    # 检查胜负（快速判定，基于最后落子）
    if last_move:
        r, c = last_move
        player = board[r][c]
        if player != EMPTY and check_win(board, r, c, player):
            if player == WHITE:
                return WIN_SCORE - depth   # AI赢
            else:
                return -WIN_SCORE + depth # 玩家赢

    if depth == 0:
        # 叶子节点：用评估函数打分（AI为WHITE）
        return evaluate_board(board, WHITE) - evaluate_board(board, BLACK)

    if is_maximizing:
        max_eval = -float('inf')
        for (r, c) in get_legal_moves(board):
            board[r][c] = WHITE
            eval = minimax(board, depth-1, alpha, beta, False, (r,c))
            board[r][c] = EMPTY
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for (r, c) in get_legal_moves(board):
            board[r][c] = BLACK
            eval = minimax(board, depth-1, alpha, beta, True, (r,c))
            board[r][c] = EMPTY
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def best_move(board, depth):
    """AI 选择最佳落子位置（返回值 (row, col)）"""
    best_val = -float('inf')
    best_pos = None
    for (r, c) in get_legal_moves(board):
        board[r][c] = WHITE
        move_val = minimax(board, depth-1, -float('inf'), float('inf'), False, (r,c))
        board[r][c] = EMPTY
        if move_val > best_val:
            best_val = move_val
            best_pos = (r, c)
    return best_pos

# ------------------- 5. 主游戏循环（整合） -------------------
def main():
    board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    current_turn = BLACK   # 玩家先手
    game_over = False
    winner = None
    clock = pygame.time.Clock()

    draw_board()
    pygame.display.update()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if not game_over and event.type == pygame.MOUSEBUTTONDOWN:
                if current_turn == BLACK:   # 玩家回合
                    pos = get_grid_pos(*pygame.mouse.get_pos())
                    if pos and board[pos[0]][pos[1]] == EMPTY:
                        r, c = pos
                        board[r][c] = BLACK
                        draw_board()
                        draw_pieces(board)
                        pygame.display.update()

                        if check_win(board, r, c, BLACK):
                            game_over = True
                            winner = "Player"
                        else:
                            current_turn = WHITE   # 切换到 AI 回合

        # AI 回合（非游戏结束并且轮到 AI）
        if not game_over and current_turn == WHITE:
            # 显示思考中
            text = font_small.render("AI thinking...", True, (0,0,0))
            screen.blit(text, (10, WINDOW_HEIGHT-30))
            pygame.display.update()

            start = time.time()
            move = best_move(board, SEARCH_DEPTH)
            elapsed = time.time() - start
            print(f"AI thinking time: {elapsed:.2f} sec")

            if move:
                r, c = move
                board[r][c] = WHITE
                draw_board()
                draw_pieces(board)
                pygame.display.update()

                if check_win(board, r, c, WHITE):
                    game_over = True
                    winner = "AI"
                else:
                    current_turn = BLACK
            else:
                # 无合法走法，平局
                game_over = True
                winner = "Draw"

        # 刷新界面
        draw_board()
        draw_pieces(board)
        # 显示状态文字
        if not game_over:
            if current_turn == BLACK:
                msg = "Your turn (Black)"
            else:
                msg = "AI turn (White)"
        else:
            if winner == "Player":
                msg = "You win! Close window to exit"
            elif winner == "AI":
                msg = "AI wins! Close window to exit"
            else:
                msg = "Draw! Close window to exit"
        text = font.render(msg, True, (0,0,0))
        screen.blit(text, (10, 10))
        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main()