using DataLayer;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TiTa.Models
{
   
    public class TicTacToeViewModel
    {
        public TicTacToeBoard Board { get; set; }

        public bool IsXTheWinner { get; set; }

        public bool IsOTheWinner { get; set; }

        public bool IsBoardFull { get; set; }

        public bool IsGameOver { get; set; }


    }
}
