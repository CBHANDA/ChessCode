"""Chess opponent. Uses Stockfish (UCI) if found, else a built-in alpha-beta engine."""
import os, shutil, random
import chess, chess.engine

VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}


def find_stockfish():
    for c in (shutil.which("stockfish"), "stockfish.exe", "./stockfish", "./stockfish.exe",
              "/usr/games/stockfish", "C:/stockfish/stockfish.exe"):
        if c and os.path.exists(c) or (c and shutil.which(c)):
            return c
    return None


class Engine:
    def __init__(self, level=3, depth=2):
        self.depth, self.sf = depth, None
        path = find_stockfish()
        if path:
            try:
                self.sf = chess.engine.SimpleEngine.popen_uci(path)
                self.sf.configure({"Skill Level": level})
            except Exception:
                self.sf = None
        self.name = "Stockfish (UCI)" if self.sf else f"Built-in alpha-beta (depth {depth})"

    def _eval(self, b):  # from side-to-move's view
        if b.is_checkmate():
            return -99999
        if b.is_stalemate() or b.is_insufficient_material():
            return 0
        s = 0
        for sq, p in b.piece_map().items():
            v = VALUES[p.piece_type]
            if p.piece_type == chess.PAWN:  # push pawns, favour centre
                r = chess.square_rank(sq) if p.color else 7 - chess.square_rank(sq)
                v += r * 5
            if chess.square_file(sq) in (3, 4) and chess.square_rank(sq) in (3, 4):
                v += 10
            s += v if p.color == b.turn else -v
        return s

    def _search(self, b, d, alpha, beta):
        if d == 0 or b.is_game_over():
            return self._eval(b)
        for m in sorted(b.legal_moves, key=lambda m: b.is_capture(m), reverse=True):
            b.push(m)
            score = -self._search(b, d - 1, -beta, -alpha)
            b.pop()
            if score >= beta:
                return beta
            alpha = max(alpha, score)
        return alpha

    def best_move(self, board):
        if self.sf:
            return self.sf.play(board, chess.engine.Limit(time=0.2)).move
        best, best_s = [], -10**9
        for m in board.legal_moves:
            board.push(m)
            s = -self._search(board, self.depth - 1, -10**9, 10**9)
            board.pop()
            if s > best_s:
                best, best_s = [m], s
            elif s == best_s:
                best.append(m)
        return random.choice(best)

    def close(self):
        if self.sf:
            self.sf.quit()
