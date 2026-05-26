import sys

# 棋盘用列表表示：['X','O',' '...] 共9个格子
board = [' '] * 9

def print_board():
    print("\n")
    for i in range(0, 9, 3):
        print(f" {board[i]} | {board[i+1]} | {board[i+2]}")
        if i < 6:
            print("---|---|---")

def check_winner(b, player):
    # 所有赢法组合
    win_patterns = [(0,1,2), (3,4,5), (6,7,8),  # 行
                    (0,3,6), (1,4,7), (2,5,8),  # 列
                    (0,4,8), (2,4,6)]           # 对角
    for a,b,c in win_patterns:
        if b[a] == b[b] == b[c] == player:
            return True
    return False

def is_full(b):
    return ' ' not in b

def evaluate(b):
    # 评估函数：AI（'O'）赢返回10，玩家（'X'）赢返回-10，平局0
    if check_winner(b, 'O'):
        return 10
    elif check_winner(b, 'X'):
        return -10
    else:
        return 0

def minimax(b, is_ai_turn):
    score = evaluate(b)
    if score == 10 or score == -10 or is_full(b):
        return score
    if is_ai_turn:
        best = -float('inf')
        for i in range(9):
            if b[i] == ' ':
                b[i] = 'O'
                best = max(best, minimax(b, False))
                b[i] = ' '
        return best
    else:
        best = float('inf')
        for i in range(9):
            if b[i] == ' ':
                b[i] = 'X'
                best = min(best, minimax(b, True))
                b[i] = ' '
        return best

def best_move():
    best_val = -float('inf')
    move = -1
    for i in range(9):
        if board[i] == ' ':
            board[i] = 'O'
            move_val = minimax(board, False)
            board[i] = ' '
            if move_val > best_val:
                best_val = move_val
                move = i
    return move

def main():
    print("井字棋（Minimax演示），你是 X，AI 是 O。")
    print_board()
    turn = 'X'   # 玩家先手
    while True:
        if turn == 'X':
            try:
                pos = int(input("请输入位置(1-9): ")) - 1
            except:
                print("输入数字1-9")
                continue
            if pos < 0 or pos > 8 or board[pos] != ' ':
                print("位置无效")
                continue
            board[pos] = 'X'
        else:
            print("AI 思考中...")
            pos = best_move()
            board[pos] = 'O'
        print_board()
        if check_winner(board, turn):
            print(f"{turn} 赢了！")
            break
        if is_full(board):
            print("平局")
            break
        turn = 'O' if turn == 'X' else 'X'

if __name__ == "__main__":
    main()