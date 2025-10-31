import { useState } from 'react'
import './App.css'

import GoStreamLogoTitleUnder from "/src/assets/GoStreamLogoTitleUnder.png";
import FullBoard from "/src/assets/fullboard.png";
import FloorGoban from "/src/assets/FloorGoban.jpg";

const App = () => {
  return (
    <>
    <div className="p-3 bg-dark custom-container">
        <div className="container">
            <div className="d-flex flex-wrap align-items-center justify-content-lg-start">

                <div className="col">
                    <img src={GoStreamLogoTitleUnder} className ="GoStreamHome" alt="Home" id="logo"/>
                </div>
                <div className="col">
                    <div className="text-start custom-color custom-size">
                        GoStream is a streaming platform, in progress, developped by IMT Atlantique-Brest students, for the sake of filming, streaming, detecting and digitizing a Go Game for the Go club Tenuki in Brest, France.
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div className="p-3 custom-color custom-container">
        <div className="container">
            <div className="d-flex flex-wrap align-items-center justify-content-lg-start">

                <div className="col">
                    <div className="text-end custom-color custom-size">
                        The platform allows the user to precisely recognize a Go board during a live stream,
                         detect black and white stones, 
                         assign them to their right positions, 
                         and visually reproduce the game for training purposes. 
                         The user can navigate through the game using navigation buttons during the live stream or download the SGF file of the streamed game.
                    </div>
                </div>

                <div className="col">
                    <img src={FullBoard} className ="homeBoard" alt="Home" id="logo"/>
                </div>
            </div>
        </div>
    </div>
    <div className="p-3 custom-container">
        <div className="container">
            <div className="d-flex flex-wrap align-items-center justify-content-lg-start">

                <div className="col">
                    <img src={GoStreamLogoTitleUnder} className ="GoStreamHome" alt="Home" id="logo"/>
                </div>
                <div className="col">
                    <div className="text-start custom-color" style={{fontSize: "20px"}}>
                        <h2>How does it work?</h2>
                        <p>
                        The board, corners, stones and some intersections are detected via a custom trained Yolov8 model.
                        The missing intersections are then calculated by finding the missing lines and removing dupes to make sure each stone is precisely assigned to its position.
                        </p>
                        <p>
                        During a stream, we make sure to detect the change between frames to ensure the continuity of the game. The game is managed via Sente, an OpenSource library.
                        For more details about the detection and the game management algorithm, check our <a href="https://github.com/GoGame-Recognition-Project/GoGame-Detection" class="custom-color text-decoration-none "><i>Github repository.</i></a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div> 
    <div className="p-3 custom-container bg-dark">
        <div className="container">
            <div className="d-flex flex-wrap align-items-center justify-content-lg-start">

                <div className="col">
                    <div className="text-end custom-color" style={{fontSize: "20px"}}>
                        <h2>How to use it?</h2>
                        <p>
                        The platform makes it possible to stream in two modes: Game Mode and Free Mode.
                        </p>
                        <p>
                        Free Mode allows streaming a game without having to respect the rules,
                        and is able to correctly position any number of pieces put on the board at the same time.
                        It's an exact, transparent live visual reproduction of what's happening on the board.
                        </p>
                        <p>
                        In Game Mode, you need to follow the Go rules, and respect black and white's turns. 
                        Being less flexible than Free Mode, this mode still allows you to undo your last move,
                        to manually correct the position of a stone and to get the sgf file of the streamed game.
                        </p>
                    </div>
                </div>

                <div className="col">
                    <img src={FloorGoban} className ="homeBoard" alt="Home" id="logo"/>
                </div>
            </div>
        </div>
    </div>
  </>
  )
}

export default App
