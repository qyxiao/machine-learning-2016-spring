using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.Mvc;
using DataLayer;
using TiTa.Models;
using BizLogic;

namespace TiTa.Controllers
{
    public class HomeController : Controller
    {
        public ActionResult Index()
        {
            if(!User.Identity.IsAuthenticated)
            {
                return View("NotAuthorized");
            }

            using (var tttc = new TicTacToeContext())
            {
                if(tttc.GetBoardForUser(User)==null)
                {
                    var newBoard = new TicTacToeBoard();
                    newBoard.Username = User.Identity.Name;
                    tttc.Boards.Add(newBoard);
                    tttc.SaveChanges();
                }
            }
                return RedirectToAction("ViewBoard");
        }


        public ActionResult ViewBoard()
        {
            using (var tttc = new TicTacToeContext())
            {
                var userBoard = tttc.GetBoardForUser(User);

                

                var tttvm = new TicTacToeViewModel()
                {
                    Board = userBoard,
                    IsOTheWinner = userBoard.IsOTheWinner(),
                    IsXTheWinner = userBoard.IsXTheWinner(),
                    IsBoardFull = userBoard.BoardIsFull(),
                    IsGameOver = userBoard.IsGameOver()
                };
                return View(tttvm);

            }
                
        }

        [HttpPost]
        public ActionResult ViewBoard(string button)
        {
            using (var tttc = new TicTacToeContext())
            {
                var userBoard = tttc.GetBoardForUser(User);

                // Prevent board clicks from doing anything if the game is over.
                if (!userBoard.IsGameOver())
                {
                    // Update the model based on what was selected
                    switch (button)
                    {
                        case "topleft": userBoard.TopLeft = (userBoard.CurrentPlayer == "X"); break;
                        case "topcenter": userBoard.TopCenter = (userBoard.CurrentPlayer == "X"); break;
                        case "topright": userBoard.TopRight = (userBoard.CurrentPlayer == "X"); break;
                        case "centerleft": userBoard.CenterLeft = (userBoard.CurrentPlayer == "X"); break;
                        case "center": userBoard.Center = (userBoard.CurrentPlayer == "X"); break;
                        case "centerright": userBoard.CenterRight = (userBoard.CurrentPlayer == "X"); break;
                        case "bottomleft": userBoard.BottomLeft = (userBoard.CurrentPlayer == "X"); break;
                        case "bottomcenter": userBoard.BottomCenter = (userBoard.CurrentPlayer == "X"); break;
                        case "bottomright": userBoard.BottomRight = (userBoard.CurrentPlayer == "X"); break;
                    }

                    userBoard.SwitchPlayers();
                    tttc.SaveChanges();
                }
                return RedirectToAction("ViewBoard");
            }

        }


        /// <summary>
        /// NewBoard action.  Creates a new board and removes
        /// any existing boards for the current user.
        /// </summary>
        public ActionResult NewBoard()
        {
            using (var tttc = new TicTacToeContext())
            {
                var res = (from b in tttc.Boards
                           where b.Username == User.Identity.Name
                           select b);

                tttc.Boards.RemoveRange(res);

                var newBoard = new TicTacToeBoard();
                newBoard.Username = User.Identity.Name;
                tttc.Boards.Add(newBoard);
                tttc.SaveChanges();
                return RedirectToAction("ViewBoard");
            }
        }
        public ActionResult About()
        {
            ViewBag.Message = "Your application description page.";

            return View();
        }

        public ActionResult NotAuthorized()
        {
            ViewBag.Message = "Your application description page.";

            return View();
        }

    }
}