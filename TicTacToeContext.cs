using System;
using System.Collections.Generic;
using System.Data.Entity;
using System.Linq;
using System.Security.Principal;
using System.Text;
using System.Threading.Tasks;

namespace DataLayer
{
    public class TicTacToeContext : DbContext
    {
        public virtual DbSet<TicTacToeBoard> Boards { get; set; }
        public TicTacToeBoard GetBoardForUser(IPrincipal user)
        {
            return (from b in Boards
                    where b.Username == user.Identity.Name
                    select b).FirstOrDefault();
        }
    }
}
