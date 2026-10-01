"""Chess Security System: beat the engine, then enter the password to open the vault.
Run: python chess_gui.py [vault_file]"""
import sys, os, tkinter as tk
from tkinter import messagebox, simpledialog
import chess
from engine import Engine
from vault import decrypt_file

GLYPH = {"P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",
         "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚"}
SQ = 64


class App(tk.Tk):
    def __init__(self, vault):
        super().__init__()
        self.title("Chess Security System")
        self.vault, self.board, self.sel, self.busy = vault, chess.Board(), None, False
        self.engine = Engine()
        self.cv = tk.Canvas(self, width=8 * SQ, height=8 * SQ)
        self.cv.pack()
        self.status = tk.Label(self, font=("Arial", 12))
        self.status.pack(pady=4)
        self.cv.bind("<Button-1>", self.click)
        self.draw()
        self.say(f"Vault locked. Win as White to unlock.  Opponent: {self.engine.name}")

    def say(self, t):
        self.status.config(text=t)

    def draw(self):
        self.cv.delete("all")
        for sq in chess.SQUARES:
            f, r = chess.square_file(sq), 7 - chess.square_rank(sq)
            col = "#f0d9b5" if (f + r) % 2 == 0 else "#b58863"
            if sq == self.sel:
                col = "#f7ec6e"
            self.cv.create_rectangle(f * SQ, r * SQ, (f + 1) * SQ, (r + 1) * SQ, fill=col, width=0)
            p = self.board.piece_at(sq)
            if p:
                self.cv.create_text(f * SQ + SQ // 2, r * SQ + SQ // 2, text=GLYPH[p.symbol()],
                                    font=("DejaVu Sans", 38), fill="black")

    def click(self, e):
        if self.busy or self.board.is_game_over():
            return
        sq = chess.square(e.x // SQ, 7 - e.y // SQ)
        if self.sel is None:
            p = self.board.piece_at(sq)
            if p and p.color == chess.WHITE:
                self.sel = sq
        else:
            mv = chess.Move(self.sel, sq)
            if chess.Move(self.sel, sq, chess.QUEEN) in self.board.legal_moves:
                mv = chess.Move(self.sel, sq, chess.QUEEN)  # auto-queen
            self.sel = None
            if mv in self.board.legal_moves:
                self.board.push(mv)
                self.draw()
                if not self.check_end():
                    self.busy = True
                    self.say("Engine thinking...")
                    self.after(100, self.reply)
        self.draw()

    def reply(self):
        self.board.push(self.engine.best_move(self.board))
        self.busy = False
        self.draw()
        if not self.check_end():
            self.say("Your move (White)." + ("  CHECK!" if self.board.is_check() else ""))

    def check_end(self):
        if not self.board.is_game_over():
            return False
        if self.board.is_checkmate() and self.board.turn == chess.BLACK:
            self.say("Checkmate - you win!")
            self.unlock()
        else:
            self.say("Access denied - you did not win. Restarting.")
            messagebox.showwarning("Access denied", "You did not win. Try again.")
            self.board = chess.Board(); self.draw()
        return True

    def unlock(self):
        pw = simpledialog.askstring("Vault", "Challenge won. Enter vault password:", show="*")
        try:
            path = decrypt_file(self.vault, pw or "", "unlocked")
            messagebox.showinfo("Unlocked", f"File decrypted to:\n{os.path.abspath(path)}")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))
        self.board = chess.Board(); self.draw()

    def destroy(self):
        self.engine.close(); super().destroy()


if __name__ == "__main__":
    vault = sys.argv[1] if len(sys.argv) > 1 else "secret_demo.txt.vault"
    App(vault).mainloop()
