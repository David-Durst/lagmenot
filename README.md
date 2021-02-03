# LagMeNot
I'm just trying out some lag hiding techniques in a simple game.

## Actions made to do networking
1. separate sprite from logic for physics locations - turns out this wasn't helpful. Would be helpful if
doing a backend server with no renderer, but I want to render the server and client side. 
Actually, this was helpful serializing state between server and client though even for me where server is rendering
