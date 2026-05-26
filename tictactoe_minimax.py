import sys

# 棋盘用列表表示：['X','O',' '...] 共9个格子
board = [' '] * 9

def print_board():
    print("\n")
    for i in range(0, 9, 3):
        print(f" {board[i]} | {board[i+1]} | {board[i+2]}")
        if i < 6:
            print("---|---|---")

def check_winner(board_state, player):
    # 所有赢法组合
    win_patterns = [(0,1,2), (3,4,5), (6,7,8),  # 行
                    (0,3,6), (1,4,7), (2,5,8),  # 列
                    (0,4,8), (2,4,6)]           # 对角
    for (a,b,c) in win_patterns:
        if board_state[a] == board_state[b] == board_state[c] == player:
            return True
    return False

def is_full(board_state):
    return ' ' not in board_state

def evaluate(board_state):
    if check_winner(board_state, 'O'):
        return 10
    elif check_winner(board_state, 'X'):
        return -10
    else:
        return 0

def minimax(board_state, is_ai_turn):
    score = evaluate(board_state)
    if score == 10 or score == -10 or is_full(board_state):
        return score
    if is_ai_turn:
        best = -float('inf')
        for i in range(9):
            if board_state[i] == ' ':
                board_state[i] = 'O'
                best = max(best, minimax(board_state, False))
                board_state[i] = ' '
        return best
    else:
        best = float('inf')
        for i in range(9):
            if board_state[i] == ' ':
                board_state[i] = 'X'
                best = min(best, minimax(board_state, True))
                board_state[i] = ' '
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