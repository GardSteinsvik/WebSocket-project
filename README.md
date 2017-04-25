# Websocket-project
Project in "Nettverksprogrammering". IDI, NTNU.

## Krav
* bruk av ferdige WebSocket biblioteker er ikke tillatt
* støtte kommunikasjon med 1 klient
    * kommunikasjon med flere klienter er ikke et krav
    * bruk av flere tråder er heller ikke et krav
* skal kunne kommunisere med en nettleser via JavaScript og støtte:
    * handshake
    * små tekstmeldinger begger veier (server til klient og klient til server)
        * større meldinger er ikke et krav
    * close
        * status og reason er ikke et krav
* README.md fil for løsningen med eksempel bruk av biblioteket