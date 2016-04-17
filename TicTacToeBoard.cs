using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations.Schema;
using System.Data.Entity;
using System.Linq;
using System.Text;
using System.Threading.Tasks;


namespace DataLayer
{
    


    public class TicTacToeBoard
    {
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }

        public string Username { get; set; }

        private char currentPlayer = 'X';
        public string CurrentPlayer
        {
            get { return currentPlayer.ToString(); }
            set
            {
                if (value == "X" || value == "O")
                    currentPlayer = value.ToCharArray()[0];
            }
        }

        // null = not checked
        // true = X
        // false = O

        public bool? TopLeft { get; set; }
        public bool? TopCenter { get; set; }
        public bool? TopRight { get; set; }
        public bool? CenterLeft { get; set; }
        public bool? Center { get; set; }
        public bool? CenterRight { get; set; }
        public bool? BottomLeft { get; set; }
        public bool? BottomCenter { get; set; }
        public bool? BottomRight { get; set; }

    }
}
