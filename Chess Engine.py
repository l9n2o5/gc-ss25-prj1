import sys
import re 
import random
from IPython.display import display, clear_output
import time

class ChessGame:
    def __init__(self, clock_time=None):
        self.board = self.initialize_board()
        self.turn = 'white' 
        self.move_history = []
        self.game_over = False
        self.no_capture_moves = 0  # Counts moves with no capture or pawn moves for the 50-move rule.
        self.en_passant_target = None  # (row, col) or None.
        self.castling_rights = [['.', '.', '.', '.', '.', '.', '.', '.'],  
                                ['.', '.', '.', '.', '.', '.', '.', '.'],  
                                ['.', '.', '.', '.', '.', '.', '.', '.'],
                                ['.', '.', '.', '.', '.', '.', '.', '.'],
                                ['.', '.', '.', '.', '.', '.', '.', '.'],
                                ['.', '.', '.', '.', '.', '.', '.', '.'],
                                ['.', '.', '.', '.', '.', '.', '.', '.'],  
                                ['.', '.', '.', '.', '.', '.', '.', '.']]
        self.clock_time = clock_time
        if clock_time:
            self.timers = {'white': clock_time, 'black': clock_time}
            self.last_move_time = time.time()

    def initialize_board(self):
        """Initializes the chess board with the standard starting position."""
        board = [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],  # Row 0, Rank 8: Black back rank
            ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],   # Row 1, Rank 7: Black pawns (note: e7 is missing because that pawn has moved)
            ['.', '.', '.', '.', '.', '.', '.', '.'],    # Row 2, Rank 6: Empty
            ['.', '.', '.', '.', '.', '.', '.', '.'],      # Row 3, Rank 5: Black pawn on e5 and white pawn on f5
            ['.', '.', '.', '.', '.', 'P', '.', '.'],     # Row 4, Rank 4: Empty
            ['.', '.', '.', '.', '.', '.', '.', '.'],     # Row 5, Rank 3: Empty
            ['P', 'P', 'P', 'P', 'P', '.', 'P', 'P'],      # Row 6, Rank 2: White pawns (f-pawn is missing since it advanced to f5)
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']   # White pieces
        ]
        return board
    
    def print_board(self):
        """Prints the board as an 8x8 grid with row and column labels and the current player's turn."""
        # clear_output(wait=False)
        print("  a b c d e f g h")
        print("  ----------------")
        for i, row in enumerate(self.board):
            print(f"{8 - i}| {' '.join(row)} |{8 - i}")
        print("  ----------------")
        print("  a b c d e f g h")
        
        if self.clock_time:
            print(f"White's time: {self.timers['white']:.2f} seconds")
            print(f"Black's time: {self.timers['black']:.2f} seconds")

    def update_turn(self):
        """Updates the turn attribute to the next player."""
        if self.clock_time:
            current_time = time.time()
            elapsed_time = current_time - self.last_move_time
            self.timers[self.turn] -= elapsed_time
            self.last_move_time = current_time

            if self.timers[self.turn] <= 0:
                print(f"{self.turn.capitalize()} ran out of time. Game over.")
                self.game_over = True
                return
        self.turn = 'black' if self.turn == 'white' else 'white'

    def is_in_check(self, color):
        """Determines if the king of the given color is in check."""
        # Define king symbol based on color
        king_symbol = 'K' if color == 'white' else 'k'
        king_pos = None

        # Locate the king on the board
        for row in range(8):
            for col in range(8):
                if self.board[row][col] == king_symbol:
                    king_pos = (row, col)
                    break
            if king_pos:
                break

        # If king isn't found, something is wrong—but we assume it's there.
        if king_pos is None:
            return False

        # Determine opponent color
        opponent_color = 'black' if color == 'white' else 'white'

        # Check every square for an opponent's piece that could attack the king
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '.':
                    # Check if the piece belongs to the opponent.
                    if (opponent_color == 'white' and piece.isupper()) or (opponent_color == 'black' and piece.islower()):
                        # For pawn moves, make sure our is_valid_move handles both upper and lower cases.
                        if self.is_valid_move(piece, (row, col), king_pos):
                            return True

        return False


    def generate_legal_moves(self):
        """
        Generates all legal moves for the current player.
        A move is legal if it is valid for the piece and does not leave the king in check.
        Returns a list of moves where each move is represented as ((start_row, start_col), (end_row, end_col)).
        """
        legal_moves = []

        # Loop over every square of the board.
        for start_row in range(8):
            for start_col in range(8):
                piece = self.board[start_row][start_col]
                if piece == '.':
                    continue

                # Only consider pieces for the current player.
                if (self.turn == 'white' and piece.isupper()) or (self.turn == 'black' and piece.islower()):
                    # Try moving to every possible square.
                    for end_row in range(8):
                        for end_col in range(8):
                            # Check if the move is valid based on the piece movement.
                            if self.is_valid_move(piece, (start_row, start_col), (end_row, end_col)): # might add .upper() to piece
                                # Simulate the move.
                                board_copy = [row[:] for row in self.board]  # Deep copy of the board.
                                board_copy[start_row][start_col] = '.'
                                board_copy[end_row][end_col] = piece

                                # Temporarily update the board for the check test.
                                original_board = self.board
                                self.board = board_copy
                                
                                # Temporarily update the turn for the check test.
                                original_turn = self.turn
                                self.turn = 'black' if self.turn == 'white' else 'white'

                                # If the king is not in check after this move, it is legal.
                                if not self.is_in_check(original_turn):
                                    legal_moves.append(((start_row, start_col), (end_row, end_col)))

                                # Restore the original board and turn.
                                self.board = original_board
                                self.turn = original_turn

        return legal_moves


    def check_game_state(self):
        """
        Checks whether the game is in checkmate, stalemate or the 50-move rule applies.
        - If there were 50 moves without a capture or a pawn move, it's a draw.
        - If there are no legal moves and the king is in check, it's checkmate.
        - If there are no legal moves and the king is not in check, it's stalemate.
        """
        
        if self.no_capture_moves >= 50:
            print("Draw by the 50-move rule!")
            self.game_over = True
            return
        
        legal_moves = self.generate_legal_moves()
    
        if not legal_moves:
            if self.is_in_check(self.turn):
                print("Checkmate!")
                if self.turn == 'white':
                    print("Black wins!")
                else:
                    print("White wins!")
                self.game_over = True
            else:
                print("Stalemate!")
                self.game_over = True





    def make_move(self, parsed_move):
        """" Makes a move on the board given a parsed move."""
        [possible_starts, piece, target_col, target_row] = parsed_move

        if len(possible_starts) == 0:
            print("Invalid move.")
            return False 
        elif len(possible_starts) > 1:
            print("Ambiguous move. More context needed.")
            return False 
        elif len(possible_starts) == 1:
            start_row, start_col = possible_starts[0]
            target_square_before = self.board[target_row][target_col] # Check what is on the target square before the move.
            
            # Check if this move qualifies as an en passant capture using the current en passant target.
            en_passant_capture = False
            if piece.upper() == 'P' and abs(target_col - start_col) == 1 and target_square_before == '.' and self.en_passant_target == (target_row, target_col):
                en_passant_capture = True
            
            # Move execution
            self.board[start_row][start_col]   = '.'     
            self.board[target_row][target_col] = piece  

            # Check if this is an en passant capture.
            if en_passant_capture:
                captured_row = target_row + (1 if piece.isupper() else -1)
                self.board[captured_row][target_col] = '.' # Remove the captured pawn.
                self.no_capture_moves = 0
            elif target_square_before != '.' or piece.upper() == 'P': # For 50-move rule: reset counter if a pawn moves or a capture is made.
                self.no_capture_moves = 0
            else:
                self.no_capture_moves += 1
                
            if piece.upper() == 'P' and abs(target_row - start_row) == 2:
                direction = -1 if piece.isupper() else 1
                self.en_passant_target = (start_row + direction, start_col)
            else:
                self.en_passant_target = None

            if piece in ['r', 'R', 'k', 'K']:
                self.castling_rights[start_row][start_col] = '1'
                
            return True
        



    # PRE: start and end not out of bounds 
    def is_valid_move(self, piece_symbol, start, end):
        """Checks if the piece can legally move to the target square."""
        board = self.board
        start_row, start_col = start
        end_row,     end_col = end
        
        # Prevent capturing your own pieces.
        start_piece = board[start_row][start_col]
        end_piece = board[end_row][end_col]
        if end_piece != '.' and start_piece.isupper() == end_piece.isupper():
            return False
        
        # Use an uppercase version for comparisons.
        upper_piece = piece_symbol.upper()
        

        if upper_piece == 'P':
            direction = -1 if board[start_row][start_col].isupper() else 1  # White moves up (-1), Black moves down (+1)
            if start_col == end_col and ((end_row == start_row + direction and board[end_row][end_col] == '.') or
                                     (start_row in (1, 6) and end_row == start_row + 2 * direction and 
                                      board[start_row + direction][start_col] == '.' and board[end_row][end_col] == '.')):
                return True  # Normal move forward
            if abs(end_col - start_col) == 1 and end_row == start_row + direction and board[end_row][end_col] != '.':
                return True  # Capturing move
            elif self.en_passant_target == (end_row, end_col):
                return True # En passant: the pawn can capture the opponent's pawn that just moved two squares forward.
            
        elif upper_piece == 'N':
            if (abs(start_row - end_row), abs(start_col - end_col)) in [(2, 1), (1, 2)]:
                return True
        elif upper_piece == 'B':
            if abs(start_row - end_row) == abs(start_col - end_col):
                step_row = 1 if end_row > start_row else -1
                step_col = 1 if end_col > start_col else -1
                for i in range(1, abs(start_row - end_row)):
                    if board[start_row + i * step_row][start_col + i * step_col] != '.':
                        return False  # Blocked path
                return True
        elif upper_piece == 'R':
            if start_row == end_row or start_col == end_col:
                step_row = (end_row - start_row) // max(1, abs(end_row - start_row))
                step_col = (end_col - start_col) // max(1, abs(end_col - start_col))
                for i in range(1, max(abs(end_row - start_row), abs(end_col - start_col))):
                    if board[start_row + i * step_row][start_col + i * step_col] != '.':
                        return False  # Blocked path
                return True
        elif upper_piece == 'Q':
            return self.is_valid_move('R', start, end) or self.is_valid_move('B', start, end)
        elif upper_piece == 'K':
            return max(abs(start_row - end_row), abs(start_col - end_col)) == 1
        
        return False




    def translated_move(self, parsed_move):
        """Finds the starting position of a piece given a move and the end position"""

        # Extract the move components
        piece_symbol, disambiguation_file, disambiguation_rank, target_square, _ = parsed_move

        # Convert the target square to coordinates
        target_col = ord(target_square[0]) - ord('a')
        target_row = 8 - int(target_square[1])

        piece = "-"
        # Find all possible starting squares for the piece
        possible_starts = []
        for row in range(8):
            for col in range(8):
                board_piece = self.board[row][col]

                # Check if the piece belongs to the current player and matches the piece symbol
                if ((self.turn == 'white' and board_piece.isupper() and board_piece == piece_symbol) 
                or  (self.turn == 'black' and board_piece.islower() and board_piece == piece_symbol.lower())):
                        # Check if the move specifies a column and row for disambiguation
                        if not disambiguation_file or col == ord(disambiguation_file) - ord('a'):
                            if not disambiguation_rank or row == 8 - int(disambiguation_rank):
                                # Check if the piece can move to the target square 
                                if self.is_valid_move(piece_symbol, (row, col), (target_row, target_col)):
                                    possible_starts.append((row, col))
                                    piece = board_piece
        
        return [possible_starts, piece, target_col, target_row]
    




    def pawn_promotion(self, parsed_move):
        """Makes move if move is pawn promotion"""
        piece_symbol, disambiguation_file, disambiguation_rank, target_square, pawn_promotion_piece = parsed_move
        pawn_promotion_move = self.translated_move(parsed_move)
        pawn_promotion_move[1] = pawn_promotion_piece
        return pawn_promotion_move



    def parse_move(self, move):
        move_pattern = re.compile(r'([KQRBN]?)([a-h]?)([1-8]?)x?([a-h][1-8])(?:=([QRBN]))?[+#]?') 
        match = move_pattern.fullmatch(move)
        a, b, c, d, e = match.groups()
        if a == '':
            a = 'P'
        return [a, b, c, d, e]

    def valid_move_format(self,move):
        move_pattern = re.compile(r'([KQRBN]?)([a-h]?)([1-8]?)x?([a-h][1-8])(?:=([QRBN]))?[+#]?') 
        if not move_pattern.fullmatch(move):
            return False
        return True
    
    def castling(self,move):
        ### validate castling conditions: 
        
        # from turn and king/queenside -> find starting position of rook 
            # check if king is at starting position 
            # check if rook is at starting position 
                # check if board is empty between rook and king 
                # check if king or rook have been moved before 
        if self.turn == "white": 
            if self.board[7][4] != 'K':
                print("King not found. Invalid move.")
                return False
            if (move == "0-0" and self.board[7][7] != 'R') or (move == "0-0-0" and self.board[7][0] != 'R'):
                print("Rook not found. Invalid move.")
                return False
            if move == "0-0":
                for piece in self.board[7][5:7]:
                    if piece != '.':
                        print("board is not empty between king and rook")
                        return False
                if self.castling_rights[7][4] == '1' or self.castling_rights[7][7] == '1':
                    print("Rook or King have been moved before")
                    return False
                self.board[7][4] = '.'
                self.board[7][5] = 'R'
                self.board[7][6] = 'K'
                self.board[7][7] = '.'
            if move == "0-0-0":
                for piece in self.board[7][1:4]:
                    if piece != '.':
                        print("board is not empty between king and rook")
                        return False  
                if self.castling_rights[7][0] == '1' or self.castling_rights[7][4] == '1':
                    print("Rook or King have been moved before")
                    return False
                self.board[7][0] = '.'
                self.board[7][1] = '.'
                self.board[7][2] = 'K'
                self.board[7][3] = 'R'
                self.board[7][4] = '.'
                         

        if self.turn == "black": 
            if self.board[0][4] != 'k': 
                print("King not found")
                return False
            if (move == "0-0" and self.board[0][0] != 'r') or (move == "0-0-0" and self.board[0][7] != 'r'):
                print("Rook not found. Invalid move.")
                return False
            if move == "0-0":
                for piece in self.board[0][5:7]:
                    if piece != '.':
                        print("board is not empty between king and rook")
                        return False
                if self.castling_rights[0][7] == '1' or self.castling_rights[0][4] == '1':
                    print("Rook or King have been moved before")
                    return False
                self.board[0][4] = '.'
                self.board[0][5] = 'r'
                self.board[0][6] = 'k'
                self.board[0][7] = '.'
            if move == "0-0-0":
                for piece in self.board[0][1:4]:
                    if piece != '.':
                        print("board is not empty between king and rook")
                        return False 
                if self.castling_rights[0][0] == '1' or self.castling_rights[0][4] == '1':
                    print("Rook or King have been moved before")
                    return False
                self.board[0][0] = '.'
                self.board[0][1] = '.'
                self.board[0][2] = 'k'
                self.board[0][3] = 'r'
                self.board[0][4] = '.'
        return True

    def generate_random_position(self):
        """Generates a random valid position with white king, white rook, and black king."""
        while True:
            wk_row, wk_col = random.randint(0, 7), random.randint(0, 7)  # White king
            wr_row, wr_col = random.randint(0, 7), random.randint(0, 7)  # White rook
            bk_row, bk_col = random.randint(0, 7), random.randint(0, 7)  # Black king

            # Ensure the kings are not adjacent
            if abs(wk_row - bk_row) <= 1 and abs(wk_col - bk_col) <= 1:
                continue

            # Ensure the rook is not giving check to the black king
            if wr_row == bk_row or wr_col == bk_col:
                continue

            # Ensure all pieces are on different squares
            if (wk_row, wk_col) == (wr_row, wr_col) or (wk_row, wk_col) == (bk_row, bk_col) or (wr_row, wr_col) == (bk_row, bk_col):
                continue

            # Place the pieces on the board
            self.board = [['.' for _ in range(8)] for _ in range(8)]
            self.board[wk_row][wk_col] = 'K'
            self.board[wr_row][wr_col] = 'R'
            self.board[bk_row][bk_col] = 'k'
            self.turn = 'white'
            self.move_history = []
            self.game_over = False
            return

    def compute_white_move(self):
        """Computes a move for white to achieve checkmate."""
        legal_moves = self.generate_legal_moves()
        for move in legal_moves:
            start, end = move
            start_piece = self.board[start[0]][start[1]]
            end_piece = self.board[end[0]][end[1]]

            # Simulate the move
            self.board[start[0]][start[1]] = '.'
            self.board[end[0]][end[1]] = start_piece

            # Check if the move leads to checkmate
            if not self.is_in_check('black') and len(self.generate_legal_moves()) == 0:
                return move  # Return the move that leads to checkmate

            # Undo the move
            self.board[start[0]][start[1]] = start_piece
            self.board[end[0]][end[1]] = end_piece

        # If no immediate checkmate, return the first legal move
        return legal_moves[0] if legal_moves else None

    # Assunptions: only valid pawn moves and resign
    def play(self):
        self.print_board()

        while not self.game_over: 
            move = input(f"{self.turn.capitalize()}'s move: ") 
            
            if move.lower() == "resign": 
                print(f"{self.turn.capitalize()} resigns. Game over.")
                self.game_over = True
                break
            
            
            if move.lower() == "(=)": 
                answer = input("Does Opponent accept draw? (yes/no)")
                if answer == "yes":
                    print(f"Players agreeded on a draw. Game over.")
                    self.game_over = True
                    break
                elif answer ==  "no":
                    print(f"Opponent did not accept draw.")
                    continue


            if move in ["0-0", "0-0-0"]:
                if self.castling(move) == True:
                    print("Castling possible")
                    self.update_turn()   
                    self.check_game_state() 
                    self.move_history.append(move)
                    self.print_board()
                else:
                    print("Castling not possible")
                continue


            if not self.valid_move_format(move):
                print("Invalid move format.")
                continue


            parsed_move = self.parse_move(move)
            
            if parsed_move[4] != None:
                if self.make_move(self.pawn_promotion(parsed_move)):
                    self.update_turn()   
                    self.check_game_state() 
                    self.move_history.append(move)               

            else:
                if self.make_move(self.translated_move(parsed_move)):
                    self.update_turn()   
                    self.check_game_state() 
                    self.move_history.append(move)
            
            self.print_board()
            
            if self.clock_time and self.timers[self.turn] <= 0:
                print(f"{self.turn.capitalize()} ran out of time. Game over.")
                self.game_over = True
                break
            

        print(self.move_history)
        
    def play_end_game(self):
            self.generate_random_position()
            self.print_board()

            move_count = 0
            while not self.game_over and move_count < 50:
                if self.turn == 'white':
                    move = self.compute_white_move()
                    if move:
                        start, end = move
                        self.make_move([[start], self.board[start[0]][start[1]], end[1], end[0]])
                        print(f"White's move: {chr(start[1] + ord('a'))}{8 - start[0]} -> {chr(end[1] + ord('a'))}{8 - end[0]}")
                    else:
                        print("No legal moves for white.")
                        break
                else:
                    move = input("Black's move: ")
                    if not self.valid_move_format(move):
                        print("Invalid move format.")
                        continue
                    parsed_move = self.parse_move(move)
                    if not self.make_move(self.translated_move(parsed_move)):
                        print("Invalid move.")
                        continue

                self.update_turn()
                self.check_game_state()
                self.print_board()
                self.move_history.append(move)
                move_count += 1

            if move_count >= 50:
                print("50-move rule reached. Game over.")
            print("Game over.")
            print("Move history:", self.move_history)


if __name__ == "__main__":
    print("Choose a mode to play:")
    print("1. Normal Mode")
    print("2. Timed Mode")
    print("3. Endgame Mode")
    
    mode = input("Enter the number corresponding to your choice: ").strip()
    
    if mode == "1":
        game = ChessGame()
        game.turn = "white"
        game.play()
    elif mode == "2":
        clock_time = input("Enter the time (in seconds) for each player: ").strip()
        try:
            clock_time = int(clock_time)
            game = ChessGame(clock_time=clock_time)
            game.turn = "white"
            game.play()
        except ValueError:
            print("Invalid input for time. Please enter an integer.")
    elif mode == "3":
        game = ChessGame() 
        game.turn = "white"
        game.play_end_game()
    else:
        print("Invalid choice. Please restart the program and choose a valid mode.")

