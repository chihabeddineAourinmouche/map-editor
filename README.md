# **2D Side-Scroller Level Editor**

This repository contains a simple and efficient 2D side-scroller level editor built with Python. It allows developers to easily design levels by placing sprites and defining hitboxes, exporting the level data into a structured `JSON` file.

## **Features**

* **Intuitive 2D Level Design:** Create side-scrolling levels visually.  
* **Sprite Placement:** Easily place any `.PNG` image as a sprite (works for tiles or any other image asset).  
* **Hitbox Definition:** Define custom hitboxes for sprites to manage collisions and interactions.  
* **JSON Output:** Exports level data (sprite positions, hitbox coordinates) into a clean, easy-to-parse `JSON` format.  
* **Simplicity & Efficiency:** Designed for straightforward use and performance.

## **Output**

The level editor generates a `JSON` file representing a single level. This file contains data structures detailing the coordinates of placed sprites and the defined hitboxes associated with them. This data can then be easily loaded and used by a game engine or framework.

## **Requirements**

* Python 3

The project uses several `Python` libraries, including `pygame` and `customtkinter`, among others. These dependencies will be handled by the provided build script.

## **Getting Started**

To run the level editor, execute the build-and-run.sh script from the root of the repository:  
`./build-and-run.sh`

This script will handle setting up the necessary environment and launching the application.

## **Packaging**

To package the project into a standalone executable using PyInstaller, run the pack.sh script:  
`./pack.sh`

This will create a distributable package of the level editor.