using DataLayer;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BizLogic
{
    public static class TicTacToeLogic
    {
        /// <summary>
        /// Extension method. Toggles between player X and O.
        /// </summary>
        /// <param name="board">The TicTacToeBoard instance to toggle.</param>
        public static void SwitchPlayers(this TicTacToeBoard board)
        {
            if (board != null)
                board.CurrentPlayer = (board.CurrentPlayer == "X") ? "O" : "X";
        }

        /// <summary>
        /// Extension method. Determines is player X is the winner.
        /// </summary>
        /// <param name="board">The TicTacToeBoard whose status is to be checked.</param>
        /// <returns>True if X is the winner.  False if either O is the winner or the game is not over.</returns>
        public static bool IsXTheWinner(this TicTacToeBoard board)
        {
            bool whoWins;
            return (IsWinner(board, out whoWins) && whoWins);
        }

        /// <summary>
        /// Extension method. Determines if player O is the winner.
        /// </summary>
        /// <param name="board">The TicTacToeBoard whose status is to be checked.</param>
        /// <returns>Trye if O is the winner. False if either X is the winner or the game is not over.</returns>
        public static bool IsOTheWinner(this TicTacToeBoard board)
        {
            bool whoWins;
            return (IsWinner(board, out whoWins) && !whoWins);
        }

        /// <summary>
        /// Extension method.  Determines if the board is full.
        /// </summary>
        /// <param name="board">The TicTacToeBoard whose status is to be checked for fullness.</param>
        /// <returns>True if the board is full.  False otherwise.</returns>
        public static bool BoardIsFull(this TicTacToeBoard board)
        {
            return (board.TopLeft != null && board.TopCenter != null && board.TopRight != null &&
               board.CenterLeft != null && board.Center != null && board.CenterRight != null &&
               board.BottomLeft != null && board.BottomCenter != null && board.BottomRight != null);
        }

        /// <summary>
        /// Extension method.  Determines if a game is over.
        /// </summary>
        /// <param name="board">The TicTacToeBoard whose completion status is to be checked.</param>
        /// <returns>True if the game is over.  False otherwise.</returns>
        public static bool IsGameOver(this TicTacToeBoard board)
        {
            return (board.IsXTheWinner() || board.IsOTheWinner() || board.BoardIsFull());
        }


        /// <summary>
        /// Extension method. Private.  Determines which player, if any, as won.
        /// </summary>
        /// <param name="board">The TicTacToeBoard whose status is to be checked for a winning player</param>
        /// <param name="winner">True if X wins. True if O wins.</param>
        /// <returns>True if somebody has one (in which case inspect parameter 'winner'). False otherwise.</returns>
        private static bool IsWinner(this TicTacToeBoard board, out bool winner)
        {
            winner = false;

            for (int x = 0; x < 2; x++)
            {
                bool valToTest = (x == 0);

                if ((board.TopLeft == valToTest && board.TopCenter == valToTest && board.TopRight == valToTest) ||
                    (board.CenterLeft == valToTest && board.Center == valToTest && board.CenterRight == valToTest) ||
                    (board.BottomLeft == valToTest && board.BottomCenter == valToTest && board.BottomRight == valToTest) ||
                    (board.TopLeft == valToTest && board.CenterLeft == valToTest && board.BottomLeft == valToTest) ||
                    (board.TopCenter == valToTest && board.Center == valToTest && board.BottomCenter == valToTest) ||
                    (board.TopRight == valToTest && board.CenterRight == valToTest && board.BottomRight == valToTest) ||
                    (board.TopLeft == valToTest && board.Center == valToTest && board.BottomRight == valToTest) ||
                    (board.BottomLeft == valToTest && board.Center == valToTest && board.TopRight == valToTest))
                {
                    winner = valToTest;
                    return true;
                }
            }
            return false;
        }

    }
}
