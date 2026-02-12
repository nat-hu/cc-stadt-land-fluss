# StadtLandFluss

A real‑time, browser‑based multiplayer version of the classic *City–Country–River* game, built as a fully serverless web application on AWS.

> This project was developed as a team project of the **Cloud Computing** module at HdM Stuttgart.  
> Team members: Sophia Schwalb, Natalie Hussfeldt, Anh Thu Bui, Gamze Isik.

---

## Game Idea 

Inspired by party games like **Skribbl.io**, this project turns *City–Country–River* into an online multiplayer experience.

Core game features:

- Create custom **game rooms** (rounds, timer, categories, player count).
- Join existing rooms via a room code.
- **Waiting room** showing all connected players.
- **Letter generator** to pick a random starting letter.
- Timed rounds where each player fills in their answers per category.
- Display of all players’ inputs after each round.
- **Hall of Fame** / scoreboard at the end of the game.


## Tech Stack & Architecture

### Frontend

- **Angular** (TypeScript) as the main web application framework.
- Uses **WebSockets** for real‑time communication with the backend.
- Deployed as a static web app to **AWS S3** and served via a generated URL.

### Backend

- **Python** for server‑side game logic.
- **Serverless Framework** to define and deploy infrastructure via a single `serverless.yml`:
  - DynamoDB tables  
  - API routes  
  - Lambda functions  
  - IAM roles and permissions

### AWS Components
DynamoDB, AWS Lambda, API Gateway (WebSocket API), CloudWatch, S3





