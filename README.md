# Social Connection App

This is a full-stack web application built with Python Flask that aims to reduce social anxiety by promoting real-life interactions. Users can only connect with others by exchanging unique referral codes.

## Features

-   User registration and authentication.
-   Unique referral code for each user.
-   QR code generation for easy sharing.
-   Connection system based solely on referral codes (no user search).
-   Daily icebreaker tasks to encourage interaction.
-   Dashboard, Profile, and Connections pages.

## Tech Stack

-   **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-Login
-   **Database**: SQLite
-   **Frontend**: HTML, CSS
-   **QR Generation**: `qrcode` library

## Setup and Installation

Follow these steps to run the application locally.

### 1. Prerequisites

-   Python 3.6+
-   `pip` package installer

### 2. Clone the Repository

Clone this project to your local machine (or simply create the files as described).

```bash
git clone <repository-url>
cd social_app